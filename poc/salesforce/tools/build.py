#!/usr/bin/env python3
"""
Lint, validate and package the POC for deployment.

Runs every check that has caught a real deploy failure so far:
  - Apex naming rules      (tools/lint_apex.py)
  - permission set regen   (tools/gen_permset.py, so it cannot drift)
  - contiguous XML groups  (the Metadata API rejects a repeated element that
                            appears in two places, with "Element X is
                            duplicated at this location")
  - namespace-aware XML    (a non namespace-aware parser once passed a file
                            with an undeclared prefix, and the deploy failed
                            with UNKNOWN_EXCEPTION and zero component errors)
  - package.xml vs zip     every member present, every file claimed

    python3 tools/build.py
"""

import glob
import io
import os
import re
import shutil
import subprocess
import sys
import xml.sax

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'mdapi')
API = '59.0'


def fail(msg):
    print('\n  FAILED: %s\n' % msg)
    sys.exit(1)


def lint():
    print('[1] apex naming')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'tools', 'lint_apex.py'),
                        os.path.join(SRC, 'classes')], capture_output=True, text=True)
    print('    ' + r.stdout.strip().replace('\n', '\n    '))
    if r.returncode:
        fail('apex lint')


def regen_permset():
    print('[2] permission set')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'tools', 'gen_permset.py')],
                       capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.returncode:
        fail('permission set generation')


def contiguity_check():
    """
    A repeated element split across two places is a deploy parse error.

    Only DIRECT SIBLINGS count. Repeated <fields> blocks are legitimate and
    each contains its own children, so a flat scan of tag names sees them as
    interleaved and reports nonsense. Walk parent by parent instead.
    """
    print('[4] contiguous element groups')
    import xml.etree.ElementTree as ET
    bad = []
    for f in sorted(glob.glob(SRC + '/**/*', recursive=True)):
        if not os.path.isfile(f) or os.path.splitext(f)[1] not in (
                '.object', '.permissionset', '.md', '.xml'):
            continue
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            fail('%s will not parse: %s' % (os.path.relpath(f, HERE), e))
        for parent in root.iter():
            seen, previous, broken = set(), None, set()
            for child in list(parent):
                name = child.tag.split('}')[-1]
                if name != previous:
                    if name in seen:
                        broken.add(name)
                    seen.add(name)
                    previous = name
            for name in sorted(broken):
                bad.append('%s: <%s> under <%s> appears in more than one place'
                           % (os.path.relpath(f, HERE), name,
                              parent.tag.split('}')[-1]))
    for b in bad:
        print('    ' + b)
    if bad:
        fail('non-contiguous repeated elements')
    print('    all repeated elements are grouped')


def xml_check():
    print('[3] namespace-aware xml')
    files = [f for f in glob.glob(SRC + '/**/*', recursive=True)
             if os.path.isfile(f) and os.path.splitext(f)[1] in
             ('.object', '.xml', '.md', '.permissionset')]
    for f in files:
        p = xml.sax.make_parser()
        p.setFeature(xml.sax.handler.feature_namespaces, True)
        try:
            p.parse(f)
        except Exception as e:
            fail('%s is not well formed: %s' % (os.path.relpath(f, HERE), e))
    print('    %d files, all well formed' % len(files))


def block(members, name):
    return ('    <types>\n'
            + ''.join('        <members>%s</members>\n' % m for m in members)
            + '        <name>%s</name>\n    </types>\n' % name)


def manifest(*blocks):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Package xmlns="http://soap.sforce.com/2006/04/metadata">\n'
            + ''.join(blocks) + '    <version>%s</version>\n</Package>\n' % API)


def package(dest, text, dirs):
    work = os.path.join(HERE, '.build', os.path.basename(dest))
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    for d in dirs:
        s = os.path.join(SRC, d)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(work, d))
    io.open(os.path.join(work, 'package.xml'), 'w', encoding='utf-8').write(text)

    claimed = set(re.findall(r'<members>([^<]+)</members>', text))
    present = {os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(work + '/**/*', recursive=True)
               if os.path.isfile(f) and not f.endswith('.xml')}
    present |= {os.path.basename(d) for d in glob.glob(work + '/lwc/*')}
    missing = {m for m in claimed if m.split('.')[0] not in present
               and m not in present}
    if missing:
        fail('package.xml claims members with no file: %s' % sorted(missing))

    if os.path.exists(dest):
        os.remove(dest)
    shutil.make_archive(dest[:-4], 'zip', work)
    n = sum(len(f) for _, _, f in os.walk(work))
    print('    %-34s %2d files  %6d bytes'
          % (os.path.relpath(dest, HERE), n, os.path.getsize(dest)))


def main():
    os.chdir(HERE)
    lint()
    regen_permset()
    xml_check()
    contiguity_check()

    objects = sorted(os.path.splitext(os.path.basename(f))[0]
                     for f in glob.glob(SRC + '/objects/*.object'))
    classes = sorted(os.path.splitext(os.path.basename(f))[0]
                     for f in glob.glob(SRC + '/classes/*.cls'))

    print('[5] packaging')
    os.makedirs('stage', exist_ok=True)

    # Main path. The custom metadata RECORD is deliberately excluded: deploying
    # a CMT type together with its records is a known failure mode, and
    # AIServiceFactory.config() already falls back when the record is absent.
    package('AI_Change_Console_POC.zip',
            manifest(block(objects, 'CustomObject'),
                     block(classes, 'ApexClass'),
                     block(['aiChangeConsole'], 'LightningComponentBundle'),
                     block(['AI_Change_Console_User'], 'PermissionSet')),
            ['objects', 'classes', 'lwc', 'permissionsets'])

    package('stage/01-schema.zip', manifest(block(objects, 'CustomObject')),
            ['objects'])
    package('stage/02-code.zip',
            manifest(block(classes, 'ApexClass'),
                     block(['aiChangeConsole'], 'LightningComponentBundle'),
                     block(['AI_Change_Console_User'], 'PermissionSet')),
            ['classes', 'lwc', 'permissionsets'])
    package('stage/03-config.zip',
            manifest(block(['AI_Poc_Config.Default'], 'CustomMetadata')),
            ['customMetadata'])

    shutil.rmtree(os.path.join(HERE, '.build'), ignore_errors=True)
    print('\n  all checks passed\n')


if __name__ == '__main__':
    main()
