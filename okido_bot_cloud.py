import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg 

load_dotenv()

# --- 1. 認証設定 ---
client = tweepy.Client(
    bearer_token=os.getenv("X_BEARER_TOKEN"),
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

# --- 2. 外部検索エンジン ---
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
    except: return []

REPLIED_FILE = "replied_tweets.txt"
def load_replied_ids():
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r", encoding="utf-8") as f: return set(line.strip() for line in f)

def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a+", encoding="utf-8") as f: f.write(f"{tweet_id}\n")

# --- 4. パトロール実行（リプ専用・最大効率ver） ---
def start_patrol():
    MAX_REPLIES_PER_RUN = 2  # 1日上限17件に合わせ、1回2件まで
    replied_count = 0
    replied_ids = load_replied_ids()
    search_list = list(CORRECTION_RULES.items())
    random.shuffle(search_list)

    print("="*40 + "\nオーキド博士「リプ専用パトロール、開始じゃ！」\n" + "="*40)

    for wrong, right in search_list:
        if replied_count >= MAX_REPLIES_PER_RUN: break
        tweets = search_tweets_external(wrong)

        for tweet in tweets:
            if replied_count >= MAX_REPLIES_PER_RUN: break 
            
            # 各種IDやユーザー名の取得
            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids: continue
            if any(k in text for k in ["bot", "通報", "ブロック"]): continue

            if wrong in text and right not in text:
                try:
                    # 本文生成（ここでもしメッセージの先頭に @ユーザー名 がなければ、ここで強制追加する）
                    msg = generate_okido_msg(user_name, wrong, right)
                    if not msg.startswith(f"@{user_name}"):
                        msg = f"@{user_name} {msg}"
                    
                    # 【リプ専用の急所】
                    # 1. in_reply_to_tweet_id を指定
                    # 2. 本文の先頭が必ず @メンション で始まっていること
                    client.create_tweet(
                        text=msg,
                        in_reply_to_tweet_id=int(tweet_id)
                    )
                    
                    print(f"  【成功】{user_name}くんへリプライしたぞ！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1
                    
                    # スパム判定を避けるため、次のリプまでしっかり時間を空ける
                    time.sleep(random.randint(120, 240))

                except Exception as e:
                    print(f"  [!] リプライ失敗: {e}")
                    # これでも403が出るなら、あとは「鍵の再生成」しか道はないぞい！
                    return 

if __name__ == "__main__":
    start_patrol()
