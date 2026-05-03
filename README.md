# ニュースダイジェスト

ニュースダイジェストを自動的に取得し、Discordに投稿するスキル。
このリポジトリでは、Gemini CLIのスキルとして使用している。

## 使用方法

GitHub Actions またはローカル環境から Gemini CLI を使用して実行します。


```bash
gemini -p "news-digest '[トピック]'"
```

### パラメータ指定方法

トピック（`NEWS_DIGEST_TOPIC`）には以下のルールが適用されます。

| 指定方法 | 挙動 | 例 |
| --- | --- | --- |
| カンマ区切り (`,`) | **OR検索**: いずれかの単語を含むニュースを取得 | `Claude,Gemini,OpenAI` |
| プラス連結 (`+`) | **AND検索**: すべての単語を含むニュースを取得 | `Claude+Release` |
| スペース | そのままの文字列として検索 | `Claude Code` |

- トピックを省略した場合は「本日の主要ニュース（国際情勢全般）」がまとめられます。
- 複数のキーワードを組み合わせる際は、シングルクォート等で囲って指定することを推奨します。

## 環境変数

| シークレット変数名 | 説明 |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | DiscordのWebhook URL |
| `GEMINI_API_KEY` | Google Gemini APIキー |

| 変数名 | 説明 |
| --- | --- |
| `GEMINI_MODEL` | Geminiモデル名 |

