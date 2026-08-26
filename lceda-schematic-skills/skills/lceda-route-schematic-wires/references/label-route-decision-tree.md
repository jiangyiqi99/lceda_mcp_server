# Wire / Label / Port / NetFlag Decision Tree

Use semantic scope first, geometry second.

## Decision tree

```text
Is this power/ground infrastructure?
  YES → NetFlag / power symbol
  NO
   ↓
Does the connection cross a sheet/module boundary?
  YES → NetPort/off-page construct
  NO
   ↓
Do the connected parts form one local causal/topological unit?
  YES → Wire; fix placement if the wire is long/ugly
  NO
   ↓
Would a direct same-sheet wire cross an unrelated block,
need >=4 bends, or span several functional regions?
  YES → same-sheet Net Label if a real label capability exists
  NO  → Wire
```

## Quantitative proxy for “non-local”

When semantic boundaries are unclear, compute a local pitch `P` from the median nearest-neighbor distance inside clean blocks. A same-sheet net becomes a label candidate when one or more is true:
- Manhattan endpoint distance exceeds roughly `4P`;
- direct route intersects the bounding region of an unrelated block;
- clean route would need `>=4` bends;
- the same control/bus identity must appear at several distant blocks and a trunk wire would dominate the page.

This is a candidate rule, not permission to destroy local topology.

## Label-stub geometry

- one short orthogonal stub, commonly one major grid;
- stub points out of the functional block, not through it;
- labels in a family align to a common X or Y;
- label text orientation remains horizontal where possible;
- do not place a label directly on top of a pin or component body;
- repeated channels use identical label offsets.

## Net Label Soup rejection

If removing a label would make it impossible to understand the local component sequence without searching elsewhere, that label is hiding too much topology. Restore the local wire.

## Capability rule

`SCH_PrimitiveComponent.createNetPort(...)` is a port API, not proof of a dedicated same-sheet Net Label API. Bind to the MCP's real label tool only if discovered. Never fake a label using a port or arbitrary text.
