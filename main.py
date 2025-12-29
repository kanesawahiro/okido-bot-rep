import os
import time
import random
import requests
import tweepy
from datetime import datetime
import pytz
from dotenv import load_dotenv

# 最新のGenAIライブラリを使用 (google-genai v1.0+)
from google import genai
from messages import TEMPLATES

# ==========================================
# 1. 補助関数・環境設定
# ==========================================
load_dotenv()
JST = pytz.timezone('Asia/Tokyo')

def log(tag, msg):
    now = datetime.now(JST).strftime("%H:%M:%S")
    print(f"[{tag}][{now}] {msg}")

# ==========================================
# 2. API 接続設定 (Tweepy & Google GenAI)
# ==========================================

# X API (Tweepy)
try:
    auth = tweepy.OAuth1UserHandler(
        os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"),
        os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    log("初期化", "X API 接続完了。パトロールの準備は万端じゃ！")
except Exception as e:
    log("初期化エラー", f"X API: {e}")

# Gemini API (最新 Client 方式)
try:
    # 404エラー対策として、ライブラリの自動判別に任せる標準構成
    client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    log("初期化", "Gemini API 接続成功。博士の脳細胞が活性化しておるぞ！")
except Exception as e:
    log("初期化エラー", f"Gemini AI: {e}")

# ==========================================
# 3. 定数・検索設定
# ==========================================
KEYWORDS_MAP = {
    "そうゆう": "そういう", "そうゆー": "そういう", "そーゆー": "そういう",
    "こうゆう": "こういう", "こうゆー": "こういう", "こーゆー": "こういう",
    "どうゆう": "どういう", "どうゆー": "どういう", "どーゆー": "どういう",
    "ゆー通り": "いう通り", "ゆーとおり": "いう通り",
    "ゆった": "いった", "ゆってる": "いってる", "ゆーてる": "いってる",
    "こんにちわ": "こんにちは", "こんばんわ": "こんばんは"
}

# 固有名詞や遊びの挨拶での誤検知（False Positive）を防ぐための除外リスト
EXCLUDE_LIST = ["ゆったん", "ゆったり", "こんにちわんこ", "こんばんわんこ"]

REPLIED_FILE = "replied_tweets.txt"
CATCHPHRASE = "みんなも正しい日本語、ゲットじゃぞ〜！"

# ==========================================
# 4. コア・ロジック
# ==========================================

def generate_okido_reply(user_name, error_word, correct_word):
    """
    GenAI Thinker: 文脈を読み取り、オーキド博士の口調で添削文を生成。
    失敗時は Strategic Polling の一環としてテンプレートを返却。
    """
    log("思考", f"@{user_name}くんへの言葉を生成中...")
    
    prompt = (
        f"あなたはポケットモンスターのオーキド博士です。 "
        f"@{user_name}さんが「{error_word}」という誤用をしていたので、"
        f"正しくは「{correct_word}」であることを、博士らしい優しく威厳のある口調で教えてあげてください。 "
        f"ポケモンに例えた表現を必ず含め、100文字以内で作成してください。 "
        f"最後に一行空けて、必ず「{CATCHPHRASE}」という決め台詞で締めてください。"
    )
    
    # AI試行
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest"]
    for m in models_to_try:
        try:
            response = client_ai.models.generate_content(model=m, contents=prompt)
            if response and response.text:
                log("AI成功", f"モデル {m} が素晴らしい回答をくれたぞい！")
                return response.text.strip()
        except Exception as e:
            log("AIエラー", f"{m} で生成失敗: {e}")
            continue

    # 失敗時のフォールバック (Robustness)
    log("全滅回避", "研究ノート（テンプレート）から最適な言葉を選出じゃ。")
    base_text = random.choice(TEMPLATES)
    reply_text = base_text.format(user_name=user_name, wrong=error_word, right=correct_word)
    return f"{reply_text}\n\n{CATCHPHRASE}"

def patrol():
    """
    Scout & Assessor: X上をスキャンし、重複・文脈を鑑定した上で実行。
    """
    log("パトロール", "マサラタウンの平和（日本語の乱れ）を守りに行くぞい！")
    
    # 履歴の読み込み
    if not os.path.exists(REPLIED_FILE): open(REPLIED_FILE, "w").close()
    with open(REPLIED_FILE, "r") as f: replied_ids = f.read().splitlines()

    # キーワードの戦略的シャッフル
    kw_list = list(KEYWORDS_MAP.keys())
    random.shuffle(kw_list)

    for kw in kw_list:
        log("調査", f"『{kw}』の誤用がないかスキャン中...")
        
        # Twitter 135 (RapidAPI) 経由の検索
        url = "https://twitter135.p.rapidapi.com/Search/"
        headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "twitter135.p.rapidapi.com"
        }
        params = {"q": kw, "count": "10"}
        
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10).json()
            instructions = res.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
            
            entries = []
            for inst in instructions:
                if inst.get('type') == 'TimelineAddEntries':
                    entries = inst.get('entries', [])
                    break
            
            for entry in entries:
                item = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                legacy = item.get('legacy') or item.get('tweet', {}).get('result', {}).get('legacy', {})
                if not legacy: continue
                
                t_id = legacy['id_str']
                text = legacy['full_text'] if 'full_text' in legacy else legacy.get('text', '')
                u_info = item.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
                u_name = u_info.get('screen_name')
                
                # Assessor (鑑定) ロジック
                if t_id in replied_ids: continue
                if not u_name: continue
                
                # 除外フレーズのチェック (False Positive 回避)
                if any(ex in text for ex in EXCLUDE_LIST) or any(ex in u_name for ex in EXCLUDE_LIST):
                    log("鑑定回避", f"固有名詞/除外語を含むためスルーじゃ: @{u_name}")
                    continue

                log("発見", f"ターゲット検知: @{u_name}")
                reply_text = generate_okido_reply(u_name, kw, KEYWORDS_MAP[kw])
                
                print("-" * 50)
                log("最終送信文", f"\n{reply_text}")
                print("-" * 50)
                
                # Action (送信実行)
                try:
                    # v2 APIでの送信
                    client_v2.create_tweet(text=reply_text, in_reply_to_tweet_id=int(t_id))
                    log("送信成功", f"@{u_name} くんへ指導を届けたぞい！")
                except Exception as e:
                    log("v2エラー", f"理由: {e}")
                    try:
                        # v1.1 APIでのフォールバック
                        api_v1.update_status(status=reply_text, in_reply_to_status_id=t_id, auto_populate_reply_metadata=True)
                        log("送信成功", "v1.1でリプライ送信完了！")
                    except Exception as e2:
                        log("送信全滅", f"致命的エラー: {e2}")
                        return

                # 履歴に記録
                with open(REPLIED_FILE, "a") as f: f.write(f"{t_id}\n")
                
                # 戦略的休息 (Strategic Rhythm)
                log("休息", "3分間の休憩を挟んでから次へ行くぞい...")
                time.sleep(180)
                return 

        except Exception as e:
            log("エラー", f"ループ内で問題発生: {e}")
            continue
        
        # 1語句ごとの待機
        time.sleep(10)

if __name__ == "__main__":
    patrol()