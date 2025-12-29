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

# --- 4. パトロール実行（究極のステルスver） ---
def start_patrol():
    # 【ライフリズム】日本時間の午前2時〜8時は活動休止（深夜休み）
    # GitHub ActionsはUTCなので、+9時間してJSTで判定
    current_hour_jst = (time.gmtime().tm_hour + 9) % 24
    if 2 <= current_hour_jst <= 7:
        print(f"博士「今は日本時間で{current_hour_jst}時...スヤスヤ...。調査は休みじゃ。」")
        return

    # 【起動のゆらぎ】開始前に最大15分（900秒）ランダム待機
    wait_before = random.randint(0, 900)
    print(f"博士「ふむ...あと{wait_before}秒ほど準備してから出発するぞい。」")
    time.sleep(wait_before)

    # 【件数のムラ】1回のリプライ数を2〜3件でランダムに決定
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
                    # リプライ専用・メンション付き
                    client.create_tweet(text=msg, in_reply_to_tweet_id=int(tweet_id))
                    
                    print(f"  【成功】{user_name}くんへリプライ完了！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1
                    
                    # リプライ間隔も3〜5分でランダムに
                    time.sleep(random.randint(180, 300))
                except Exception as e:
                    print(f"  [!] エラー発生: {e}")
                    return 

    print("パトロール完了じゃ！")

if __name__ == "__main__":
    start_patrol()
