#!/usr/bin/env python3
"""
GitHub Actions 等で gemini-cli をヘッドレス実行し JSON を保存する。
事前: npm install -g @google/gemini-cli
認証: GEMINI_API_KEY または GOOGLE_API_KEY（Google AI Studio の API キー）
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def main() -> int:
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "gemini-out.json")
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("GEMINI_API_KEY または GOOGLE_API_KEY が必要です。", file=sys.stderr)
        return 1

    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        print("gemini コマンドが見つかりません。npm install -g @google/gemini-cli を実行してください。", file=sys.stderr)
        return 1

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite").strip() or "gemini-2.5-flash"
    topic = os.environ.get("NEWS_DIGEST_TOPIC", "").strip()
    prompt_cmd = f"/news-digest 「{topic}」" if topic else "/news-digest"

    cmd = [
        gemini_bin,
        "-p",
        prompt_cmd,
        "-y",
        "--output-format",
        "json",
        "-m",
        model,
    ]

    print(f"--- Configuration ---")
    print(f"Model: {model}")
    print(f"Topic: {topic or '(none)'}")
    print(f"Command: {' '.join(cmd)}")
    print(f"----------------------")

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    # Node.js / Gemini CLI の内部デバッグログを有効化（ネットワーク等の状態把握用）
    env.setdefault("DEBUG", "gemini:*,google:*")

    is_github = os.environ.get("GITHUB_ACTIONS") == "true"
    if is_github:
        print(f"::group::Gemini CLI Output")

    print(f"Gemini CLI 実行開始 (timeout=180s)...")
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, env=env, timeout=180)
        print(f"Gemini CLI 実行完了")
        if proc.stdout:
            print(proc.stdout)
    except subprocess.TimeoutExpired as e:
        if is_github:
            print(f"::error::Gemini CLI timed out after 180 seconds")
        print(f"Error: Gemini CLI timed out", file=sys.stderr)
        
        # タイムアウト時にバッファに残っていた出力（内部エラー等）を救出
        if e.stdout:
            print("\n--- Partial stdout before timeout ---", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        return 1

    if is_github:
        print(f"::endgroup::")

    out_path.write_text(proc.stdout, encoding="utf-8")

    if proc.returncode != 0:
        if is_github:
            print(f"::error::Gemini CLI failed with exit code {proc.returncode}")
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON 解析エラー: {e}\n---\n{proc.stdout[:2000]}", file=sys.stderr)
        return 1

    if data.get("error"):
        err_msg = json.dumps(data["error"], ensure_ascii=False, indent=2)
        if is_github:
            print(f"::error::Gemini API returned error: {data['error'].get('message', 'Unknown error')}")
        print(err_msg, file=sys.stderr)
        return 1

    response = (data.get("response") or "").strip()
    if not response:
        print("Gemini の response が空です。", file=sys.stderr)
        return 1

    digest_path = out_path.with_name("digest.txt")
    digest_path.write_text(response, encoding="utf-8")
    print(f"Wrote {out_path} and {digest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
