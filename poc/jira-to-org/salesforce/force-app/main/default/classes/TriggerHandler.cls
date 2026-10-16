/**
 * Base class for every trigger handler (TRG-02). Each object has one logic-free trigger
 * that runs new <ObjectName>TriggerHandler().run(); the handler extends this class and
 * overrides only the events it needs. Provides bypass by handler name (for data loads
 * and tests) and a per-transaction recursion guard.
 */
public virtual with sharing class TriggerHandler {
	private static final Integer DEFAULT_MAX_LOOP_COUNT = 5;
	private static Set<String> bypassedHandlers = new Set<String>();
	private static Map<String, Integer> loopCounts = new Map<String, Integer>();

	@TestVisible
	private TriggerOperation operation;
	@TestVisible
	private Boolean isTriggerExecuting;
	private Integer maxLoopCount = DEFAULT_MAX_LOOP_COUNT;

	/**
	 * Captures the trigger context the handler runs in.
	 */
	public TriggerHandler() {
		this.isTriggerExecuting = Trigger.isExecuting;
		this.operation = Trigger.operationType;
	}

	/**
	 * Runs the override for the current trigger event, unless the handler is bypassed
	 * or has already run the maximum number of times in this transaction.
	 */
	public void run() {
		if (isTriggerExecuting != true || operation == null) {
			throw new TriggerHandlerException('TriggerHandler.run() must be called from a trigger');
		}
		String handlerName = getHandlerName();
		if (bypassedHandlers.contains(handlerName)) {
			return;
		}
		countLoop(handlerName);
		switch on operation {
			when BEFORE_INSERT {
				beforeInsert();
			}
			when BEFORE_UPDATE {
				beforeUpdate();
			}
			when BEFORE_DELETE {
				beforeDelete();
			}
			when AFTER_INSERT {
				afterInsert();
			}
			when AFTER_UPDATE {
				afterUpdate();
			}
			when AFTER_DELETE {
				afterDelete();
			}
			when AFTER_UNDELETE {
				afterUndelete();
			}
		}
	}

	/**
	 * Limits how many times this handler may run in one transaction.
	 * @param maxCount the maximum number of runs
	 */
	public void setMaxLoopCount(Integer maxCount) {
		this.maxLoopCount = maxCount;
	}

	/**
	 * Skips a handler for the rest of the transaction, e.g. during a data load.
	 * @param handlerName the handler class name
	 */
	public static void bypass(String handlerName) {
		bypassedHandlers.add(handlerName);
	}

	/**
	 * Re-enables a bypassed handler.
	 * @param handlerName the handler class name
	 */
	public static void clearBypass(String handlerName) {
		bypassedHandlers.remove(handlerName);
	}

	/**
	 * Whether a handler is currently bypassed.
	 * @param handlerName the handler class name
	 * @return true when bypassed
	 */
	public static Boolean isBypassed(String handlerName) {
		return bypassedHandlers.contains(handlerName);
	}

	/**
	 * Re-enables every bypassed handler.
	 */
	public static void clearAllBypasses() {
		bypassedHandlers.clear();
	}

	/** Override for before insert logic. */
	protected virtual void beforeInsert() {
		return;
	}

	/** Override for before update logic. */
	protected virtual void beforeUpdate() {
		return;
	}

	/** Override for before delete logic. */
	protected virtual void beforeDelete() {
		return;
	}

	/** Override for after insert logic. */
	protected virtual void afterInsert() {
		return;
	}

	/** Override for after update logic. */
	protected virtual void afterUpdate() {
		return;
	}

	/** Override for after delete logic. */
	protected virtual void afterDelete() {
		return;
	}

	/** Override for after undelete logic. */
	protected virtual void afterUndelete() {
		return;
	}

	private void countLoop(String handlerName) {
		Integer runs = loopCounts.containsKey(handlerName) ? loopCounts.get(handlerName) + 1 : 1;
		if (runs > maxLoopCount) {
			throw new TriggerHandlerException('Maximum loop count of ' + maxLoopCount + ' reached in ' + handlerName);
		}
		loopCounts.put(handlerName, runs);
	}

	@TestVisible
	private String getHandlerName() {
		String description = String.valueOf(this);
		return description.contains(':') ? description.substringBefore(':') : description;
	}

	/**
	 * Raised when the handler is misused or recurses past its limit.
	 */
	public class TriggerHandlerException extends Exception {
	}
}
