/**
 * Live Jira and Confluence search, through Named Credentials.
 *
 * Optional. When a credential is not configured the source reports that
 * plainly and contributes nothing, rather than inventing a result. The whole
 * point of the graph is that every claim traces to an artifact, so a source
 * that cannot be reached must say so.
 */
public with sharing class AIAtlassianSource {

    private static final Integer TIMEOUT_MS = 20000;
    private static final Integer MAX_RESULTS = 5;

    public class Result {
        public List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>();
        public String note;
    }

    public static Result searchJira(String namedCredential, String projectKey,
                                    Set<String> terms) {
        Result r = new Result();
        if (String.isBlank(namedCredential)) {
            r.note = 'Jira not configured';
            return r;
        }
        String text = String.join(new List<String>(terms), ' ');
        String jql = 'text ~ "' + text.replace('"', '') + '"';
        if (String.isNotBlank(projectKey)) {
            jql = 'project = ' + projectKey + ' AND ' + jql;
        }
        jql += ' ORDER BY updated DESC';

        HttpResponse res = send(namedCredential,
            '/rest/api/3/search?maxResults=' + MAX_RESULTS
            + '&fields=summary,status,updated&jql=' + EncodingUtil.urlEncode(jql, 'UTF-8'));
        if (res == null) {
            r.note = 'Jira callout failed';
            return r;
        }
        if (res.getStatusCode() != 200) {
            r.note = 'Jira returned HTTP ' + res.getStatusCode();
            return r;
        }

        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> issues = (List<Object>) body.get('issues');
        if (issues == null || issues.isEmpty()) {
            r.note = 'Jira reachable, nothing matched';
            return r;
        }
        for (Object o : issues) {
            Map<String, Object> issue = (Map<String, Object>) o;
            Map<String, Object> f = (Map<String, Object>) issue.get('fields');
            String key = String.valueOf(issue.get('key'));
            r.findings.add(AIContextSlice.build(
                'req:' + key, 'Requirement', String.valueOf(f.get('summary')),
                'Matched the request text in Jira',
                'Two Hop', 'Medium', 'Jira',
                'JIRA_ISSUE ' + key + ' · updated ' + String.valueOf(f.get('updated'))));
        }
        return r;
    }

    public static Result searchConfluence(String namedCredential, String spaceKey,
                                          Set<String> terms) {
        Result r = new Result();
        if (String.isBlank(namedCredential)) {
            r.note = 'Confluence not configured';
            return r;
        }
        String text = String.join(new List<String>(terms), ' ');
        String cql = 'type = page AND text ~ "' + text.replace('"', '') + '"';
        if (String.isNotBlank(spaceKey)) {
            cql = 'space = ' + spaceKey + ' AND ' + cql;
        }

        HttpResponse res = send(namedCredential,
            '/wiki/rest/api/search?limit=' + MAX_RESULTS
            + '&cql=' + EncodingUtil.urlEncode(cql, 'UTF-8'));
        if (res == null) {
            r.note = 'Confluence callout failed';
            return r;
        }
        if (res.getStatusCode() != 200) {
            r.note = 'Confluence returned HTTP ' + res.getStatusCode()
                   + (res.getStatusCode() == 403
                      ? ' (the account has no Confluence licence)' : '');
            return r;
        }

        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> results = (List<Object>) body.get('results');
        if (results == null || results.isEmpty()) {
            r.note = 'Confluence reachable, nothing matched';
            return r;
        }
        for (Object o : results) {
            Map<String, Object> hit = (Map<String, Object>) o;
            Map<String, Object> content = (Map<String, Object>) hit.get('content');
            String id = content == null ? '?' : String.valueOf(content.get('id'));
            String title = String.valueOf(hit.get('title'));
            r.findings.add(AIContextSlice.build(
                'doc:' + id, 'DesignDocument', title,
                'Matched the request text in Confluence',
                'Two Hop', 'Medium', 'Confluence',
                'CONFLUENCE_PAGE id ' + id + ' · ' + title));
        }
        return r;
    }

    private static HttpResponse send(String namedCredential, String path) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:' + namedCredential + path);
        req.setMethod('GET');
        req.setHeader('Accept', 'application/json');
        req.setTimeout(TIMEOUT_MS);
        try {
            return new Http().send(req);
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'Atlassian callout failed: ' + e.getMessage());
            return null;
        }
    }
}
