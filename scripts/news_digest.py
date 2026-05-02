#!/usr/bin/env python3
"""
news-digest スキル（.gemini/skills/news-digest/SKILL.md）と同じ流れで:
  前日の日付 → 日英 Web 検索でニュース収集 → 整形 → Discord Webhook に投稿。
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import feedparser
from ddgs import DDGS

import discord_post

JST = ZoneInfo("Asia/Tokyo")


def yesterday_in_jst() -> date:
    """JST の「今日」の前日（スキル Step 1: 前日を特定）。"""
    jst_today = datetime.now(JST).date()
    return jst_today - timedelta(days=1)


def unique_by_url(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        u = (it.get("url") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(it)
        if len(out) >= limit:
            break
    return out


def ddg_news(query: str, max_results: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, region="wt-wt", safesearch="off", timelimit="w"):
                rows.append(
                    {
                        "title": r.get("title") or "",
                        "body": r.get("body") or "",
                        "url": r.get("url") or "",
                        "source": r.get("source") or "",
                    }
                )
                if len(rows) >= max_results:
                    break
    except Exception as e:
        print(f"[warn] DDG news failed for {query!r}: {e}", file=sys.stderr)
    return rows


# DDG がブロック・レート制限のときのフォールバック（主要英語 RSS）
RSS_FALLBACK_FEEDS = (
    "https://feeds.reuters.com/reuters/topNews",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
)


def rss_fallback(max_per_feed: int = 6, total_cap: int = 16) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for url in RSS_FALLBACK_FEEDS:
        try:
            parsed = feedparser.parse(url)
            for e in parsed.entries[:max_per_feed]:
                title = (getattr(e, "title", None) or "").strip()
                link = (getattr(e, "link", None) or "").strip()
                summary = (getattr(e, "summary", None) or getattr(e, "description", None) or "")
                if isinstance(summary, str):
                    summary = summary.strip()
                    if len(summary) > 400:
                        summary = summary[:397] + "…"
                if title and link:
                    out.append({"title": title, "body": summary, "url": link, "source": "RSS"})
                if len(out) >= total_cap:
                    return out
        except Exception as ex:
            print(f"[warn] RSS failed {url}: {ex}", file=sys.stderr)
    return out


def fetch_news(topic: str | None, day: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    y = day.year
    m = day.month
    d = day.day
    jp_date = f"{y}年{m}月{d}日"
    months_en = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    en_date = f"{months_en[m]} {d}, {y}"

    if topic:
        q_jp = f"{topic} {jp_date}"
        q_en = f"{topic} {en_date}"
    else:
        q_jp = f"世界主要ニュース {jp_date}"
        q_en = f"world news headlines {en_date}"

    jp_items = ddg_news(q_jp)
    en_items = ddg_news(q_en)
    if not jp_items and not en_items:
        fb = rss_fallback()
        return fb, []
    return jp_items, en_items


def build_message(
    topic: str | None,
    day: date,
    jp_items: list[dict[str, Any]],
    en_items: list[dict[str, Any]],
) -> str:
    jp_date_s = f"{day.year}年{day.month}月{day.day}日"
    title_topic = topic if topic else "本日の主要ニュース（国際）"

    merged = unique_by_url(jp_items + en_items, 24)
    main = merged[:5]

    lines: list[str] = [
        "提督、おはようございますわ♪ くまりんこ朝の情報をお届けしますね！",
        "",
        f"## {jp_date_s}の{title_topic}まとめ",
        "",
    ]

    if not main:
        lines.append("本日は大きな動きはありませんでしたわ（検索結果が取得できませんでした）。")
        lines.append("")
        lines.append("📰 ソース")
        lines.append("・（なし）")
        body = "\n".join(lines)
        return body

    for i, it in enumerate(main, start=1):
        head = (it.get("title") or "（無題）").strip()
        desc = (it.get("body") or "").strip()
        if len(desc) > 280:
            desc = desc[:277] + "…"
        lines.append(f"### 📌 {head}")
        lines.append(desc if desc else "（概要なし）")
        lines.append("")

    lines.append("📰 ソース")
    for it in merged[:8]:
        t = (it.get("title") or "").strip()
        u = (it.get("url") or "").strip()
        if u:
            lines.append(f"・[{t}]({u})")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="news-digest → Discord (Webhook)")
    p.add_argument(
        "topic",
        nargs="?",
        default=os.environ.get("NEWS_DIGEST_TOPIC", "").strip() or None,
        help="トピック（省略時は主要ニュース全般）",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Discord に送らず標準出力のみ",
    )
    args = p.parse_args()

    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not args.dry_run and not webhook:
        print("DISCORD_WEBHOOK_URL が未設定です。", file=sys.stderr)
        return 1

    day = yesterday_in_jst()
    jp_items, en_items = fetch_news(args.topic, day)
    msg = build_message(args.topic, day, jp_items, en_items)

    if args.dry_run:
        print(msg)
        return 0

    parsed = urlparse(webhook)
    if parsed.scheme not in ("https",) or "discord.com" not in (parsed.netloc or ""):
        print("DISCORD_WEBHOOK_URL が不正です（https://discord.com/api/webhooks/... を想定）。", file=sys.stderr)
        return 1

    discord_post.post_discord_webhook(webhook, msg)
    print("Posted to Discord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
