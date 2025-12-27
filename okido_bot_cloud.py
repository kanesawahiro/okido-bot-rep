import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg 

load_dotenv()

# --- 認証設定 ---
client = tweepy.Client(
    bearer_token=os.getenv("X_BEARER_TOKEN"),
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

def search_tweets_external(query):
    url = "https://twitter-api45.p.rapidapi.com/search.php" 
    headers = {"x-rapidapi-key": os.getenv("RAPID_API_KEY"), "x-rapidapi-host": "twitter-api45.p.rapidapi.com"}
    params = {"query": f'"{query}" -filter:retweets', "search_mode": "live"}
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('timeline', []) if response.status_code == 200 else []
    except: return []

REPLIED_FILE = "replied_tweets.txt"
def load_replied_ids():
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r", encoding="utf-8") as f: return set(line.strip() for line in f)

def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a+", encoding="utf-8") as f: f.write(f"{tweet_id}\n")

# --- ステルスパトロール実行 ---
def start_patrol():
    # 1. 深夜休み（午前2時〜8時まではパトロールしない）
    current_hour = (time.localtime().tm_hour + 9) % 24 # GitHub ActionsはUTCなのでJSTに補正
    if 2 <= current_hour <= 7:
        print(f"博士「今は{current_hour}時...深夜じゃ。ワシもポケモンも眠る時間ぞい。」")
        return

    # 2. 起動のゆらぎ（最大15分の二度寝）
    wait_sec = random.randint(0, 900)
    print(f"博士「ふむ...あと{wait_sec}秒ほど準備してから出発するぞい。」")
    time.sleep(wait_sec)

    # 3. 1回の投稿数を2〜3件でランダムに
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
            if not tweet_id or tweet_id in replied_ids: continue

            try:
                msg = generate_okido_msg(user_name, wrong, right)
                client.create_tweet(text=msg, in_reply_to_tweet_id=int(tweet_id))
                print(f"  【成功】{user_name}くんに教えたぞ！")
                save_replied_id(tweet_id)
                replied_ids.add(tweet_id)
                replied_count += 1
                time.sleep(random.randint(150, 300)) # リプライ間隔も人間らしく
            except Exception as e:
                print(f"  [!] 失敗: {e}")
                return

if __name__ == "__main__":
    start_patrol()
