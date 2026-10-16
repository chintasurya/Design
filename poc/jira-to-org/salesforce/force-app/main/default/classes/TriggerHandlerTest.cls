/**
 * Tests for the TriggerHandler framework: event dispatch, bypass, recursion guard and misuse.
 */
@isTest
private class TriggerHandlerTest {
	/**
	 * Records which override ran.
	 */
	private class RecordingHandler extends TriggerHandler {
		public List<String> calls = new List<String>();
		protected override void beforeInsert() {
			calls.add('beforeInsert');
		}
		protected override void beforeUpdate() {
			calls.add('beforeUpdate');
		}
		protected override void beforeDelete() {
			calls.add('beforeDelete');
		}
		protected override void afterInsert() {
			calls.add('afterInsert');
		}
		protected override void afterUpdate() {
			calls.add('afterUpdate');
		}
		protected override void afterDelete() {
			calls.add('afterDelete');
		}
		protected override void afterUndelete() {
			calls.add('afterUndelete');
		}
	}

	private static RecordingHandler handlerFor(TriggerOperation operation) {
		RecordingHandler handler = new RecordingHandler();
		handler.isTriggerExecuting = true;
		handler.operation = operation;
		handler.setMaxLoopCount(100);
		return handler;
	}

	@isTest
	static void dispatchesEveryEventToItsOverride() {
		Map<TriggerOperation, String> expected = new Map<TriggerOperation, String>{
			TriggerOperation.BEFORE_INSERT => 'beforeInsert',
			TriggerOperation.BEFORE_UPDATE => 'beforeUpdate',
			TriggerOperation.BEFORE_DELETE => 'beforeDelete',
			TriggerOperation.AFTER_INSERT => 'afterInsert',
			TriggerOperation.AFTER_UPDATE => 'afterUpdate',
			TriggerOperation.AFTER_DELETE => 'afterDelete',
			TriggerOperation.AFTER_UNDELETE => 'afterUndelete'
		};
		Test.startTest();
		for (TriggerOperation operation : expected.keySet()) {
			RecordingHandler handler = handlerFor(operation);
			handler.run();
			System.assertEquals(new List<String>{ expected.get(operation) }, handler.calls,
				'wrong override for ' + operation);
		}
		Test.stopTest();
	}

	@isTest
	static void baseClassOverridesDoNothing() {
		TriggerHandler handler = new TriggerHandler();
		handler.isTriggerExecuting = true;
		handler.setMaxLoopCount(100);
		for (TriggerOperation operation : TriggerOperation.values()) {
			handler.operation = operation;
			handler.run();
		}
		System.assertEquals('TriggerHandler', handler.getHandlerName());
	}

	@isTest
	static void bypassSkipsTheHandlerUntilCleared() {
		RecordingHandler handler = handlerFor(TriggerOperation.AFTER_INSERT);
		String name = handler.getHandlerName();
		TriggerHandler.bypass(name);
		System.assert(TriggerHandler.isBypassed(name), 'should be bypassed');
		handler.run();
		System.assertEquals(0, handler.calls.size(), 'a bypassed handler must not run');

		TriggerHandler.clearBypass(name);
		handler.run();
		System.assertEquals(1, handler.calls.size());

		TriggerHandler.bypass(name);
		TriggerHandler.clearAllBypasses();
		System.assert(!TriggerHandler.isBypassed(name), 'clearAllBypasses re-enables every handler');
	}

	@isTest
	static void recursionStopsAtTheLoopLimit() {
		RecordingHandler handler = handlerFor(TriggerOperation.BEFORE_UPDATE);
		handler.setMaxLoopCount(2);
		handler.run();
		handler.run();
		try {
			handler.run();
			System.assert(false, 'the third run must be refused');
		} catch (TriggerHandler.TriggerHandlerException limitError) {
			System.assert(limitError.getMessage().contains('Maximum loop count of 2'), limitError.getMessage());
		}
	}

	@isTest
	static void refusesToRunOutsideATrigger() {
		TriggerHandler handler = new TriggerHandler();
		try {
			handler.run();
			System.assert(false, 'run() outside a trigger must throw');
		} catch (TriggerHandler.TriggerHandlerException misuse) {
			System.assert(misuse.getMessage().contains('must be called from a trigger'), misuse.getMessage());
		}
	}
}
