#!/usr/bin/env python3
"""
Gemini CLI ヘッドレス用プロンプト（.gemini/skills/news-digest/SKILL.md 準拠）。
環境変数: NEWS_DIGEST_TOPIC（省略可）
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def build_prompt() -> str:
    topic = os.environ.get("NEWS_DIGEST_TOPIC", "").strip()
    jst_today = datetime.now(JST).date()
    prev = jst_today - timedelta(days=1)
    y, m, d = prev.year, prev.month, prev.day
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
        title_topic = topic
        search_hint = (
            f'Web検索: 「{topic} {jp_date}」と「{topic} {en_date}」（英語）を両方使い、'
            "その日付前後の出来事を調べる。"
        )
    else:
        title_topic = "本日の主要ニュース（国際）"
        search_hint = (
            f'Web検索: 「世界主要ニュース {jp_date}」と「world news headlines {en_date}」を'
            "両方使う。"
        )

    return f"""あなたは news-digest スキルに従うアシスタントです。必ず Web 検索ツールで事実を確認してから書く。

【対象の「前日」（JST）】
- 日本語表記: {jp_date}
- 英語表記: {en_date}

【調査】
{search_hint}
日本語・英語のソースを両方参照すること。

【本文の要件】
- 主要な出来事を 3〜5 件。背景・今後の見通しが分かれば短く。
- ニュースが少ない日は「本日は大きな動きはありませんでしたわ」と正直に書く。
- 情報は正確に。📰 ソースに必ず [タイトル](URL) 形式で複数列挙（日英両方から）。

【出力フォーマット】（この Markdown 本文のみ。前置きや「了解しました」等は禁止）

提督、おはようございますわ♪ くまりんこ朝の情報をお届けしますね！

## {jp_date}の{title_topic}まとめ

### 📌 （見出し）
（本文）

（必要なら 📌 を繰り返す）

📰 ソース
・[記事タイトル](https://...)
・[記事タイトル](https://...)

三隈からの報告でしたわ。くまりんこ♪
"""


def main() -> int:
    sys.stdout.write(build_prompt())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
