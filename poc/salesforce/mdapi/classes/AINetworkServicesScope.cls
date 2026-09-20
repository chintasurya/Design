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
    public Set<String> recordTypes = new Set<String>();
    public Boolean profileFound = false;
    public String note;

    private static Map<String, AINetworkServicesScope> cache =
        new Map<String, AINetworkServicesScope>();

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

        for (ObjectPermissions op : [
                SELECT SobjectType, PermissionsCreate, PermissionsEdit
                FROM ObjectPermissions
                WHERE ParentId = :owned[0].Id AND PermissionsRead = true]) {
            s.readable.add(op.SobjectType);
            if (op.PermissionsCreate || op.PermissionsEdit) {
                s.writable.add(op.SobjectType);
            }
        }
        s.note = s.readable.size() + ' objects readable by "' + key + '", '
               + s.writable.size() + ' writable';
        cache.put(key, s);
        return s;
    }

    public Boolean covers(String objectApiName) {
        return !profileFound || readable.contains(objectApiName);
    }
}
