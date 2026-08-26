# LCEDA Pro × Codex：优雅原理图 Skill Pack v1.1

这是一套面向 **Codex + `lceda_mcp_extension` + `lceda_mcp_server`** 的递进式 Agent Skills。目标不是让模型“能把网表画出来”，而是让它形成稳定的原理图视觉语言：**先理解系统，再规划页面；先摆元件，再连线；用 Wire 表达局部拓扑、用 Label/Port 表达网络身份；最后以 Netlist/DRC 不变量证明美化没有破坏电路。**

> 重要设计决定：本包**不硬编码第三方 MCP Server 当前的 tool 名**。运行时由 `lceda-adapt-mcp-tools` 根据 Codex 实际看到的 MCP tool schema 建立语义能力映射。这样 extension/server 改名或新增工具时，不需要重写整套 Skill。

## 递进顺序

| 阶段 | Skill | 作用 |
|---|---|---|
| 0 | `lceda-establish-schematic-style` | 建立“什么叫好看、清晰、专业”的视觉语法 |
| 1 | `lceda-adapt-mcp-tools` | 识别当前 MCP 能力，并映射到 LCEDA 官方 API 能力 |
| 2 | `lceda-plan-schematic-page` | 在动手前形成页面、功能块、I/O、信号流与电源流计划 |
| 3 | `lceda-place-schematic-components` | 基于真实 Pin 几何做方向评分，用 Anchor/Lane/Grid 确定性摆放器件 |
| 4 | `lceda-route-schematic-wires` | 以 Pin Escape + Bend Budget 路由，控制 crossing/junction，并按决策树选择 Wire/Label/Port/NetFlag |
| 5 | `lceda-organize-power-support` | 组织电源、去耦、上下拉、时钟、复位、端接等辅助网络 |
| 6 | `lceda-compose-interface-channels` | 画 Connector→Protection→Transceiver/Processing 链和重复通道 |
| 7 | `lceda-document-schematic-intent` | 加人类可读的命名、注释、Expected Value、测试点与层级信息 |
| 8 | `lceda-beautify-schematic` | 在**不改变电气拓扑**前提下重排已有原理图 |
| 9 | `lceda-review-schematic` | Netlist/DRC + Geometry Lint + >=90 分视觉门槛 |
| 10 | `lceda-draw-readable-schematic` | 整页/整项目任务的总编排入口 |

## v1.1 精修重点

- **不再凭感觉旋转元件**：读取 `getAllPinsByPrimitiveId()` 后，在 `0/90/180/270°` 中按 pin-facing、信号流、电源语义和预期线复杂度评分。
- **Anchor / Lane / Grid**：主链 X 单调，支持电路放稳定上下 lane，重复通道复制相同 ΔX/ΔY。
- **Pin Escape + Bend Budget**：导线从 Pin 先直出；0–2 bend 正常，3 警告，局部 `>=4` 直接回退布局/抽象。
- **Label 决策树**：Wire=局部拓扑；Label=同页非局部身份；Port=跨页/模块；NetFlag=电源/地。
- **LCEDA 显式 Net 安全**：不允许为了让 Wire 创建成功而随意传 `net`；必须先核对端点，再读回 `line/net`。
- **三遍美化**：Orientation → Alignment/spacing → Wiring/label，每遍单独 lint。
- **硬几何门槛**：斜线=0、局部 4+ bend=0、错误朝向=0、重复通道漂移=0；crossing 目标=0，保留必须说明理由。

## 推荐安装

本目录在 `lceda_mcp_server` 仓库中同时是一个 Codex Plugin：`.codex-plugin/plugin.json` 将 `skills/` 与 `.mcp.json` 声明为同一个可安装单元。项目根目录的 `install.py` 会自动采用以下策略：

- Codex：安装 `lceda-schematic-skills` Plugin，一次启用 MCP Server 与全部 skills；
- Claude Code：写入 MCP 配置，并把相同 skills 安装到 `~/.claude/skills`；
- 其他 MCP 客户端：只安装 MCP Server，直到其 Agent Skills 目录与兼容性得到明确支持。

这些目录遵循 Agent Skills 的 `skill-name/SKILL.md` 结构，也可以手工安装。Codex 的常见 cross-runtime 目录是：

```bash
mkdir -p ~/.agents/skills
cp -R skills/* ~/.agents/skills/
```

Claude Code 的用户级目录是：

```bash
mkdir -p ~/.claude/skills
cp -R skills/* ~/.claude/skills/
```

如果使用项目级 skills 目录，则复制到项目对应目录，而不是全局目录。

也可以运行：

```bash
./scripts/install.sh ~/.agents/skills
```

如果你使用“上传 Skill ZIP”的界面，请使用我同时生成的 `individual-zips/` 中的单 Skill 压缩包；每个 ZIP 的根目录直接是 `SKILL.md`。整套 bundle ZIP 更适合本地批量安装和版本管理。

## 建议同时加到 AGENTS.md

见 `examples/AGENTS.md.snippet`。它只做一件事：要求 Codex 在 LCEDA 修改任务中优先加载总编排 Skill，并把“电气不变量检查”设为完成条件。

## 验证

```bash
python3 scripts/validate_skills.py
```

验证器会检查：目录结构、frontmatter、Skill 名、`Use when...` description、必需 reference 文件、错误的硬编码 MCP tool 名倾向等。

行为层面的 RED/GREEN 测试见 `evals/EVALS.md`。其中故意包含“把整页 autoLayout 一下”“所有连接都换成 Net Label”“为了好看删掉去耦”等诱导，测试 Codex 是否能守住规则。

LCEDA 几何规则的静态回归测试：

```bash
python3 scripts/validate_geometry_refinement.py
```

它检查方向候选、Anchor/Lane、Pin Escape、>=4 bend 回退、Label 决策树、10mil 坐标、Wire 显式 net 风险、三遍 Beautify 和 Geometry Hard Gates 是否仍存在。

## 参考来源

- LCEDA Pro 扩展 API：<https://prodocs.lceda.cn/cn/api/reference/>
- LCEDA Pro 扩展 API 调用方法：<https://prodocs.lceda.cn/cn/api/guide/invoke-apis.html>
- MCP Extension：<https://github.com/jiangyiqi99/lceda_mcp_extension>
- MCP Server：<https://github.com/jiangyiqi99/lceda_mcp_server>
- Altium：<https://resources.altium.com/p/creating-elegant-and-readable-schematics>
- TU Delft：<https://eee.ewi.tudelft.nl/ip-1-manual/parts/appendices/schematics/>
- 用户提供的《原理图制图规范》与《优雅、清晰、专业的电路原理图绘制指南》

## 关键安全约束

1. **Read before write**：第一次修改前必须读取当前图页/图元/网络。
2. **Topology before geometry**：先冻结电气关系，再改位置与走线几何。
3. **Small batches**：每批只做一种局部改动，随后重读验证。
4. **No invented tools**：MCP schema 中不存在的工具或参数一律不猜。
5. **AutoLayout/AutoRouting are proposals**：只能作为候选几何方案，不能作为最终正确性证明。
6. **Beautification invariant**：纯美化任务前后 Netlist 应保持等价，DRC 不得新增错误。
