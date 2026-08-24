# 嘉立创 EDA AI Agent

这是一个面向嘉立创 EDA 专业版的本地 AI 自动化框架。MCP 层无项目状态；只有 Python Broker 在进程内保存 WebSocket 连接和待处理请求。服务停止后，连接、请求和临时图片都会消失。

## 架构

```text
MCP Client / AI Agent
        |
        | Streamable HTTP: POST /mcp
        v
Stateless MCP tools
        |
        | in-process call
        v
In-memory asyncio Broker
        |
        | JSON over WebSocket: /ws
        v
JLCEDA TypeScript Extension
        |
        v
JLCEDA Extension API (eda.*)
```

截图不会通过 WebSocket 传 Base64。Extension 通过 `POST /upload/image` 上传 Blob，并将 `/files/{id}` 临时 URL 返回给 MCP 调用方。图片默认 5 分钟过期，服务退出时立即删除。

## 目录

```text
lceda_mcp_server/
  main.py                 # 独立服务入口
  application.py          # HTTP、WebSocket、MCP ASGI 组合
  mcp_api/                # 无状态 MCP 工具定义
  broker/                 # 唯一有状态组件（仅内存）
  protocol/               # WebSocket JSON 协议
  files/                  # 临时图片存储
  tests/

lceda_mcp_extension/
  src/main.ts
  src/websocket/          # 注册、心跳、RPC 响应、重连
  src/commands/           # schematic、PCB、DRC、capture
  src/utils/
  extension.json
  build/dist/             # npm run build 生成 .eext
```

## 启动后端

项目已经使用 `lceda_mcp_server/.venv` 安装依赖：

```bash
cd lceda_mcp_server
source .venv/bin/activate
python main.py
```

默认地址：

- MCP：`http://127.0.0.1:8000/mcp`
- Extension WebSocket：`ws://127.0.0.1:8000/ws`
- 健康检查：`http://127.0.0.1:8000/health`
- 图片上传：`http://127.0.0.1:8000/upload/image`

## 自动配置 MCP Client

后端启动后，可运行安装脚本自动扫描本机已安装的 MCP Client，并把
`jlceda-ai-agent` 服务写入相应的全局配置文件：

```bash
cd lceda_mcp_server
python install.py
```

脚本支持 Claude Desktop/Code、Cursor、Windsurf、Codex、Cline、Roo Code、
Kilo Code、VS Code、Gemini CLI、OpenCode、Kimi Code、Zed 等常见 Client。
它只自动处理已检测到的 Client，不会覆盖配置中的其他 MCP 服务；JSON 或
TOML 无法解析时会跳过该文件。

对支持 Agent Skills 且安装路径已经验证的客户端，脚本会同时安装原理图
skills：Codex 通过 `lceda-schematic-skills` Plugin 一次安装 MCP Server 与
skills；Claude Code 写入 MCP 配置并同步 skills 到 `~/.claude/skills`。
其他客户端目前保持 MCP-only 安装。

Codex Plugin 将该 MCP Server 的 `default_tools_approval_mode` 固定为
`approve`。嘉立创 EDA 主程序支持直接撤销修改，因此该 Server 的工具调用
默认无需逐次批准。

```bash
python install.py --list                         # 查看支持项及扫描结果
python install.py codex,cursor                   # 安装到指定 Client
python install.py --url http://127.0.0.1:9000/mcp
python install.py --dry-run                      # 只预览
python install.py --uninstall codex              # 从指定 Client 中移除
```

安装后需要完全重启对应的 MCP Client；Codex 应在新任务中使用新 Plugin。
安装脚本只负责 Client/Plugin 配置，后端服务仍需按下节所述单独启动。

可用环境变量：

| 名称 | 默认值 | 说明 |
| --- | ---: | --- |
| `JLCEDA_HOST` | `127.0.0.1` | 监听地址 |
| `JLCEDA_PORT` | `8000` | 监听端口 |
| `JLCEDA_RPC_TIMEOUT` | `30` | Extension RPC 超时秒数 |
| `JLCEDA_HEARTBEAT_TIMEOUT` | `30` | 项目离线判定秒数 |
| `JLCEDA_IMAGE_TTL` | `300` | 临时图片有效期秒数 |
| `JLCEDA_MAX_IMAGE_BYTES` | `12582912` | 单张图片上限 |
| `JLCEDA_MAX_ARTIFACT_BYTES` | `134217728` | 单个 EDA 导出文件上限 |
| `JLCEDA_PUBLIC_BASE_URL` | 空 | 反向代理后对外返回的基础 URL |
| `JLCEDA_LOG_LEVEL` | `INFO` | 服务日志级别；设为 `DEBUG` 可查看正常事件 |
| `JLCEDA_ACCESS_LOG` | `false` | 是否记录每个 HTTP 请求；设为 `true` 可恢复 Uvicorn access log |

## 构建并安装 Extension

```bash
cd lceda_mcp_extension
npm install
npm run typecheck
npm run build
```

生成文件：

```text
lceda_mcp_extension/build/dist/jlceda-ai-agent_v0.3.1.eext
```

在嘉立创 EDA 专业版 V3 中通过“高级 → 扩展管理器 → 导入”安装。安装后必须为该扩展启用“允许外部交互”，否则官方 `SYS_WebSocket` 和 `SYS_ClientUrl` API 会拒绝 WebSocket 与图片上传。

Extension 使用当前工程 UUID 作为 `project_id`，同时在 `list_projects` 中提供工程名称。切换工程后，下一次心跳会自动重新注册。因此 AI 应先调用 `list_projects`，再将返回的 `project_id` 放进后续每个 EDA 工具调用。

如果后端地址改变，请同步修改：

```text
lc_extension/src/config.ts
```

## MCP 工具

工程与库：

- `list_projects`、`project.get_info`
- `component.search`

原理图读取与检查：

- `schematic.get_info`、`schematic.get_primitives_bbox`
- `schematic.get_netlist`、`schematic.run_drc`

原理图器件与清理：

- `schematic.place_component`、`schematic.add_component`
- `schematic.modify_component`、`schematic.delete_components`
- `schematic.delete_wires`、`schematic.modify_wire`、`schematic.clear`
- `schematic.modify_pin`（符号编辑器中的独立引脚）

原理图网络与布线：

- `schematic.create_net_flag`、`schematic.create_net_port`
- `schematic.create_net_label`、`schematic.modify_net_label`
- `schematic.modify_net_marker`、`schematic.connect_net`
- `schematic.create_wire`、`schematic.connect`
- `schematic.auto_layout`、`schematic.auto_route`

PCB：

- `pcb.get_info`、`pcb.get_primitives_bbox`
- `pcb.place_component`、`pcb.modify_component`、`pcb.delete_components`
- `pcb.create_track`、`pcb.modify_track`、`pcb.create_board_outline`
- `pcb.create_via`、`pcb.modify_via`、`pcb.delete_routing_primitives`
- `pcb.clear_routing`、`pcb.route_net`、`pcb.auto_route`、`pcb.auto_layout`
- `pcb.run_drc`

截图：

- `capture.schematic`、`capture.pcb`、`capture.region`

原始 EDA API 覆盖：

- `eda.list_apis`、`eda.describe_api`、`eda.describe_type`：发现当前 EDA 运行时
  能力，并返回由官方 `.d.ts` 生成的完整方法重载、枚举、接口和类型别名
- `eda.call`：调用 `dmt_*`、`lib_*`、`pnl_*`、`sch_*`、`pcb_*` 及受控
  `sys_*` 中的公开 API
- `eda.call_primitive`：读取图元实例的 `getState_*`/其他实例方法，或通过
  `toAsync()` → setters → `done()` 原子提交一组图元修改
- `eda.export_file`、`eda.export_primitive_file`：执行返回一个或多个
  `File/Blob` 的命名空间/图元实例 API，并取得临时下载 URL
- `eda.subscribe`、`eda.unsubscribe`、`eda.poll_events`：事件订阅与读取

`eda.call` 对可能修改工程的方法要求 `confirm_mutation=true`。需要把 File 传给导入、
转换等 API 时，可在参数中使用
`{"$file_base64":"...","name":"input.epro","type":"application/octet-stream"}`；
单个内联文件上限为 8 MiB。

以官方 `@jlceda/pro-api-types 0.4.15` 为准，覆盖审计会检查 95 个 EDA 顶层公开
命名空间。目前其中 92 个可由上述通道访问；仅明确保留三个宿主级命名空间：
`sys_ClientUrl`（任意外部请求）、`sys_FileSystem`（宿主文件系统）和
`sys_WebSocket`（Broker 连接本身）。工程文件导入/导出仍可通过受控的
`sys_FileManager` 与 Broker 临时文件通道完成。

推荐的 AI 选型流程是：先调用 `component.search`，读取每个候选项的名称、描述、
符号、封装、3D 模型、扩展属性以及 `library_uuid`/`device_uuid`；AI 选定后，再将
这两个 UUID 传给 `schematic.place_component` 精确放置。搜索结果按页返回（默认 20、
最多 100 条/页），当 `has_more` 为 `true` 时 AI 可以继续请求下一页，避免一次把大量
候选塞满模型上下文。`schematic.add_component` 仍保留为“搜索并放置第一个结果”的兼容
快捷工具。

跨区域原理图连接优先使用 `schematic.connect_net`。它把同名网络标志、端口或
标签直接放到各个目标引脚上，不会因导线交叉形成意外短路。需要绘制实体导线时，
使用 `schematic.connect` 的 `waypoints` 或 `schematic.create_wire` 的 `points`
显式指定正交路径；默认会检查与不同网络导线的相交，并以 `WIRE_CROSSING` 拒绝
危险操作。只有调用方明确传入 `allow_crossings=true` 时才跳过该保护。

`schematic.get_info` 会为每个器件返回边界框，并为每个引脚返回相对于器件边界的
`side`（`left`、`right`、`top`、`bottom`）。`schematic.connect_net` 默认使用
`side=auto` 读取这个方位；创建或修改端口、网络标志、网络标签时也可以显式传入方位。
嘉立创原始 `createNetLabel(x, y, net)` 没有方位参数，因此 Extension 会在创建后修改
标签的旋转和对齐方式；调用方仍可用 `rotation`、`align_mode` 覆盖默认映射。
嘉立创 API 明确不支持修改已放置器件实例的 ComponentPin；这类引脚的方位可读但
不可直接改写。`schematic.modify_pin` 只操作符号编辑器中的独立 Pin 图元。

`schematic.clear` 会删除当前图页中的已放置器件、网络标志和导线，但保留无引脚、
无位号、无网络的图框/标题栏图元。精确清理可改用 `schematic.delete_components`
或 `schematic.delete_wires`。

`pcb.route_net` 会调用嘉立创的单网络自动布线；`pcb.auto_route` 支持网络白名单、
排除列表和速度/布通率策略。原理图与 PCB 的 DRC 均使用详细结果模式。部分嘉立创 API
仍标记为 Beta，升级 EDA 后应重新运行 TypeScript 类型检查并做真机回归。

## 验证

```bash
cd lceda_mcp_server
.venv/bin/python -m pytest -q

cd ../lceda_mcp_extension
npm audit --audit-level=moderate
npm run audit:api
npm run typecheck
npm run build
```

当前自动验证包含协议校验、Broker RPC 往返与错误诊断、能力检查、事件缓冲、HTTP
图片/导出文件上传读取、Extension/MCP 命令面一致性，以及 Extension 的官方类型检查
和 `.eext` 打包。

## 设计边界

- 不使用 Redis、SQLite 或任何数据库。
- MCP 工具不持有 WebSocket、工程或 EDA 状态。
- Broker 只保存在线连接、心跳时间和正在等待的请求。
- Extension 不认识 MCP，只处理 Broker JSON RPC。
- 不存储 AI 对话或 PCB/原理图数据。
- 图片和导出文件只存在系统临时目录并按 TTL 清理。

嘉立创官方参考：[扩展 API 入门](https://prodocs.lceda.cn/cn/api/guide/how-to-start.html)、[调用扩展 API](https://prodocs.lceda.cn/cn/api/guide/invoke-apis.html)、[SYS_WebSocket](https://prodocs.lceda.cn/cn/api/reference/pro-api.sys_websocket.html)。
