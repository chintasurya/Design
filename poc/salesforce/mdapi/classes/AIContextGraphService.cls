/**
 * Contract for the graph layer.
 *
 * Semantica stays behind this interface so the org never depends on a
 * particular graph runtime, and so the console can be demonstrated before
 * the service exists.
 */
public interface AIContextGraphService {
    AIContextSlice query(AI_Change_Request__c request);
}
