# v1.1 LCEDA Geometry Refinement Notes

This revision targets concrete failures observed in AI-drawn LCEDA schematics: wrong component orientation, arbitrary placement, ugly routing, excessive complexity, poor label use, and inconsistent alignment.

| Observed failure | v1.0 weakness | v1.1 rule |
|---|---|---|
| Component faces the wrong way | “prefer intuitive orientation” | Read live pin coordinates; score `0/90/180/270°` candidates by pin-facing, signal flow, power semantics, expected routing complexity; mirror is penalized/default-off |
| Components scattered/arbitrary | qualitative grouping only | Anchor/Lane/Grid model; main-chain X monotonic; support lanes above/below; repeated ΔX/ΔY template |
| Lines look tangled | “Manhattan, few bends” | Pin escape + normalized polyline + 0–2 bend norm; 3 warning; local `>=4` fail and return to placement/abstraction |
| Diagonal/zig-zag/U-turn wires | no explicit hard gate | diagonal=0; backtracking lint; U-turn/zig-zag rejected |
| Poor use of labels | generic Wire/Label advice | semantic decision tree: Wire local topology / Label same-sheet non-local identity / Port cross-sheet / NetFlag power |
| Net Label Soup | qualitative warning | explicit anti-soup test: if local sequence disappears, restore Wire |
| Port used because Label tool missing | not covered | capability rule: never fake same-sheet Label with NetPort/plain text |
| Accidental net mutation | general net verification | explicit LCEDA `SCH_PrimitiveWire.create(..., net)` side-effect warning + endpoint pre-read + post-read `line/net` |
| Repeated channels look uneven | “be consistent” | canonical channel transform; compare orientation, ΔX/ΔY, bend topology, label offset |
| Beautify changes everything at once | pass order too broad | three isolated passes: Orientation → Alignment/spacing → Wiring/label, with geometry lint after each |
| “Looks good” declared too early | score >=85 | hard geometry gates + target >=90; crossing exceptions require reasons |
| Wrong coordinate scale | not prominent | schematic coordinate unit fixed in workflow: 10mil/unit; never reuse PCB units |

## Geometry hard gates

For a normal refined page:
- diagonal wire segments = 0;
- local 4+ bend wires = 0 unless explicitly unavoidable;
- wrong-facing role components = 0 unless explicitly justified;
- avoidable four-way junctions = 0;
- unexplained repeated-channel geometry outliers = 0;
- critical label/text collisions = 0;
- crossings target = 0; retained crossings require rationale.

These gates are subordinate to electrical correctness: topology and DRC remain authoritative.
