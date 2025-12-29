import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg 

# 環境変数のロード
load_dotenv()

# --- 1. X API 認証設定（403突破・ハイブリッド版） ---
# API v2 (一応残しておくが、今回はv1.1を優先するぞい)
client = tweepy.Client(
    bearer_token=os.getenv("X_BEARER_TOKEN"),
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

# API v1.1 (リプライ送信の成功率が極めて高い伝統的な方式じゃ)
auth = tweepy.OAuthHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET")
)
auth.set_access_token(
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)

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
        return response.json().get('timeline', []) if response.status_code == 200 else []
    except:
        return []

# --- 3. 履歴管理 ---
REPLIED_FILE = "replied_tweets.txt"
def load_replied_ids():
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r", encoding="utf-8") as f: 
        return set(line.strip() for line in f if line.strip())

def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a+", encoding="utf-8") as f:
        f.write(f"{tweet_id}\n")

# --- 4. パトロール実行 ---
def start_patrol():
    # テスト用に制限を解除したままにしておくぞい
    print("博士「ハイブリッド認証で、403の壁をぶち破りに行くぞい！」")

    MAX_REPLIES = random.randint(2, 3)
    replied_count = 0
    replied_ids = load_replied_ids()
    search_list = list(CORRECTION_RULES.items())
    random.shuffle(search_list)

    print(f"パトロール開始！今回の目標は{MAX_REPLIES}件じゃ！")

    for wrong, right in search_list:
        if replied_count >= MAX_REPLIES: break
        tweets = search_tweets_external(wrong)

        for tweet in tweets:
            if replied_count >= MAX_REPLIES: break 
            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids: continue
            if any(k in text for k in ["bot", "通報", "ブロック"]): continue

            if wrong in text and right not in text:
                try:
                    msg = generate_okido_msg(user_name, wrong, right)
                    
                    # --- ここが403回避の切り札「v1.1送信」じゃ！ ---
                    api.update_status(
                        status=msg, 
                        in_reply_to_status_id=tweet_id, 
                        auto_populate_reply_metadata=True
                    )
                    
                    print(f"   【成功】{user_name}くんへリプライ完了！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1
                    
                    time.sleep(10) 

                except tweepy.errors.Forbidden as e:
                    print(f"   [!] 403エラー：これでもダメか！理由: {e}")
                    return 
                except Exception as e:
                    print(f"   [!] エラー発生: {e}")
                    return 

    print("パトロール完了じゃ！")

if __name__ == "__main__":
    start_patrol()
