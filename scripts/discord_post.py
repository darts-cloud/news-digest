#!/usr/bin/env python3
"""Discord Webhook に長文を分割投稿する（news_digest / CI 共通）。"""
from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

import requests

DISCORD_CONTENT_LIMIT = 1900


def post_discord_webhook(webhook_url: str, content: str) -> None:
    chunks: list[str] = []
    rest = content
    while rest:
        if len(rest) <= DISCORD_CONTENT_LIMIT:
            chunks.append(rest)
            break
        cut = rest.rfind("\n", 0, DISCORD_CONTENT_LIMIT)
        if cut == -1:
            cut = DISCORD_CONTENT_LIMIT
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()

    for part in chunks:
        r = requests.post(
            webhook_url,
            json={"content": part},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if not r.ok:
            raise RuntimeError(f"Discord webhook failed ({r.status_code}): {r.text[:500]}")


def main() -> int:
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        print("DISCORD_WEBHOOK_URL が未設定です。", file=sys.stderr)
        return 1
    parsed = urlparse(webhook)
    if parsed.scheme != "https" or "discord.com" not in (parsed.netloc or ""):
        print("DISCORD_WEBHOOK_URL が不正です。", file=sys.stderr)
        return 1

    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    if not content.strip():
        print("投稿する内容が空です。", file=sys.stderr)
        return 1

    post_discord_webhook(webhook, content)
    print("Posted to Discord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
