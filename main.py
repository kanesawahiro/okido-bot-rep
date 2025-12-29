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
    """ログにタグと時間を付与して出力するぞい"""
    now = datetime.now(JST).strftime("%H:%M:%S")
    print(f"[{tag}][{now}] {msg}")

def countdown_sleep(seconds):
    """待機時間を秒数で表示するカウントダウン関数じゃ"""
    for i in range(seconds, 0, -1):
        print(f"\r[待機] あと {i} 秒...", end="")
        time.sleep(1)
    print("\r" + " " * 30 + "\r", end="") # 表示をクリアする

# ==========================================
# 2. API 接続設定
# ==========================================

# X API (Tweepy) の初期化
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

# Gemini API の初期化 (404対策のため標準構成)
try:
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

# 固有名詞や遊びの挨拶での誤検知を防ぐ除外リスト
EXCLUDE_LIST = ["ゆったん", "ゆったり", "こんにちわんこ", "こんばんわんこ"]

REPLIED_FILE = "replied_tweets.txt"
CATCHPHRASE = "みんなも正しい日本語、ゲットじゃぞ〜！"

# ==========================================
# 4. コア・ロジック
# ==========================================

def generate_okido_reply(user_name, error_word, correct_word):
    """AIが博士の口調で添削文を生成。失敗時はテンプレートを返却"""
    log("思考", f"@{user_name}くんへの言葉を生成中...")
    
    prompt = (
        f"あなたはポケットモンスターのオーキド博士です。 "
        f"@{user_name}さんが「{error_word}」という誤用をしていたので、"
        f"正しくは「{correct_word}」であることを、博士らしい優しく威厳のある口調で教えてあげてください。 "
        f"ポケモンに例えた表現を必ず含め、100文字以内で作成してください。 "
        f"最後に一行空けて、必ず「{CATCHPHRASE}」で締めてください。"
    )
    
    # AI試行 (404対策として短いモデル名を使用)
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest"]
    for m in models_to_try:
        try:
            response = client_ai.models.generate_content(model=m, contents=prompt)
            if response and response.text:
                log("AI成功", f"モデル {m} が覚醒したぞい！")
                return response.text.strip()
        except Exception as e:
            log("AIエラー", f"{m} 失敗: {e}")
            continue

    # 失敗時のフォールバック
    log("全滅回避", "研究ノートから最適な言葉を選出じゃ。")
    base_text = random.choice(TEMPLATES)
    reply_text = base_text.format(user_name=user_name, wrong=error_word, right=correct_word)
    return f"{reply_text}\n\n{CATCHPHRASE}"

def patrol():
    """戦略的パトロール実行関数"""
    # 1. 目標人数を2か3でランダムに決定
    target_count = random.choice([2, 3])
    
    # 2. 開始前のランダム待機 (10〜60秒)
    wait_pre = random.randint(10, 60)
    log("待機", f"パトロール開始前に {wait_pre} 秒間、様子を見るぞい...")
    countdown_sleep(wait_pre)
    
    log("パトロール", f"今回は目標 {target_count} 名の日本語を守りに行くぞい！")
    
    # 履歴の読み込み
    if not os.path.exists(REPLIED_FILE): open(REPLIED_FILE, "w").close()
    with open(REPLIED_FILE, "r") as f: replied_ids = f.read().splitlines()

    # キーワードのシャッフル
    kw_list = list(KEYWORDS_MAP.keys())
    random.shuffle(kw_list)

    success_count = 0
    for kw in kw_list:
        if success_count >= target_count:
            log("完了", f"目標の {target_count} 名を達成したぞい！帰還じゃ！")
            return

        log("調査", f"『{kw}』をスキャン中... (成果: {success_count}/{target_count})")
        
        url = "https://twitter135.p.rapidapi.com/Search/"
        headers = {"X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"), "X-RapidAPI-Host": "twitter135.p.rapidapi.com"}
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
                text = legacy.get('full_text', legacy.get('text', ''))
                u_name = item.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get('screen_name')
                
                if t_id in replied_ids or not u_name: continue
                if any(ex in text for ex in EXCLUDE_LIST) or any(ex in u_name for ex in EXCLUDE_LIST):
                    continue

                log("発見", f"ターゲット検知: @{u_name}")
                reply_text = generate_okido_reply(u_name, kw, KEYWORDS_MAP[kw])
                
                try:
                    # v2 APIでの送信
                    client_v2.create_tweet(text=reply_text, in_reply_to_tweet_id=int(t_id))
                    log("送信成功", f"@{u_name} くんへ指導を届けたぞい！")
                    
                    # 履歴に記録
                    success_count += 1
                    with open(REPLIED_FILE, "a") as f: f.write(f"{t_id}\n")
                    
                    if success_count < target_count:
                        # 成功後のランダム休息 (180〜300秒)
                        wait_success = random.randint(180, 300)
                        log("休息", f"成功のご褒美に {wait_success} 秒休むぞい。")
                        countdown_sleep(wait_success)
                        break # 次のキーワード調査へ
                    else:
                        return 
                except Exception as e:
                    log("送信失敗", f"理由: {e}")
                    continue

        except Exception as e:
            log("エラー", f"詳細: {e}")
            continue
        
        # 次のキーワードに行く前のランダムインターバル (10〜25秒)
        if success_count < target_count:
            wait_next = random.randint(10, 25)
            log("待機", f"次のキーワード調査まで {wait_next} 秒待機じゃ...")
            countdown_sleep(wait_next)

if __name__ == "__main__":
    patrol()
