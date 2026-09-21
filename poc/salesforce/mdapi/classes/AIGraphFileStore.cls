/**
 * Layer 5 storage: the graph as a Salesforce File.
 *
 * Records were the wrong home. 36,330 nodes and 76,980 edges came to 113,310
 * rows and roughly 221 MB of DATA storage, which filled a sandbox for a single
 * pod. A File counts against FILE storage, a separate allocation, and the same
 * graph is about 1 MB as JSON.
 *
 * ContentVersion rather than a Static Resource because Apex can insert a
 * ContentVersion directly; writing a Static Resource at runtime needs a
 * Metadata API callout.
 *
 * Saving with an existing ContentDocumentId creates a new VERSION, so every
 * prior build is retained by the platform.
 *
 * That is retention, not a snapshot model, and the two are easy to confuse.
 * load() always takes IsLatest = true, nothing reads an earlier version, and
 * nothing compares two of them. A build stamps a snapshotId and an exportedAt,
 * and AI_Change_Request__c records which snapshot its analysis ran against, so
 * an answer can always be tied back to the state of the org it was given for.
 * What is absent is everything built on top of that: no diff between builds,
 * no validFrom or validTo on a node or an edge, no record of what appeared or
 * disappeared, and no way to ask what the graph held last Tuesday without
 * fetching an old ContentVersion by hand. Versioning makes those buildable.
 * It does not make them built.
 *
 * "without sharing" is deliberate: the graph is org-wide reference metadata
 * built by whichever user ran the sync, and every console user must be able to
 * read it. It contains component names and provenance, never record data.
 */
public without sharing class AIGraphFileStore {

    public static final String SALESFORCE = 'graph-salesforce';
    public static final String JIRA = 'graph-jira';
    public static final String CONFLUENCE = 'graph-confluence';
    public static final String COMBINED = 'graph-combined';

    public class GraphFileException extends Exception {}

    /** Roughly 1.7 MB of JSON is the practical ceiling: see AIGraphMemory. */
    private static final Integer MAX_BYTES = 2500000;

    public static Id save(String fileName, AIGraphDocument doc) {
        doc.exportedAt = System.now().formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\'');
        String body = JSON.serialize(doc);

        if (body.length() > MAX_BYTES) {
            throw new GraphFileException(
                'Graph is ' + (body.length() / 1024) + ' KB, over the '
                + (MAX_BYTES / 1024) + ' KB ceiling. Loading it would exceed the '
                + 'Apex heap limit. Narrow the pod scope rather than raising this.');
        }

        ContentVersion cv = new ContentVersion(
            Title = fileName,
            PathOnClient = fileName + '.json',
            VersionData = Blob.valueOf(body),
            IsMajorVersion = true);

        Id existingDoc = documentIdFor(fileName);
        if (existingDoc != null) {
            cv.ContentDocumentId = existingDoc;    // new version, not a new file
        }
        insert cv;
        return cv.Id;
    }

    public static AIGraphDocument load(String fileName) {
        List<ContentVersion> rows = [
            SELECT VersionData FROM ContentVersion
            WHERE Title = :fileName AND IsLatest = true
            ORDER BY CreatedDate DESC LIMIT 1];
        if (rows.isEmpty()) {
            return null;
        }
        return (AIGraphDocument) JSON.deserialize(
            rows[0].VersionData.toString(), AIGraphDocument.class);
    }

    /** Size and counts without paying to deserialize the body. */
    public static Map<String, Object> describe(String fileName) {
        List<ContentVersion> rows = [
            SELECT ContentSize, VersionNumber, CreatedDate
            FROM ContentVersion
            WHERE Title = :fileName AND IsLatest = true
            ORDER BY CreatedDate DESC LIMIT 1];
        if (rows.isEmpty()) {
            return new Map<String, Object>{ 'exists' => false };
        }
        return new Map<String, Object>{
            'exists' => true,
            'bytes' => rows[0].ContentSize,
            'kb' => rows[0].ContentSize / 1024,
            'version' => rows[0].VersionNumber,
            'builtAt' => rows[0].CreatedDate
        };
    }

    public static void remove(String fileName) {
        Id docId = documentIdFor(fileName);
        if (docId == null) {
            return;
        }
        delete [SELECT Id FROM ContentDocument WHERE Id = :docId];
    }

    private static Id documentIdFor(String fileName) {
        List<ContentVersion> rows = [
            SELECT ContentDocumentId FROM ContentVersion
            WHERE Title = :fileName AND IsLatest = true
            ORDER BY CreatedDate DESC LIMIT 1];
        return rows.isEmpty() ? null : rows[0].ContentDocumentId;
    }
}
