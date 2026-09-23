#!/usr/bin/env python
"""Regenerate week5/docs/API.md from the live FastAPI /openapi.json.

Used by the `docs-sync` Warp Drive saved prompt. Stdlib only.

Usage:
    python warp-drive/scripts/gen_api_docs.py \
        --base-url http://127.0.0.1:8000 \
        --out docs/API.md \
        [--diff-against docs/API.md]  # diff before overwriting
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

ENVELOPE_NOTE = """\
> All JSON responses use the response envelope (TASK 7):
> success `{"ok": true, "data": ...}` / error `{"ok": false, "error": {"code", "message"}}`.
> The schema column below describes the **inner `data` payload**.
"""


def fetch_openapi(base_url: str) -> dict:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}/openapi.json", timeout=10) as r:
        return json.loads(r.read().decode())


def schema_ref_name(ref: str) -> str:
    return ref.split("/")[-1]


def fmt_schema(schema: dict | None) -> str:
    if schema is None:
        return "—"
    if "$ref" in schema:
        return f"`{schema_ref_name(schema['$ref'])}`"
    t = schema.get("type", "any")
    if t == "array":
        inner = fmt_schema(schema.get("items", {}))
        return f"array of {inner}"
    fmt = schema.get("format")
    return f"`{fmt or t}`"


def fmt_params(op: dict) -> str:
    rows = []
    for p in op.get("parameters", []):
        schema = p.get("schema", {})
        bits = [p["name"]]
        if p.get("required"):
            bits.append("*(required)*")
        if "default" in schema:
            bits.append(f"default `{schema['default']}`")
        if "enum" in schema:
            bits.append("one of " + ", ".join(f"`{v}`" for v in schema["enum"]))
        for bound in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
            if bound in schema:
                bits.append(f"{bound} `{schema[bound]}`")
        rows.append(" — ".join(bits))
    return "<br>".join(rows) if rows else "—"


def gen_md(openapi: dict) -> str:
    lines = [
        "# Week5 Backend API (auto-generated)",
        "",
        f"Generated from `/openapi.json` — title: {openapi.get('info', {}).get('title', '?')}.",
        "",
        ENVELOPE_NOTE,
        "| Method | Path | Query params | Request body | Response (`data`) |",
        "|---|---|---|---|---|",
    ]
    for path, methods in sorted(openapi.get("paths", {}).items()):
        for method, op in methods.items():
            if method == "parameters":
                continue
            body = op.get("requestBody", {}).get("content", {}).get("application/json", {})
            body_s = fmt_schema(body.get("schema")) if body else "—"
            resp = op.get("responses", {}).get("200") or op.get("responses", {}).get("201") or {}
            ok_schema = (
                resp.get("content", {}).get("application/json", {}).get("schema", {})
                if isinstance(resp, dict)
                else {}
            )
            lines.append(
                f"| `{method.upper()}` | `{path}` | {fmt_params(op)} | {body_s} | {fmt_schema(ok_schema)} |"
            )
    lines += [
        "",
        "## Schemas",
        "",
    ]
    for name in sorted(openapi.get("components", {}).get("schemas", {})):
        sch = openapi["components"]["schemas"][name]
        req = sch.get("required", [])
        lines.append(f"### {name}")
        lines.append("")
        for prop, ps in sch.get("properties", {}).items():
            mark = "*(required)*" if prop in req else ""
            lines.append(f"- `{prop}`: {fmt_schema(ps)} {mark}")
        lines.append("")
    lines.append("## Route changelog")
    lines.append("")
    lines.append("Route deltas are appended here by the docs-sync automation when routes change.")
    return "\n".join(lines) + "\n"


def extract_routes(md: str) -> set[str]:
    return {
        m.group(0)
        for m in re.finditer(r"\| `(GET|POST|PUT|DELETE|PATCH)` \| `[^`]+`", md)
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--out", default="docs/API.md")
    ap.add_argument("--diff-against", default=None, help="file to diff routes against (usually the same as --out)")
    args = ap.parse_args()

    spec = fetch_openapi(args.base_url)
    new_md = gen_md(spec)

    old_routes: set[str] = set()
    if args.diff_against:
        try:
            with open(args.diff_against, encoding="utf-8") as f:
                old_routes = extract_routes(f.read())
        except FileNotFoundError:
            pass

    new_routes = extract_routes(new_md)
    added = new_routes - old_routes
    removed = old_routes - new_routes

    if added or removed:
        print("Route delta detected:")
        for r in sorted(added):
            print(f"  + {r}")
        for r in sorted(removed):
            print(f"  - {r}")
        # stamp the delta into the changelog section
        delta_lines = []
        if added:
            delta_lines.append(f"- added: {', '.join(sorted(added))}")
        if removed:
            delta_lines.append(f"- removed: {', '.join(sorted(removed))}")
        marker = "Route deltas are appended here by the docs-sync automation when routes change."
        new_md = new_md.replace(marker, marker + "\n" + "\n".join(delta_lines))
    else:
        print("No route changes.")

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_md)
    print(f"Wrote {args.out} ({len(new_routes)} routes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
