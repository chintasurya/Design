#!/usr/bin/env python3
"""
Discover the Network Service pod's metadata footprint in a Salesforce sandbox.

Scope is derived from a profile's object permissions rather than a hand-written
list, so the inventory is reproducible, auditable, and re-runnable as the pod
changes. Nothing here writes to the org. Every query is read-only.

Usage:
    sf org login web --alias ns-sandbox
    python3 discover_scope.py --org ns-sandbox --profile "Network Service"

Output:
    out/*.json          one file per discovered component type
    out/summary.json    counts plus an estimate of resulting graph size
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

OUT_DIR = "out"


def sf_query(org, soql, tooling=False, label=""):
    """Run one SOQL query through the sf CLI and return its records."""
    cmd = ["sf", "data", "query", "--target-org", org, "--query", soql, "--json"]
    if tooling:
        cmd.append("--use-tooling-api")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = proc.stdout or proc.stderr
        try:
            detail = json.loads(proc.stdout).get("message", detail)
        except (ValueError, AttributeError):
            pass
        print("  ! %-28s failed: %s" % (label, str(detail).strip()[:160]))
        return []

    records = json.loads(proc.stdout).get("result", {}).get("records", [])
    for r in records:
        r.pop("attributes", None)
    print("  . %-28s %d" % (label, len(records)))
    return records


def write(name, records):
    path = os.path.join(OUT_DIR, name + ".json")
    with open(path, "w") as f:
        json.dump(records, f, indent=2, sort_keys=True)
    return path


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def quoted_list(values):
    return ", ".join("'%s'" % v.replace("'", r"\'") for v in values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True, help="sf CLI org alias or username")
    ap.add_argument("--profile", default="Network Service",
                    help="profile whose object access defines the pod scope")
    ap.add_argument("--record-type-pattern", default="network",
                    help="case-insensitive regex matched against record type names")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    profile = args.profile.replace("'", r"\'")
    inventory = {}

    # ---------------------------------------------------------------- scope
    print("\n[1] Resolving profile scope")

    perm_sets = sf_query(
        args.org,
        "SELECT Id, Name, Profile.Name FROM PermissionSet "
        "WHERE IsOwnedByProfile = true AND Profile.Name = '%s'" % profile,
        label="profile permission set",
    )
    if not perm_sets:
        sys.exit("\nNo profile named %r found. Check the exact spelling in Setup > Profiles."
                 % args.profile)
    ps_id = perm_sets[0]["Id"]

    obj_perms = sf_query(
        args.org,
        "SELECT SobjectType, PermissionsRead, PermissionsCreate, PermissionsEdit, "
        "PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords "
        "FROM ObjectPermissions WHERE ParentId = '%s' AND PermissionsRead = true "
        "ORDER BY SobjectType" % ps_id,
        label="readable objects",
    )
    objects = sorted({o["SobjectType"] for o in obj_perms})
    writable = sorted({o["SobjectType"] for o in obj_perms
                       if o.get("PermissionsCreate") or o.get("PermissionsEdit")})
    inventory["objects"] = obj_perms
    write("objects", obj_perms)

    # --------------------------------------------------------------- fields
    print("\n[2] Field-level access (chunked, FieldPermissions rejects broad filters)")
    fields = []
    for batch in chunked(objects, 20):
        fields += sf_query(
            args.org,
            "SELECT SobjectType, Field, PermissionsRead, PermissionsEdit "
            "FROM FieldPermissions WHERE ParentId = '%s' AND SobjectType IN (%s)"
            % (ps_id, quoted_list(batch)),
            label="fields %s.." % batch[0][:18],
        )
    inventory["fields"] = fields
    write("fields", fields)

    # ---------------------------------------------------------- record types
    print("\n[3] Record types")
    rt_all = sf_query(
        args.org,
        "SELECT Id, Name, DeveloperName, SobjectType, IsActive FROM RecordType "
        "WHERE IsActive = true ORDER BY SobjectType",
        label="active record types",
    )
    pattern = re.compile(args.record_type_pattern, re.I)
    rts = [r for r in rt_all
           if r["SobjectType"] in set(objects)
           and (pattern.search(r["DeveloperName"] or "") or pattern.search(r["Name"] or ""))]
    print("  . %-28s %d in-scope" % ("matching pod pattern", len(rts)))
    inventory["record_types"] = rts
    write("record_types", rts)

    # ----------------------------------------------------------- automation
    print("\n[4] Automation attached to those objects")

    triggers = [t for t in sf_query(
        args.org,
        "SELECT Id, Name, TableEnumOrId, Status, ApiVersion, LengthWithoutComments "
        "FROM ApexTrigger WHERE NamespacePrefix = null",
        tooling=True, label="apex triggers (all)",
    ) if t.get("TableEnumOrId") in set(objects)]
    print("  . %-28s %d on in-scope objects" % ("apex triggers", len(triggers)))
    inventory["triggers"] = triggers
    write("triggers", triggers)

    flows_all = sf_query(
        args.org,
        "SELECT ApiName, Label, ProcessType, TriggerType, TriggerObjectOrEventLabel, "
        "IsActive, VersionNumber, Description FROM FlowDefinitionView WHERE IsActive = true",
        label="active flows (all)",
    )
    labels = set(objects)
    flows = [f for f in flows_all
             if (f.get("TriggerObjectOrEventLabel") or "") in labels
             or (f.get("ApiName") or "").lower().find("network") >= 0]
    print("  . %-28s %d likely in scope" % ("flows", len(flows)))
    inventory["flows"] = flows
    write("flows", flows_all)

    vrules = [v for v in sf_query(
        args.org,
        "SELECT Id, ValidationName, Active, EntityDefinition.QualifiedApiName "
        "FROM ValidationRule",
        tooling=True, label="validation rules (all)",
    ) if (v.get("EntityDefinition") or {}).get("QualifiedApiName") in set(objects)]
    print("  . %-28s %d on in-scope objects" % ("validation rules", len(vrules)))
    inventory["validation_rules"] = vrules
    write("validation_rules", vrules)

    classes = sf_query(
        args.org,
        "SELECT Id, Name, ApiVersion, Status, LengthWithoutComments FROM ApexClass "
        "WHERE NamespacePrefix = null ORDER BY Name",
        tooling=True, label="apex classes (all)",
    )
    inventory["apex_classes"] = classes
    write("apex_classes", classes)

    # --------------------------------------------------------- dependencies
    print("\n[5] Dependency edges (MetadataComponentDependency)")
    print("    Tooling-only, caps around 2000 rows per query, so this runs per object.")
    deps = []
    for obj in objects:
        rows = sf_query(
            args.org,
            "SELECT MetadataComponentId, MetadataComponentName, MetadataComponentType, "
            "RefMetadataComponentId, RefMetadataComponentName, RefMetadataComponentType "
            "FROM MetadataComponentDependency "
            "WHERE RefMetadataComponentName = '%s'" % obj.replace("'", r"\'"),
            tooling=True, label="deps -> %s" % obj[:20],
        )
        deps += rows
    inventory["dependencies"] = deps
    write("dependencies", deps)

    referenced = {d["MetadataComponentName"] for d in deps
                  if d.get("MetadataComponentType") == "ApexClass"}
    scoped_classes = [c for c in classes if c["Name"] in referenced]

    # -------------------------------------------------------------- summary
    by_type = defaultdict(int)
    for d in deps:
        by_type[d.get("MetadataComponentType") or "Unknown"] += 1

    nodes = (len(objects) + len(fields) + len(rts) + len(triggers)
             + len(flows) + len(vrules) + len(scoped_classes))
    edges = len(deps) + len(fields) + len(rts)

    summary = {
        "profile": args.profile,
        "objects_readable": len(objects),
        "objects_writable": len(writable),
        "fields": len(fields),
        "record_types_in_scope": len(rts),
        "triggers": len(triggers),
        "flows_in_scope": len(flows),
        "validation_rules": len(vrules),
        "apex_classes_total": len(classes),
        "apex_classes_referencing_scope": len(scoped_classes),
        "dependency_edges": len(deps),
        "dependency_edges_by_type": dict(by_type),
        "estimated_graph_nodes_salesforce_only": nodes,
        "estimated_graph_edges_salesforce_only": edges,
        "writable_objects": writable,
    }
    write("summary", summary)

    print("\n" + "=" * 64)
    print("SCOPE SUMMARY  (Salesforce only, before Jira and Confluence)")
    print("=" * 64)
    for k in ("objects_readable", "objects_writable", "fields", "record_types_in_scope",
              "triggers", "flows_in_scope", "validation_rules",
              "apex_classes_referencing_scope", "dependency_edges",
              "estimated_graph_nodes_salesforce_only",
              "estimated_graph_edges_salesforce_only"):
        print("  %-42s %s" % (k.replace("_", " "), summary[k]))
    print("\nWrote %s/ ... share summary.json and I will size the graph and the build.\n" % OUT_DIR)


if __name__ == "__main__":
    main()
