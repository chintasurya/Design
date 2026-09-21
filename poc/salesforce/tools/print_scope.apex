/*
 * Which objects are actually in the Network Services pod scope, and why.
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run, then read the USER_DEBUG lines. Read-only.
 *
 * This exists because the scope has only ever reported COUNTS. "36 objects
 * owned out of 18 readable" cannot be checked by anyone, cannot be argued
 * with, and left "is Account in scope?" unanswerable for three sessions. The
 * scope is computed from live org state, so this is the only place the list
 * can come from.
 *
 * Every object is printed with the reason it qualified:
 *
 *   [profile]   the pod profile can create or edit it
 *   [recordtype] it carries an active record type with "network" in the name
 *   [permset]   only a permission set assigned to the pod's users grants it
 *   [dropped]   in scope, but the exporter skips it (history, share, feed,
 *               tag and change event objects are never graph nodes)
 *   [missing]   in scope per permissions, but getGlobalDescribe() does not
 *               have it, so nothing can be read from it
 */

String POD = 'Network Services';

AINetworkServicesScope scope = AINetworkServicesScope.resolve(POD);

System.debug('=== SCOPE FOR "' + POD + '" ===');
System.debug('profile matched: ' + scope.matchedProfile
    + ' (found=' + scope.profileFound + ')');
System.debug('NOTE: ' + scope.note);
System.debug('counts: ' + scope.owned.size() + ' owned · '
    + scope.writable.size() + ' writable on the profile · '
    + scope.recordTypeObjects.size() + ' with a Network record type · '
    + scope.readable.size() + ' readable on the profile · '
    + scope.permissionSetWritable.size() + ' writable via permission sets');

Map<String, Schema.SObjectType> described = Schema.getGlobalDescribe();

// Lowercase indexes, because ObjectPermissions.SobjectType and
// getGlobalDescribe().keySet() do not reliably agree on casing.
Set<String> writableLower = new Set<String>();
for (String o : scope.writable) { writableLower.add(o.toLowerCase()); }
Set<String> recordTypeLower = new Set<String>();
for (String o : scope.recordTypeObjects) { recordTypeLower.add(o.toLowerCase()); }
Set<String> permsetLower = new Set<String>();
for (String o : scope.permissionSetWritable) { permsetLower.add(o.toLowerCase()); }

List<String> ordered = new List<String>(scope.owned);
ordered.sort();

System.debug('=== ' + ordered.size() + ' OBJECTS IN SCOPE ===');
Integer graphable = 0;
for (String apiName : ordered) {
    String key = apiName.toLowerCase();
    List<String> why = new List<String>();
    if (writableLower.contains(key))   { why.add('profile'); }
    if (recordTypeLower.contains(key)) { why.add('recordtype'); }
    if (permsetLower.contains(key) && !writableLower.contains(key)) {
        why.add('permset');
    }

    Boolean skipped = apiName.endsWith('__History') || apiName.endsWith('__Share')
                   || apiName.endsWith('__Feed') || apiName.endsWith('__Tag')
                   || apiName.endsWith('ChangeEvent');
    if (skipped)                       { why.add('dropped'); }
    if (!described.containsKey(apiName)) { why.add('missing'); }
    if (!skipped && described.containsKey(apiName)) { graphable++; }

    String fieldNote = '';
    if (described.containsKey(apiName)) {
        fieldNote = ' · ' + described.get(apiName).getDescribe()
                                     .fields.getMap().size() + ' fields';
    }
    System.debug('  [' + String.join(why, '+') + '] ' + apiName + fieldNote);
}
System.debug('=> ' + graphable + ' of ' + ordered.size()
    + ' will become SObject nodes; the rest are dropped or unreadable');

// The three that kept coming up. Answered explicitly so nobody has to scan.
for (String q : new List<String>{
        'Account', 'HealthcareProvider', 'HealthcareFacility', 'Contact' }) {
    System.debug('covers(' + q + '): ' + scope.covers(q)
        + ' · exists in org: ' + described.containsKey(q));
}

// What the profile can see but does NOT own. This is the set the pod reads
// and does not maintain, and it is where an object that ought to be in scope
// would be hiding.
List<String> readOnly = new List<String>();
for (String r : scope.readable) {
    if (!scope.covers(r)) {
        readOnly.add(r);
    }
}
readOnly.sort();
System.debug('=== ' + readOnly.size() + ' READABLE BUT NOT OWNED ===');
Integer shown = 0;
for (String apiName : readOnly) {
    if (shown++ >= 60) {
        System.debug('  ... and ' + (readOnly.size() - 60) + ' more');
        break;
    }
    System.debug('  [read-only] ' + apiName);
}

// Objects a permission set grants that the profile-based scope missed
// entirely. If this list is long, the profile is the wrong scope signal.
List<String> permsetOnly = new List<String>();
for (String o : scope.permissionSetWritable) {
    if (!scope.covers(o)) {
        permsetOnly.add(o);
    }
}
permsetOnly.sort();
System.debug('=== ' + permsetOnly.size()
    + ' WRITABLE VIA PERMISSION SET BUT NOT IN SCOPE ===');
shown = 0;
for (String apiName : permsetOnly) {
    if (shown++ >= 60) {
        System.debug('  ... and ' + (permsetOnly.size() - 60) + ' more');
        break;
    }
    System.debug('  [permset-only] ' + apiName);
}
if (!permsetOnly.isEmpty()) {
    System.debug('SIGNAL: these are maintained by the pod\'s users but are not '
        + 'in the graph. If the pod owns any of them, the profile is the wrong '
        + 'scope signal for this org.');
}
