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
