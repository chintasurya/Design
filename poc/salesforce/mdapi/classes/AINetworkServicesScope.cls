/**
 * The pod's footprint, taken from a profile's object access rather than a
 * hand-maintained list.
 *
 * "Why is this object in scope" then has one answer: the Network Service
 * profile can read it. That is auditable, and it stays correct as the pod
 * changes without anyone editing code.
 */
public with sharing class AINetworkServicesScope {

    public Set<String> readable = new Set<String>();
    public Set<String> writable = new Set<String>();
    public Set<String> recordTypeObjects = new Set<String>();
    public Set<String> owned = new Set<String>();
    public Boolean profileFound = false;
    public String matchedProfile;
    public String note;

    /**
     * Objects the pod's own users can maintain through an assigned permission
     * set rather than through the profile.
     *
     * This exists because the profile reported 18 readable objects in an org
     * that plainly uses more than 18, which is the signature of access granted
     * by permission set. Measured on every resolve and always reported, so the
     * question "is the profile even the right scope signal here" is answered
     * by the build output instead of by argument.
     */
    public Set<String> permissionSetWritable = new Set<String>();
    public Boolean scopeCameFromPermissionSets = false;

    /**
     * The objects declared on AINetworkServicesPod that this org actually has,
     * and the declared names that resolved to nothing.
     *
     * The declared list is the authority. The profile is a second opinion,
     * because several pod objects are written only by automation and the
     * profile has no create permission on them: using create access as the
     * ownership test is what hid HealthcareFacilityNetwork, the object most
     * questions are about.
     */
    public Set<String> declaredObjects = new Set<String>();
    public List<String> unresolvedDeclarations = new List<String>();

    /** Why each object is in scope, for the note and the scope printout. */
    public Map<String, String> reasonOf = new Map<String, String>();

    private static Map<String, AINetworkServicesScope> cache =
        new Map<String, AINetworkServicesScope>();

    @TestVisible
    private static void clearCache() {
        cache.clear();
    }

    public static AINetworkServicesScope resolve(String profileName) {
        String key = String.isBlank(profileName) ? 'Network Service' : profileName;
        if (cache.containsKey(key)) {
            return cache.get(key);
        }
        AINetworkServicesScope s = new AINetworkServicesScope();

        List<PermissionSet> owned = findProfile(key, s);

        if (owned.isEmpty()) {
            s.note = 'Profile "' + key + '" not found, so the search is not scoped '
                   + 'to the pod. Set the profile name on AI_Poc_Config__mdt.';
            cache.put(key, s);
            return s;
        }
        s.profileFound = true;

        List<ObjectPermissions> perms = [
            SELECT SobjectType, PermissionsCreate, PermissionsEdit
            FROM ObjectPermissions
            WHERE ParentId = :owned[0].Id AND PermissionsRead = true];
        for (ObjectPermissions op : perms) {
            s.readable.add(op.SobjectType);
            if (op.PermissionsCreate || op.PermissionsEdit) {
                s.writable.add(op.SobjectType);
            }
        }
        s.measurePermissionSets(owned[0].ProfileId);
        s.resolveDeclaredPod();
        s.resolveOwned(key);
        cache.put(key, s);
        return s;
    }

    /**
     * Match the declared pod objects against the org.
     *
     * Normalized on both sides, so a declared "Credentialing Application"
     * finds Credentialing_Application__c and a declared
     * "HealthcareFacilityNetwork" finds either the standard object or a custom
     * one of that name, whichever this org has. Keys only from
     * getGlobalDescribe(): describing ~1,400 objects to read their labels
     * would spend CPU the export needs.
     */
    private void resolveDeclaredPod() {
        Map<String, String> byName = new Map<String, String>();
        for (String apiName : Schema.getGlobalDescribe().keySet()) {
            String flat = AINetworkServicesPod.normalize(apiName);
            if (!byName.containsKey(flat)) {
                byName.put(flat, apiName);
            }
            if (apiName.endsWith('__c')) {
                String bare = AINetworkServicesPod.normalize(
                    apiName.removeEnd('__c'));
                if (!byName.containsKey(bare)) {
                    byName.put(bare, apiName);
                }
            }
        }
        Map<String, String> resolved =
            AINetworkServicesPod.resolveObjects(byName);
        declaredObjects.addAll(resolved.values());
        for (String declared : AINetworkServicesPod.OBJECTS) {
            if (!resolved.containsKey(declared)) {
                unresolvedDeclarations.add(declared);
            }
        }
    }

    /**
     * What the pod's users can maintain via permission sets, not the profile.
     *
     * Two plain queries, bounded, and wrapped because a shortfall in Setup
     * visibility must degrade the diagnostic rather than fail the export.
     * Permission sets owned by a profile are excluded: those are the profile,
     * already counted.
     */
    private void measurePermissionSets(Id profileId) {
        if (profileId == null) {
            return;
        }
        try {
            List<Id> assignees = new List<Id>();
            for (User u : [SELECT Id FROM User
                           WHERE ProfileId = :profileId AND IsActive = true
                           LIMIT 500]) {
                assignees.add(u.Id);
            }
            if (assignees.isEmpty()) {
                return;
            }
            Set<Id> psIds = new Set<Id>();
            for (PermissionSetAssignment psa : [
                    SELECT PermissionSetId FROM PermissionSetAssignment
                    WHERE AssigneeId IN :assignees
                    AND PermissionSet.IsOwnedByProfile = false
                    LIMIT 2000]) {
                psIds.add(psa.PermissionSetId);
            }
            if (psIds.isEmpty()) {
                return;
            }
            for (AggregateResult ar : [
                    SELECT SobjectType st FROM ObjectPermissions
                    WHERE ParentId IN :psIds
                    AND (PermissionsCreate = true OR PermissionsEdit = true)
                    GROUP BY SobjectType LIMIT 2000]) {
                permissionSetWritable.add((String) ar.get('st'));
            }
        } catch (Exception e) {
            // A diagnostic that cannot be read is not a reason to stop.
            permissionSetWritable.clear();
        }
    }

    /**
     * Find the profile, tolerating a near miss.
     *
     * The configured name was "Network Service" and the real profile is
     * "Network Services". An exact-match-only lookup silently widened the
     * scope to the whole org over a single trailing character, so the lookup
     * now falls back through case-insensitive and prefix matching, and always
     * reports which profile it actually used.
     */
    private static List<PermissionSet> findProfile(String wanted,
                                                   AINetworkServicesScope s) {
        List<PermissionSet> exact = [
            SELECT Id, ProfileId, Profile.Name FROM PermissionSet
            WHERE IsOwnedByProfile = true AND Profile.Name = :wanted LIMIT 1];
        if (!exact.isEmpty()) {
            s.matchedProfile = exact[0].Profile.Name;
            return exact;
        }

        String target = normalize(wanted);
        List<PermissionSet> all = [
            SELECT Id, ProfileId, Profile.Name FROM PermissionSet
            WHERE IsOwnedByProfile = true LIMIT 500];

        for (PermissionSet ps : all) {           // case and punctuation only
            if (normalize(ps.Profile.Name) == target) {
                s.matchedProfile = ps.Profile.Name;
                return new List<PermissionSet>{ ps };
            }
        }
        for (PermissionSet ps : all) {           // singular versus plural
            String candidate = normalize(ps.Profile.Name);
            if (target.length() >= 6
                    && (candidate.startsWith(target) || target.startsWith(candidate))) {
                s.matchedProfile = ps.Profile.Name;
                return new List<PermissionSet>{ ps };
            }
        }
        return new List<PermissionSet>();
    }

    private static String normalize(String value) {
        return value == null ? '' : value.toLowerCase().replaceAll('[^a-z0-9]', '');
    }

    /**
     * What the pod actually owns, which is narrower than what it can see.
     *
     * Read access is a poor proxy for ownership: every profile reads hundreds
     * of standard objects, which is how a first build walked ~1,400 objects
     * and produced 36,330 nodes for a pod that should yield a few thousand.
     *
     * Two better signals, unioned:
     *   create or edit access   the pod maintains these
     *   a pod record type       the pod's records live on these
     */
    private void resolveOwned(String profileName) {
        for (RecordType rt : [
                SELECT SobjectType, DeveloperName FROM RecordType
                WHERE IsActive = true LIMIT 2000]) {
            // "Network Services" and "Network Services TX CIN", not the bare
            // word "network", which would also catch an unrelated Network
            // Partner or Network Ops record type.
            if (AINetworkServicesPod.podRecordType(rt.DeveloperName)) {
                recordTypeObjects.add(rt.SobjectType);
            }
        }
        // Declared first, because it is the authority. An object written only
        // by automation has no create permission behind it and would never
        // arrive through the profile.
        owned.addAll(declaredObjects);
        owned.addAll(writable);
        owned.addAll(recordTypeObjects);
        recordReasons();

        // An org that grants access through permission sets leaves the profile
        // almost empty, and the old fallback to "everything readable" then
        // produced a scope that was both wrong and enormous. What the pod's
        // users can actually maintain is the better answer.
        if (owned.isEmpty() && !permissionSetWritable.isEmpty()) {
            owned.addAll(permissionSetWritable);
            scopeCameFromPermissionSets = true;
            indexLowercase();
            note = 'Profile "' + profileName + '" grants no create or edit access '
                 + 'and no object carries a Network record type, so the scope is '
                 + 'taken from the ' + permissionSetWritable.size() + ' objects the '
                 + 'profile\'s users can maintain through assigned permission sets';
            return;
        }

        if (owned.isEmpty()) {
            owned.addAll(readable);
            indexLowercase();
            note = 'Profile "' + profileName + '" grants no create or edit access, '
                 + 'no object carries a Network record type and no permission set '
                 + 'assigned to its users grants any either, so the scope falls '
                 + 'back to all ' + readable.size() + ' readable objects';
            return;
        }
        indexLowercase();
        String shown = String.isBlank(matchedProfile) ? profileName : matchedProfile;
        String matchNote = (matchedProfile != null && matchedProfile != profileName)
            ? ' (configured as "' + profileName + '", matched "' + matchedProfile + '")'
            : '';
        note = owned.size() + ' objects in the Network Services pod: '
             + declaredObjects.size() + ' declared, '
             + writable.size() + ' writable on "' + shown + '"' + matchNote + ', '
             + recordTypeObjects.size() + ' carrying a Network Services record '
             + 'type. The count is the union, so it can exceed any of them. '
             + 'For reference the profile reads ' + readable.size()
             + ' objects and permission sets assigned to its users grant write '
             + 'on ' + permissionSetWritable.size() + '.'
             + (unresolvedDeclarations.isEmpty()
                ? ''
                : ' DECLARED BUT NOT FOUND IN THIS ORG: '
                  + String.join(unresolvedDeclarations, ', ')
                  + ' — check the API names on AINetworkServicesPod.');
    }

    /** One line per object saying which signal put it in scope. */
    private void recordReasons() {
        for (String o : owned) {
            List<String> why = new List<String>();
            if (declaredObjects.contains(o)) {
                // The declared names are logical; "o" is the API name they
                // resolved to, which may carry a __c. Compare normalized or
                // the automation note silently never appears.
                Boolean automated = false;
                for (String a : AINetworkServicesPod.CREATED_BY_AUTOMATION) {
                    if (AINetworkServicesPod.normalize(a)
                            == AINetworkServicesPod.normalize(
                                o.endsWith('__c') ? o.removeEnd('__c') : o)) {
                        automated = true;
                        break;
                    }
                }
                why.add(automated
                    ? 'declared (created by automation, not by people)'
                    : 'declared');
            }
            if (writable.contains(o)) {
                why.add('profile create or edit');
            }
            if (recordTypeObjects.contains(o)) {
                why.add('Network Services record type');
            }
            if (permissionSetWritable.contains(o) && !writable.contains(o)) {
                why.add('permission set');
            }
            reasonOf.put(o, String.join(why, ' + '));
        }
    }

    /**
     * Scope test used by the exporter and the search.
     *
     * Case-insensitive on purpose. ObjectPermissions.SobjectType and
     * Schema.getGlobalDescribe().keySet() do not reliably agree on casing, and
     * a case-sensitive Set comparison between them produced an EMPTY scope:
     * zero objects, zero fields, zero edges, and 350 orphan automation nodes
     * that looked like a graph.
     */
    public Boolean covers(String objectApiName) {
        if (String.isBlank(objectApiName)) {
            return false;
        }
        String key = objectApiName.toLowerCase();
        if (!ownedLower.isEmpty()) {
            return ownedLower.contains(key);
        }
        return !profileFound || readableLower.contains(key);
    }

    private Set<String> ownedLower = new Set<String>();
    private Set<String> readableLower = new Set<String>();

    private void indexLowercase() {
        for (String o : owned) {
            ownedLower.add(o.toLowerCase());
        }
        for (String r : readable) {
            readableLower.add(r.toLowerCase());
        }
    }

    /** Every profile in the org with how many objects each can create or edit. */
    public static List<Map<String, Object>> candidates() {
        Map<Id, String> nameOf = new Map<Id, String>();
        Map<Id, Integer> writableOf = new Map<Id, Integer>();
        for (PermissionSet ps : [
                SELECT Id, Profile.Name FROM PermissionSet
                WHERE IsOwnedByProfile = true LIMIT 200]) {
            nameOf.put(ps.Id, ps.Profile.Name);
            writableOf.put(ps.Id, 0);
        }
        for (AggregateResult ar : [
                SELECT ParentId pid, COUNT(Id) n FROM ObjectPermissions
                WHERE ParentId IN :nameOf.keySet()
                AND (PermissionsCreate = true OR PermissionsEdit = true)
                GROUP BY ParentId]) {
            writableOf.put((Id) ar.get('pid'), (Integer) ar.get('n'));
        }
        List<Map<String, Object>> out = new List<Map<String, Object>>();
        for (Id psId : nameOf.keySet()) {
            out.add(new Map<String, Object>{
                'name' => nameOf.get(psId),
                'writable' => writableOf.get(psId)
            });
        }
        return out;
    }
}
