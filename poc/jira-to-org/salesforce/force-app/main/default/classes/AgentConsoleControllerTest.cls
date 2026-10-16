@isTest
private class AgentConsoleControllerTest {

    private class GatewayMock implements HttpCalloutMock {
        Integer code;
        String responseBody;
        HttpRequest last;

        GatewayMock(Integer code, String responseBody) {
            this.code = code;
            this.responseBody = responseBody;
        }

        public HttpResponse respond(HttpRequest req) {
            last = req;
            HttpResponse res = new HttpResponse();
            res.setStatusCode(code);
            res.setBody(responseBody);
            return res;
        }
    }

    private static GatewayMock mock(Integer code, String responseBody) {
        GatewayMock m = new GatewayMock(code, responseBody);
        Test.setMock(HttpCalloutMock.class, m);
        return m;
    }

    @isTest
    static void routesEachCallToItsOwnPath() {
        GatewayMock m = mock(200, '{"ok":true}');
        Test.startTest();
        System.assertEquals('{"ok":true}', AgentConsoleController.status());
        System.assertEquals('callout:Agent_Gateway/v1/status', m.last.getEndpoint());

        AgentConsoleController.connectCodex('  sk-test  ');
        System.assertEquals('POST', m.last.getMethod());
        System.assert(m.last.getBody().contains('"apiKey":"sk-test"'));

        AgentConsoleController.connectCodex(null);
        System.assertEquals('{}', m.last.getBody());

        AgentConsoleController.listTickets(false);
        System.assert(m.last.getEndpoint().endsWith('/v1/jira/tickets?only_open=false'));

        AgentConsoleController.askRequirementAgent('Analyze KAN-1', 'abc123');
        System.assert(m.last.getBody().contains('"conversationId":"abc123"'));

        AgentConsoleController.startDevelopment('kan-1', '{"ticket_key":"KAN-1"}', true);
        System.assert(m.last.getBody().contains('"ticketKey":"KAN-1"'));
        System.assert(m.last.getBody().contains('"override":true'));

        AgentConsoleController.getRun('0123456789abcdef');
        System.assert(m.last.getEndpoint().endsWith('/v1/runs/0123456789abcdef'));
        AgentConsoleController.approveDeployment('0123456789abcdef');
        System.assert(m.last.getEndpoint().endsWith('/deploy'));
        AgentConsoleController.rejectDeployment('0123456789abcdef');
        System.assert(m.last.getEndpoint().endsWith('/reject'));
        AgentConsoleController.rebuildGraph();
        System.assert(m.last.getEndpoint().endsWith('/v1/graph/rebuild'));
        Test.stopTest();
    }

    @isTest
    static void rejectsBadInputBeforeAnyCallout() {
        GatewayMock m = mock(200, '{}');
        Integer refused = 0;
        try { AgentConsoleController.getRun('../v1/graph/rebuild'); } catch (AuraHandledException e) { refused++; }
        try { AgentConsoleController.startDevelopment('not a key', '{}', false); } catch (AuraHandledException e) { refused++; }
        try { AgentConsoleController.startDevelopment('KAN-1', 'not json', false); } catch (AuraHandledException e) { refused++; }
        try { AgentConsoleController.askRequirementAgent('  ', null); } catch (AuraHandledException e) { refused++; }
        System.assertEquals(4, refused);
        System.assertEquals(null, m.last, 'no callout may be made for refused input');
    }

    @isTest
    static void surfacesTheGatewayReason() {
        mock(409, '{"detail":"Connect to Codex first"}');
        try {
            AgentConsoleController.askRequirementAgent('hi', null);
            System.assert(false, 'expected an error');
        } catch (AuraHandledException e) {
            System.assertEquals('Gateway 409: Connect to Codex first', e.getMessage());
        }
        System.assert(AgentConsoleController.gatewayMessage(401, '').contains('rejected the key'));
        System.assert(AgentConsoleController.gatewayMessage(500, 'plain text').endsWith('plain text'));
        System.assert(AgentConsoleController.gatewayMessage(422, '{"detail":[{"msg":"x"}]}').contains('"msg"'));
    }
}
