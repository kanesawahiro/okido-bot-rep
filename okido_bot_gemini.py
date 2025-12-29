import os
import time
import random
import requests
import tweepy
from datetime import datetime
import pytz
from dotenv import load_dotenv

# 最新のGenAIライブラリを使用
from google import genai
from messages import TEMPLATES

# ==========================================
# 1. 補助関数
# ==========================================
load_dotenv()
JST = pytz.timezone('Asia/Tokyo')

def log(tag, msg):
    now = datetime.now(JST).strftime("%H:%M:%S")
    print(f"[{now}][{tag}] {msg}")

# ==========================================
# 2. API 接続設定
# ==========================================

# X API 接続
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
    log("初期化", "X API 接続完了じゃ。")
except Exception as e:
    log("初期化エラー", f"X API: {e}")

# Gemini API 接続 (オプションを外し、ライブラリの自動判別に任せるぞい)
try:
    client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    log("初期化", "Gemini API 接続成功。AIの目覚めを待つぞい！")
except Exception as e:
    log("初期化エラー", f"Gemini: {e}")

# ==========================================
# 3. 定数
# ==========================================
KEYWORDS_MAP = {
    "そうゆう": "そういう", "そうゆー": "そういう", "そーゆー": "そういう",
    "こうゆう": "こういう", "こうゆー": "こういう", "こーゆー": "こういう",
    "どうゆう": "どういう", "どうゆー": "どういう", "どーゆー": "どういう",
    "ゆー通り": "いう通り", "ゆーとおり": "いう通り",
    "ゆった": "いった", "ゆってる": "いってる", "ゆーてる": "いってる",
    "こんにちわ": "こんにちは", "こんばんわ": "こんばんは"
}
REPLIED_FILE = "replied_tweets.txt"
CATCHPHRASE = "みんなも正しい日本語、ゲットじゃぞ〜！"

# ==========================================
# 4. ロジック
# ==========================================

def generate_okido_reply(user_name, error_word, correct_word):
    log("AI思考", f"@{user_name}くんへの言葉を生成中...")
    
    prompt = (
        f"あなたはポケットモンスターのオーキド博士です。 "
        f"@{user_name}さんが「{error_word}」という誤用をしていたので、"
        f"正しくは「{correct_word}」であることを、博士らしい優しく威厳のある口調で教えてあげてください。 "
        f"ポケモンに例えた表現を必ず含め、100文字以内で作成してください。 "
        f"最後に必ず一行空けてから「{CATCHPHRASE}」で締めなさい。"
    )
    
    # 複数の名前を試すが、新しいキーなら gemini-1.5-flash で通るはずじゃ！
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest"]
    
    for m in models:
        try:
            response = client_ai.models.generate_content(model=m, contents=prompt)
            if response and response.text:
                log("AI成功", f"モデル {m} が覚醒したぞい！")
                return response.text.strip()
        except Exception as e:
            log("AIエラー", f"モデル {m} 失敗: {e}")
            continue

    # AIが全滅した場合はテンプレート
    log("全滅回避", "研究ノート（テンプレート）から選ぶぞい。")
    base_text = random.choice(TEMPLATES)
    reply_text = base_text.format(user_name=user_name, wrong=error_word, right=correct_word)
    return f"{reply_text}\n\n{CATCHPHRASE}"

def patrol():
    log("パトロール", "開始じゃ！")
    if not os.path.exists(REPLIED_FILE): open(REPLIED_FILE, "w").close()
    with open(REPLIED_FILE, "r") as f: replied_ids = f.read().splitlines()

    kw_list = list(KEYWORDS_MAP.keys())
    random.shuffle(kw_list)

    for kw in kw_list:
        log("調査", f"キーワード『{kw}』を検索中...")
        url = "https://twitter135.p.rapidapi.com/Search/"
        headers = {"X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"), "X-RapidAPI-Host": "twitter135.p.rapidapi.com"}
        params = {"q": kw, "count": "5"}
        
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10).json()
            data = res.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
            entries = []
            for inst in data:
                if inst.get('type') == 'TimelineAddEntries':
                    entries = inst.get('entries', [])
                    break
            
            for entry in entries:
                item = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                legacy = item.get('legacy') or item.get('tweet', {}).get('result', {}).get('legacy', {})
                if not legacy: continue
                
                t_id = legacy['id_str']
                u_name = item.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get('screen_name')
                
                if t_id in replied_ids or not u_name: continue

                log("発見", f"ターゲット: @{u_name}")
                reply_text = generate_okido_reply(u_name, kw, KEYWORDS_MAP[kw])
                
                print("-" * 50)
                log("送信内容", f"\n{reply_text}")
                print("-" * 50)
                
                try:
                    client_v2.create_tweet(text=reply_text, in_reply_to_tweet_id=int(t_id))
                    log("成功", "送信完了じゃ！")
                except Exception as e:
                    log("送信失敗", f"理由: {e}")
                    try:
                        api_v1.update_status(status=reply_text, in_reply_to_status_id=t_id, auto_populate_reply_metadata=True)
                        log("成功", "v1.1で送信したぞい！")
                    except Exception as e2:
                        log("エラー", f"送信不可: {e2}")
                        return

                with open(REPLIED_FILE, "a") as f: f.write(f"{t_id}\n")
                return 
                
        except Exception:
            continue
        time.sleep(2)

if __name__ == "__main__":
    patrol()