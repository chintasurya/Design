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
    public String note;

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

        List<PermissionSet> owned = [
            SELECT Id FROM PermissionSet
            WHERE IsOwnedByProfile = true AND Profile.Name = :key
            LIMIT 1];

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
        s.resolveOwned(key);
        cache.put(key, s);
        return s;
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
            String name = (rt.DeveloperName == null ? '' : rt.DeveloperName)
                          .toLowerCase().replaceAll('[^a-z0-9]', '');
            if (name.contains('network')) {
                recordTypeObjects.add(rt.SobjectType);
            }
        }
        owned.addAll(writable);
        owned.addAll(recordTypeObjects);

        if (owned.isEmpty()) {
            owned.addAll(readable);
            note = 'Profile "' + profileName + '" grants no create or edit access '
                 + 'and no object carries a Network record type, so the scope '
                 + 'falls back to all ' + readable.size() + ' readable objects';
            return;
        }
        note = owned.size() + ' objects owned by "' + profileName + '" ('
             + writable.size() + ' writable, ' + recordTypeObjects.size()
             + ' with a Network record type) out of ' + readable.size()
             + ' readable';
    }

    /** Scope test used by the builder and the search. */
    public Boolean covers(String objectApiName) {
        if (!owned.isEmpty()) {
            return owned.contains(objectApiName);
        }
        return !profileFound || readable.contains(objectApiName);
    }

    /** Profiles in the org with how many objects each can create or edit. */
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
