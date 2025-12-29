# 🎓 Project Okido: Semantic Japanese Correction Bot

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Gemini API](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange.svg)](https://ai.google.dev/)
[![Library](https://img.shields.io/badge/Lib-google--genai-green.svg)](https://pypi.org/project/google-genai/)

> **「正しい日本語、ゲットじゃぞ〜！」**
> 
> 本プロジェクトは、SNS上の日本語誤用（例：「そうゆう」→「そういう」）をリアルタイムで検知し、オーキド博士のキャラクター性を用いて教育的なフィードバックを自動送信するソーシャル・リスニング・エージェントです。

---

## 🔬 1. 設計思想 (Architectural Philosophy)

本システムは、単なる文字列置換Botではありません。以下の3つの柱に基づき設計されています。

1. **Semantic Consistency (文脈の整合性)**
   最新のLLM（Gemini 1.5 Flash）を活用。単なる添削ではなく「オーキド博士」というキャラクターを通じ、ポケモン世界のメタファーを用いた教育体験を提供します。
2. **Robust Filtering (堅牢な鑑定ロジック)**
   「ゆったん」「ゆったり」「こんにちわんこ」等の固有名詞・擬態語・遊びの挨拶を誤検知（False Positive）しないよう、多層的な除外フレーズ・フィルタリングを実装しています。
3. **Strategic Polling (戦略的調査リズム)**
   APIのレート制限を考慮し、1語句ずつの逐次検索、失敗時のインターバル（10秒）、成功後の休息（3分）といった、人間らしい探索アルゴリズムを採用しています。

---

## 🛠 2. 技術スタック (Tech Stack)

| カテゴリ | 採用技術 | 役割 |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | メインロジックの実装 |
| **AI Engine** | Google GenAI SDK (v1.0+) | 自然言語生成 (NLG) |
| **Social API** | X API v2 (Tweepy) | リプライ送信・スレッド管理 |
| **Search Engine** | RapidAPI (Twitter 135) | データマイニング / リアルタイム検索 |
| **Automation** | GitHub Actions | 定期実行 (Cron) & 送信履歴の永続化 |
| **Timezone** | Pytz (Asia/Tokyo) | 博士の生活リズム（活動時間）の制御 |

---

## 🧬 3. システム・アーキテクチャ (System Architecture)



本システムは以下のステートフローで動作します。

1. **Activator**: GitHub Actionsにより1時間おきにパトロールを開始。
2. **Scout**: 20種類以上の誤用キーワードからランダムに1つを選択し、X（旧Twitter）上をスキャン。
3. **Assessor (鑑定)**:
   - **重複チェック**: すでにリプライ済みのツイートを排除。
   - **コンテキスト解析**: ユーザー名や本文に除外フレーズが含まれていないか確認。
   - **セルフチェック**: 投稿者がすでに正しい日本語を併記している場合はスルー。
4. **GenAI Thinker**: Geminiが文脈を読み取り、博士の口調（「ワシ」「〜じゃぞい」）で添削文を生成。
5. **Action**: ターゲットへリプライを送信し、成果を `replied_tweets.txt` に記録。

---

## 🚀 4. セットアップ (Installation & Setup)

### プリレクイジット
- Python 3.9 以上
- X Developer Portal (API Key, Secret, Access Token, Bearer Token)
- Google AI Studio (Gemini API Key)
- RapidAPI (Twitter 135 API Key)

### インストール手順
1. リポジトリのクローン
   git clone https://github.com/yourusername/okido-bot-rep.git
   cd okido-bot-rep

2. 依存ライブラリのインストール
   pip install -r requirements.txt

3. 環境変数の設定 (.env)
   cp .env.example .env

### 環境変数 (.env) の設定内容
GEMINI_API_KEY=your_key
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_SECRET=your_secret
X_BEARER_TOKEN=your_token
RAPIDAPI_KEY=your_key

---

## 📊 5. 運用ログの読み方 (Observability)

博士の活動はターミナルおよびGitHubのアクションログで詳細に確認可能です。

- [待機]: パトロール開始前のランダムな準備時間。
- [鑑定回避]: 名前にキーワードが含まれるユーザー等を正しくスルーした記録。
- [思考]: Geminiが博士のセリフを生成しているプロセス。
- [APIエラー]: 通信障害やレート制限の具体的なステータスコード。

---

## 📜 6. 免責事項 (Disclaimer)

本プロジェクトはファン活動およびプログラミング学習の一環として開発されており、株式会社ポケモン、株式会社ゲームフリーク、その他公式企業とは一切関係ありません。日本語の美しさを広めるための、ユーモアを交えた教育的Botです。

---

Developed by Kanesawa Hiroki (Okido Lab Assistant)