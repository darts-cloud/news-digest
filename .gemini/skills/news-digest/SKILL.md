---
name: news-digest
description: 指定したトピックの前日ニュースをWebSearchで取得し、Discordチャンネルに日本語で投稿するスキル。毎朝の定期通知や手動実行に使用。引数でトピックを指定する。
origin: local
---

# ニュースダイジェスト通知

指定トピックの前日ニュースを調査してDiscordに投稿する。

## Usage

```
/news-digest [トピック]
```

例：
- `/news-digest イラン情勢`
- `/news-digest 米中貿易摩擦`
- `/news-digest 円ドル相場`
- `/news-digest AI規制`

引数なしの場合は「本日の主要ニュース」として国際情勢全般をまとめる。

## When to Activate

- ユーザーが「〇〇のニュースを通知して」「〇〇の最新情報を調べてDiscordに送って」と言ったとき
- スケジュールされた自動通知
- `/news-digest` コマンドが呼ばれたとき

## Workflow

### Step 1: 日付を確認
前日の日付を特定する（例：今日が4月10日なら前日は4月9日）。

### Step 2: ニュース検索（並列実行）

以下を**同時に**実行：

```
WebSearch: "[トピック] [前日の日付 例: 2026年4月9日]"
WebSearch: "[topic in English] [yesterday's date e.g. April 9 2026]"
```

トピックが指定されていない場合：
```
WebSearch: "世界主要ニュース [前日日付]"
WebSearch: "world news headlines [yesterday's date]"
```

### Step 3: 情報を整理

取得したニュースから以下を抽出：
- 主要な出来事（3〜5件）
- 背景・文脈（必要に応じて）
- 今後の見通し（わかる場合）

### Step 4: Discordに投稿

`run_shell_command` ツールを使って、`scripts/discord_post.py`スクリプトを実行し、標準入力からメッセージを渡す（`DISCORD_WEBHOOK_URL` が設定されていること）。

```bash
python scripts/discord_post.py <<EOF
提督、おはようございますわ♪ くまりんこ朝の情報をお届けしますね！

## [日付]の[トピック]まとめ

### 📌 [見出し1]
[内容]

### 📌 [見出し2]
[内容]

（続く場合は追加）

📰 ソース
・[タイトル](URL)
・[タイトル](URL)

三隈からの報告でしたわ。くまりんこ♪
EOF
```

## Notes

- ソースは日本語・英語両方から引用すること
- ニュースが少ない日は「本日は大きな動きはありませんでしたわ」と正直に伝える
- 情報は正確に
- URLは必ずソースとして列挙する
