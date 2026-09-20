/**
 * The bounded evidence package returned by the graph layer.
 *
 * This is deliberately small. It carries the nodes that matter for one
 * request plus their provenance, never the raw artifact bodies. Codex
 * fetches source on demand; the slice only says what to fetch and why.
 */
public class AIContextSlice {

    public String snapshotId;
    public String summary;
    public List<Finding> findings = new List<Finding>();

    public class Finding {
        public String nodeId;
        public String nodeType;
        public String nodeName;
        public String relationshipPath;
        public String impact;
        public String riskTier;
        public String sourceSystem;
        public String provenance;
        public String artifactHash;
        public Decimal confidence;
    }

    /** Build one finding. Shared so every source produces the same shape. */
    public static Finding build(String nodeId, String nodeType, String nodeName,
            String path, String impact, String risk, String sourceSystem,
            String provenance) {
        Finding f = new Finding();
        f.nodeId = nodeId;
        f.nodeType = nodeType;
        f.nodeName = nodeName;
        f.relationshipPath = path;
        f.impact = impact;
        f.riskTier = risk;
        f.sourceSystem = sourceSystem;
        f.provenance = provenance;
        f.confidence = 1.0;
        return f;
    }

    /** Project the slice onto findings rows hung off a request. */
    public List<AI_Graph_Finding__c> toRecords(Id requestId) {
        List<AI_Graph_Finding__c> rows = new List<AI_Graph_Finding__c>();
        for (Finding f : findings) {
            rows.add(new AI_Graph_Finding__c(
                Change_Request__c  = requestId,
                Node_Id__c         = f.nodeId,
                Node_Type__c       = f.nodeType,
                Node_Name__c       = f.nodeName,
                Relationship_Path__c = f.relationshipPath,
                Impact__c          = f.impact,
                Risk_Tier__c       = f.riskTier,
                Source_System__c   = f.sourceSystem,
                Provenance__c      = f.provenance,
                Artifact_Hash__c   = f.artifactHash,
                Confidence__c      = f.confidence
            ));
        }
        return rows;
    }
}
