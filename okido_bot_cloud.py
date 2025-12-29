import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg 

# 環境変数のロード
load_dotenv()

# --- 1. X API 認証設定（API v2 専用） ---
# お主が画像で確認した「Read and write」権限を持つ新しいカギを使うぞい！
client = tweepy.Client(
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
    # 重複を避けるため、少し検索範囲を狭めて「ライブ」な投稿を狙うぞい
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
    print("博士「さあ、新しい体での初パトロール、出発じゃ！」")

    # 初動は慎重に、1〜2件を目標にするぞい
    MAX_REPLIES = 2
    replied_count = 0
    replied_ids = load_replied_ids()
    search_list = list(CORRECTION_RULES.items())
    random.shuffle(search_list)

    for wrong, right in search_list:
        if replied_count >= MAX_REPLIES: break
        tweets = search_tweets_external(wrong)

        for tweet in tweets:
            if replied_count >= MAX_REPLIES: break 
            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids: continue
            
            # ボットや通報を避ける防衛本能じゃ
            if any(k in text for k in ["bot", "通報", "ブロック"]): continue

            if wrong in text and right not in text:
                try:
                    msg = generate_okido_msg(user_name, wrong, right)
                    
                    # --- ここが API v2 でのリプライ送信じゃ！ ---
                    # in_reply_to_tweet_id を指定するのがポイントじゃぞ
                    client.create_tweet(
                        text=msg,
                        in_reply_to_tweet_id=tweet_id
                    )
                    
                    print(f"   【大成功】{user_name}くんへ正しい日本語を届けたぞい！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1
                    
                    # 連続投稿で怪しまれないよう、少し休むぞい
                    time.sleep(15) 

                except Exception as e:
                    print(f"   [!] エラー発生: {e}")
                    # 重複エラー(403)が出た場合は、次へ行くのじゃ
                    continue

    print("博士「今日のパトロールはここまでじゃ！また明日会おう！」")

if __name__ == "__main__":
    start_patrol()
