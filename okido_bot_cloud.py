import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg 

# 環境変数のロード
load_dotenv()

# --- 1. X API (v2) 認証設定 ---
client = tweepy.Client(
    bearer_token=os.getenv("X_BEARER_TOKEN"),
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

# --- 2. 外部検索エンジン（RapidAPI） ---
def search_tweets_external(query):
    url = "https://twitter-api45.p.rapidapi.com/search.php" 
    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "twitter-api45.p.rapidapi.com"
    }
    params = {"query": f'"{query}" -filter:retweets', "search_mode": "live"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            print("  [!] RapidAPI制限：一時中断じゃ。")
            return "LIMIT"
        return response.json().get('timeline', []) if response.status_code == 200 else []
    except Exception as e:
        print(f"  [!] 検索エラー: {e}")
        return []

# --- 3. 永続化管理 ---
REPLIED_FILE = "replied_tweets.txt"

def load_replied_ids():
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r", encoding="utf-8") as f: 
        return set(line.strip() for line in f if line.strip())

def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a+", encoding="utf-8") as f:
        f.write(f"{tweet_id}\n")

# --- 4. パトロール実行（最大効率ver） ---
def start_patrol():
    MAX_REPLIES_PER_RUN = 2  # 1回の実行で2件まで（1日8回×2=16件/日で制限内）
    replied_count = 0

    print("\n" + "="*40)
    print(f"オーキド博士「最大効率パトロール開始！目標:{MAX_REPLIES_PER_RUN}件」")
    print("="*40)
    
    replied_ids = load_replied_ids()
    search_list = list(CORRECTION_RULES.items())
    random.shuffle(search_list)

    for wrong, right in search_list:
        if replied_count >= MAX_REPLIES_PER_RUN: break

        print(f"\n『{wrong}』を調査中...")
        tweets = search_tweets_external(wrong)
        if tweets == "LIMIT": break

        for tweet in tweets:
            if replied_count >= MAX_REPLIES_PER_RUN: break 

            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids: continue
            
            # ボット嫌い・スパム等を回避
            ignore_keywords = ["botお断り", "通報", "ブロック", "スパム"]
            if any(k in text for k in ignore_keywords): continue

            if wrong in text and right not in text:
                try:
                    msg = generate_okido_msg(user_name, wrong, right)
                    # API v2のリプライ仕様に合わせ、IDを数値化
                    client.create_tweet(text=msg, in_reply_to_tweet_id=int(tweet_id))
                    
                    print(f"  【成功】{user_name}くんに教えたぞ！({replied_count + 1}件目)")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1

                    if replied_count < MAX_REPLIES_PER_RUN:
                        wait_time = random.randint(120, 300)
                        print(f"  [待機] スパム避けの休憩じゃ。{wait_time}秒待つぞい...")
                        time.sleep(wait_time)

                except Exception as e:
                    print(f"  [!] 403/429エラー等を検知。中断するぞい: {e}")
                    return 

    print("\n" + "-"*40)
    print("パトロール完了じゃ！")

if __name__ == "__main__":
    start_patrol()
