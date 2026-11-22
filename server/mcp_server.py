"""Pure-Python MCP App server for agy-hindsight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory_bank  # noqa: E402

APP_URI = "ui://agy-hindsight/app.html"
UI_DIR = Path(__file__).resolve().parent.parent / "ui"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "hindsight_open_ui",
        "title": "AGY 长期记忆",
        "description": "打开 AGY 长期记忆（Hindsight）面板，浏览项目知识页、检索跨会话记忆并索引历史会话。",
        "inputSchema": {"type": "object", "properties": {}},
        "_meta": {
            "ui": {"resourceUri": APP_URI},
            "com.google.antigravity/ui": {
                "entrypoints": [
                    {"type": "aux_pane", "title": "长期记忆"},
                ]
            },
        },
    },
    {
        "name": "hindsight_list_pages",
        "title": "列出知识页",
        "description": "列出记忆库中的项目知识页，可按 project 与 category 过滤。",
        "inputSchema": {
            "type": "object",
            "properties": {"project": {"type": "string"}, "category": {"type": "string"}},
        },
    },
    {
        "name": "hindsight_search_pages",
        "title": "检索知识页",
        "description": "按关键词检索项目架构、约定与历史决策知识页。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "project": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "hindsight_read_page",
        "title": "读取知识页详情",
        "description": "按 page_id 读取完整的知识页正文。",
        "inputSchema": {
            "type": "object",
            "properties": {"page_id": {"type": "string"}},
            "required": ["page_id"],
        },
    },
    {
        "name": "hindsight_ingest_document",
        "title": "写入/更新知识页",
        "description": "将项目文档、架构规范或关键决策写入/更新到 Hindsight 知识页。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string", "enum": ["architecture", "conventions", "decisions", "initiatives"]},
                "project": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "page_id": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "hindsight_capture_initiative",
        "title": "记录项目决策与进行中事项",
        "description": "快速将当前敲定的项目规则、纠偏经验或进行中事项沉淀为长期记忆。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "project": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "hindsight_recall",
        "title": "跨会话记忆召回",
        "description": "按关键词同时检索知识页与已索引的 Antigravity 历史对话记忆。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
        "_meta": {"ui": {"resourceUri": APP_URI}},
    },
    {
        "name": "hindsight_ingest_conversations",
        "title": "索引本地历史会话",
        "description": "扫描 ~/.gemini/antigravity/brain 下的历史会话日志并索引到长期记忆库。",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "最多扫描最近 N 个会话，默认 20"}},
        },
    },
]


def load_app_html() -> str:
    html = (UI_DIR / "app.html").read_text(encoding="utf-8")
    sdk = (UI_DIR / "ext-apps.js").read_text(encoding="utf-8")
    idx = sdk.rfind("export{")
    if idx != -1:
        sdk = (
            sdk[:idx]
            + "return { App: oc, applyDocumentTheme: uc, applyHostStyleVariables: tc, applyHostFonts: gc, getDocumentTheme: $c };"
        )
    wrapped = f"const {{ App, applyDocumentTheme, applyHostStyleVariables }} = (() => {{\n{sdk}\n}})();"
    return html.replace("/*__EXT_APPS_SDK__*/", wrapped, 1)


def handle_tool_call(bank: memory_bank.MemoryBank, name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "hindsight_open_ui":
        s = bank.summary()
        return {
            "content": [{"type": "text", "text": f"AGY 长期记忆库：{s['page_count']} 个知识页，{s['memory_count']} 条会话记忆。"}],
            "structuredContent": {"summary": s},
        }
    if name == "hindsight_list_pages":
        pages = bank.list_pages(args.get("project"), args.get("category"))
        return {"content": [{"type": "text", "text": json.dumps(pages, ensure_ascii=False, indent=2)}], "structuredContent": {"pages": pages}}
    if name == "hindsight_search_pages":
        pages = bank.search_pages(str(args["query"]), args.get("project"), int(args.get("limit") or 20))
        return {"content": [{"type": "text", "text": json.dumps(pages, ensure_ascii=False, indent=2)}], "structuredContent": {"pages": pages}}
    if name == "hindsight_read_page":
        page = bank.read_page(str(args["page_id"]))
        if not page:
            return {"content": [{"type": "text", "text": "未找到该知识页"}], "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(page, ensure_ascii=False, indent=2)}], "structuredContent": {"page": page}}
    if name == "hindsight_ingest_document":
        p = bank.upsert_page(
            title=str(args["title"]),
            content=str(args["content"]),
            category=str(args.get("category") or "architecture"),
            project=str(args.get("project") or "default"),
            tags=args.get("tags"),
            page_id=args.get("page_id"),
        )
        return {"content": [{"type": "text", "text": f"已保存知识页 #{p['id']}「{p['title']}」"}], "structuredContent": {"page": p}}
    if name == "hindsight_capture_initiative":
        p = bank.upsert_page(
            title=str(args["title"]),
            content=str(args["content"]),
            category="initiatives",
            project=str(args.get("project") or "default"),
            tags=args.get("tags"),
        )
        return {"content": [{"type": "text", "text": f"已记录决策/事项 #{p['id']}「{p['title']}」"}], "structuredContent": {"page": p}}
    if name == "hindsight_recall":
        rec = bank.recall(str(args["query"]), int(args.get("limit") or 15))
        return {
            "content": [{"type": "text", "text": f"召回结果：{len(rec['pages'])} 个知识页，{len(rec['memories'])} 条历史会话记忆。\n" + json.dumps(rec, ensure_ascii=False, indent=2)[:4000]}],
            "structuredContent": {"recall": rec, "summary": bank.summary()},
        }
    if name == "hindsight_ingest_conversations":
        res = bank.ingest_conversations(int(args.get("limit") or 20))
        return {"content": [{"type": "text", "text": f"已扫描 {res['indexed_sessions']} 个新会话，新增 {res['added_memories']} 条记忆。"}], "structuredContent": res}

    return {"content": [{"type": "text", "text": f"未知工具: {name}"}], "isError": True}


def write_msg(payload: dict[str, Any]) -> None:
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    sys.stdout.buffer.write(line.encode("utf-8"))
    sys.stdout.buffer.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(Path.home() / ".gemini" / "antigravity" / "plugin_data" / "agy-hindsight"))
    cli_args, _ = parser.parse_known_args()
    bank = memory_bank.MemoryBank(Path(cli_args.data_dir))

    while True:
        raw = sys.stdin.buffer.readline()
        if not raw:
            break
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}
        if req_id is None:
            continue

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": params.get("protocolVersion") or "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "agy-hindsight", "version": "0.1.0"},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                result = handle_tool_call(bank, params.get("name", ""), params.get("arguments") or {})
            elif method == "resources/list":
                result = {
                    "resources": [
                        {
                            "uri": APP_URI,
                            "name": "AGY 长期记忆面板",
                            "mimeType": "text/html;profile=mcp-app",
                            "_meta": {"ui": {"prefersBorder": False}},
                        }
                    ]
                }
            elif method == "resources/read":
                if params.get("uri") != APP_URI:
                    write_msg({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Unknown resource"}})
                    continue
                result = {
                    "contents": [
                        {
                            "uri": APP_URI,
                            "mimeType": "text/html;profile=mcp-app",
                            "text": load_app_html(),
                            "_meta": {"ui": {"prefersBorder": False}},
                        }
                    ]
                }
            else:
                write_msg({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
                continue
            write_msg({"jsonrpc": "2.0", "id": req_id, "result": result})
        except Exception as exc:
            write_msg({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}})


if __name__ == "__main__":
    main()
