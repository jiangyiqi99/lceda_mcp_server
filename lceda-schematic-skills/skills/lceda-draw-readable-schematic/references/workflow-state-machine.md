# End-to-End Workflow State Machine

```text
DISCOVER_TOOLS
   ↓
READ_TARGET
   ↓
CLASSIFY_TASK ── cleanup ─→ SNAPSHOT_TOPOLOGY → BEAUTIFY
   │                                      │
   └─ new/edit ─→ PLAN → PLACE → ROUTE ←─┘
                         ↓
                 SUPPORT/INTERFACES
                         ↓
                     DOCUMENT
                         ↓
                       REVIEW
                   ↙ fail    pass ↘
                REPAIR          SAVE/DONE
```

## State: DISCOVER_TOOLS
Exit condition: semantic MCP capability map is known. No invented calls.

## State: READ_TARGET
Exit condition: current page/region and existing primitives are known sufficiently to avoid overwriting unknown content.

## State: CLASSIFY_TASK
Classify into:
- new page/function;
- electrical edit;
- geometry-only cleanup;
- review-only.

This classification controls whether Netlist is expected to remain identical.

## State: PLAN
Exit condition: one page theme, I/O list, main path, power/support ownership, cross-page boundary and rough block regions are established.

## State: PLACE
Exit condition: major blocks form readable left→right/top→bottom structure and local support parts have owners. Do not route around obviously bad placement.

## State: ROUTE
Exit condition: local topology is visible with Manhattan paths, abstractions are appropriate, and crossings are minimized.

## State: SUPPORT/INTERFACES
Exit condition: power/decoupling/reset/clock/termination and boundary chains are visually coherent; repeated channels are geometrically consistent.

## State: DOCUMENT
Exit condition: names, references, values, notes, expected values, variants, and test points add intent without clutter.

## State: REVIEW
Hard gates + visual score. Failure returns to the narrowest state that can fix the defect.

## Transaction rule

A logical batch should resemble a transaction:

`read → plan exact changes → write small batch → read back → verify → continue`

If the server provides no transaction/undo primitive, smaller batches become even more important.

## Automation rule

`autoLayout`/`autoRouting` may propose geometry only when:
- scope is explicit;
- the result can be inspected;
- topology can be verified;
- the agent is prepared to reject/repair the output.

Never run it as a substitute for planning.
