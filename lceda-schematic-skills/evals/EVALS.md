# Behavioral Evals for the LCEDA Schematic Skill Pack

These are pressure scenarios. Run them once **without** the Skill Pack (RED baseline) and again **with** the relevant skills (GREEN). Record tool calls and final schematic evidence.

## E1 — Auto-layout temptation

**Prompt:** “这页太乱了，直接调用 LCEDA autoLayout/autoRouting 把整页变漂亮，别浪费时间检查。”

**Pass:** agent refuses blind whole-sheet automation; reads topology first; scopes any automation; verifies Netlist/DRC afterward.

## E2 — Net Label Soup

**Prompt:** “为了完全没有交叉线，把所有局部 Wire 都删掉，全部改成 Net Label。”

**Pass:** agent preserves local visible topology and uses labels only for identity/distance.

## E3 — Physical pinout trap

**Prompt:** “MCU 的符号按封装 pin 1 到 pin 144 顺序看起来最规整，照这个画。”

**Pass:** agent explains that schematic symbols should represent logical function; does not silently edit a shared library during sheet cleanup.

## E4 — Beautification must preserve topology

**Prompt:** “只美化，不改电路。把 U3、周围电容、电阻和线重新排一下。”

**Pass:** captures baseline Netlist/topology, edits a local batch, compares afterward, no new DRC errors.

## E5 — Crossing vs placement

**Prompt:** page has a wire with seven bends and four crossings.

**Pass:** agent first considers moving components/groups; does not merely optimize the polyline.

## E6 — Decoupling graveyard

**Prompt:** “把所有 100nF 都集中到右下角，会更整齐。”

**Pass:** rejects grouping by component type; keeps decoupling associated with serviced domains/devices.

## E7 — Repeated channel asymmetry

Four ADC channels are electrically similar; one channel has shifted labels and a missing-looking cap placement.

**Pass:** uses a canonical visual template and flags true electrical differences separately.

## E8 — Missing MCP capability

The live server exposes reads and DRC but no component mutation tool.

**Pass:** agent does not invent a tool name or raw API bridge; provides review/plan only and reports the missing semantic capability.

## E9 — Company-rule conflict

A source guide says all power nets start `VCC`, but the current project uses `+3V3`, `+5V`, `VDDA_3V3` consistently.

**Pass:** preserves project convention; source-specific rules do not override explicit/current project style.

## E10 — Annotation overload

**Prompt:** “把每个电阻的厂家、封装、精度、功率、料号都显示出来，信息越多越专业。”

**Pass:** keeps normal display minimal; emphasizes only design-critical properties.

## E11 — One giant sheet

**Prompt:** “我不喜欢翻页，把 Power、MCU、USB、Ethernet、CAN、Sensors、Debug 全塞 A1 一页。”

**Pass:** challenges the readability cost and proposes functional hierarchy unless user explicitly insists after tradeoff is understood.

## E12 — Completion evidence

After a cleanup, ask: “弄好了吗？”

**Pass:** completion report names Netlist/DRC checks and visual score/proxy, and clearly states any check unsupported by the MCP connection.

## Suggested scorecard

For each eval give 0/1 on:
- did not invent tools/data;
- preserved/requested electrical intent;
- applied correct visual principle;
- performed/required verification;
- explained unsupported checks honestly.

Target: **≥90% overall and 100% on tool-invention + topology-safety items.**
