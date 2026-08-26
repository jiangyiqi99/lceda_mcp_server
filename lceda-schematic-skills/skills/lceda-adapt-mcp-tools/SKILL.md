---
name: lceda-adapt-mcp-tools
description: Use when an LCEDA Pro task will use lceda_mcp_server or lceda_mcp_extension, especially at the first schematic mutation in a session or when exposed MCP tools or schemas may have changed.
---

# Adapt LCEDA MCP Tools

## Rule: schemas are the authority

Never guess a third-party MCP tool name, argument, UUID, coordinate, enum, or return shape. Inspect the MCP tools Codex actually has and map them to the semantic capabilities in `references/mcp-capability-contract.md`.

## Establish a session capability map

Before the first write, identify at least:

`READ_COMPONENTS`, `READ_WIRES`, `READ_NET_LABELS`, `READ_NETLIST`, `READ_DRC`, `PLACE_COMPONENT`, `MODIFY_COMPONENT`, `CREATE_WIRE`, `MODIFY_WIRE`, `CREATE_NET_FLAG`, `CREATE_NET_PORT`, `CREATE_NET_LABEL`, `MODIFY_NET_LABEL`, `CREATE_TEXT`, `SAVE`.

Optional: library search, region read, rectangle, export/render, raw LCEDA API/script execution, auto-layout, auto-routing.

Record **actual tool + exact required arguments** mentally/in working notes. Do not expose invented aliases as callable tools; aliases are only reasoning labels.

## Probe read-only first

Validate the mapping with non-mutating calls against the current sheet where possible. If a capability is absent, mark it unavailable. Do not create a sacrificial component in a real design just to test a schema.

## Official API fallback

If the server exposes a generic LCEDA API/script bridge, use the official `eda.*` interface described in `references/lceda-api-reference.md`. Do not assume such a bridge exists.

## Mutation discipline

For every meaningful edit batch:

1. read the target objects/topology;
2. perform a small, homogeneous mutation;
3. re-read affected objects;
4. verify expected geometry/topology;
5. save only when the batch is coherent.

Treat `autoLayout` and `autoRouting` as **proposal generators**. Never run whole-sheet automation merely because it is available.

## Failure behavior

If a required capability is missing, stop only the unsupported step and state which semantic capability is absent. Prefer a partial safe result over fabricated tool usage.
