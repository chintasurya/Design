#!/usr/bin/env python3
"""
Catch the Apex naming faults that only surface at deploy time.

The Metadata API reports these as "Invalid character in identifier" or
"Identifier name is reserved", and every dependent class then fails with
"needs recompilation", so one bad name produces a wall of cascade errors
that hides the real cause. Cheaper to catch here.

Three narrow checks, chosen so there are no false positives to train
yourself to ignore:

  1. Identifiers ending in "_"          Apex forbids it outright.
  2. Reserved words as parameter names  "system", "type", "date" and friends.
  3. Reserved words as local variables  "any", "list", "limit" and friends.
  4. Custom exception class names       Must end "Exception", must not reuse
                                        the name of a System exception.
  5. Unqualified inner enum values      Apex rejects Phase.EDGES inside the
                                        class declaring "enum Phase" with
                                        "Static field cannot be referenced
                                        from a non static context".

Checks 2 and 3 exist because the same class of bug reached a real org three
times: a parameter called "system", a field called "override_", and a local
called "any". Each one produced a wall of "dependent class needs
recompilation" errors that buried the single line actually at fault.

    python3 tools/lint_apex.py mdapi/classes
"""

import os
import re
import sys

RESERVED = {
    'abstract', 'and', 'any', 'array', 'as', 'asc', 'blob', 'boolean', 'break',
    'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'database',
    'date', 'datetime', 'decimal', 'default', 'delete', 'desc', 'do', 'double',
    'else', 'enum', 'exception', 'extends', 'false', 'final', 'finally',
    'float', 'for', 'from', 'global', 'goto', 'group', 'having', 'if',
    'implements', 'import', 'in', 'insert', 'instanceof', 'int', 'integer',
    'interface', 'into', 'join', 'like', 'limit', 'list', 'long', 'map',
    'merge', 'new', 'not', 'null', 'object', 'on', 'or', 'override', 'package',
    'private', 'protected', 'public', 'return', 'rollback', 'select', 'set',
    'short', 'static', 'string', 'super', 'switch', 'system', 'testmethod',
    'this', 'throw', 'time', 'transaction', 'trigger', 'true', 'try', 'type',
    'undelete', 'update', 'upsert', 'virtual', 'void', 'webservice', 'when',
    'where', 'while', 'with', 'without',
}

SYSTEM_EXCEPTIONS = {
    'CalloutException', 'DmlException', 'QueryException', 'LimitException',
    'NullPointerException', 'SObjectException', 'TypeException',
    'JSONException', 'MathException', 'StringException', 'ListException',
    'NoAccessException', 'NoDataFoundException', 'SearchException',
    'SecurityException', 'SerializationException', 'AsyncException',
}

# Method or constructor signature, captured so parameters can be inspected.
SIGNATURE = re.compile(
    r'\b(?:public|private|protected|global)\b[^;{()]*?\b(\w+)\s*\(([^)]*)\)\s*\{')

EXC_CLASS = re.compile(r'\bclass\s+(\w+)\s+extends\s+Exception\b')

# Local and field declarations, restricted to type forms that cannot be
# confused with anything else once SOQL and strings are stripped. A broader
# pattern matches SOQL field lists and drowns the real findings in noise.
LOCAL_DECL = re.compile(
    r'\b(?:List|Map|Set)\s*<[^<>]*>\s+([A-Za-z]\w*)\s*[;=:)]'
    r'|\b(?:String|Integer|Boolean|Decimal|Double|Long|Date|Datetime|Time|'
    r'Blob|Object|Id)\s+([A-Za-z]\w*)\s*[;=:)]'
    r'|\b(\w+__c)\s+([A-Za-z]\w*)\s*[;=:)]')

# Anything a custom object or field legitimately ends with.
SF_SUFFIX = re.compile(r'__(c|r|e|x|b|mdt|Share|History|Feed|Tag)$', re.I)


def strip_noise(src):
    """Remove comments, string literals and inline SOQL, which are not code."""
    src = re.sub(r'/\*.*?\*/', ' ', src, flags=re.S)
    src = re.sub(r'//[^\n]*', ' ', src)
    src = re.sub(r"'(?:[^'\\]|\\.)*'", "''", src)
    src = re.sub(r'\[[^\[\]]*\]', '[]', src)          # SOQL and list indexes
    return src


def check(path):
    raw = open(path, encoding='utf-8').read()
    src = strip_noise(raw)
    out = []

    for n, line in enumerate(src.split('\n'), 1):
        for ident in re.findall(r'\b([A-Za-z]\w*_)(?![\w])', line):
            if not SF_SUFFIX.search(ident):
                out.append((n, ident, 'identifier may not end with "_"'))

    for m in LOCAL_DECL.finditer(src):
        name = next((g for g in m.groups()[::-1] if g), None)
        if name and name.lower() in RESERVED:
            n = src[:m.start()].count('\n') + 1
            out.append((n, name, 'variable name is reserved in Apex'))

    for m in SIGNATURE.finditer(src):
        n = src[:m.start()].count('\n') + 1
        for param in m.group(2).split(','):
            parts = param.strip().split()
            if len(parts) < 2:
                continue
            name = parts[-1]
            if name.lower() in RESERVED:
                out.append((n, name, 'parameter name is reserved in Apex'))

    for m in re.finditer(r'\benum\s+(\w+)\s*\{', src):
        enum_name = m.group(1)
        cls = os.path.splitext(os.path.basename(path))[0]
        for use in re.finditer(r'(?<![\w.])%s\s*\.\s*[A-Z_]{2,}' % enum_name, src):
            before = src[max(0, use.start() - len(cls) - 1):use.start()]
            if before.endswith(cls + '.'):
                continue
            n = src[:use.start()].count('\n') + 1
            out.append((n, enum_name,
                        'inner enum used unqualified; write %s.%s.X or use '
                        'String constants' % (cls, enum_name)))

    for m in EXC_CLASS.finditer(src):
        n = src[:m.start()].count('\n') + 1
        name = m.group(1)
        if not name.endswith('Exception'):
            out.append((n, name, 'exception class name must end "Exception"'))
        if name in SYSTEM_EXCEPTIONS:
            out.append((n, name, 'shadows the System exception of the same name'))

    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'mdapi/classes'
    files = sorted(f for f in os.listdir(root) if f.endswith('.cls'))
    total = 0
    for f in files:
        for line, name, why in check(os.path.join(root, f)):
            print('%s:%d  %-26s %s' % (f, line, name, why))
            total += 1
    print('%d classes checked, %d problem%s'
          % (len(files), total, '' if total == 1 else 's'))
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
