import os
import time
import random
import requests
import datetime
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_okido_msg

load_dotenv()

# --- 1. X公式APIの設定 ---
client = tweepy.Client(
    bearer_token=os.getenv("X_BEARER_TOKEN"),
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

# --- 2. 外部APIの設定 ---
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
            print("  [!] RapidAPIの制限に達したようじゃ。調査を一時中断するぞ。")
            return "LIMIT"
        if response.status_code != 200:
            return []
        return response.json().get('timeline', [])
    except Exception as e:
        print(f"  [!] 検索エラー: {e}")
        return []

# --- 3. 記憶管理 ---
REPLIED_FILE = "replied_tweets.txt"
def load_replied_ids():
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r") as f: return set(f.read().splitlines())
def save_replied_id(tweet_id):
    with open(REPLIED_FILE, "a+") as f: f.write(f"{tweet_id}\n")

# --- 4. パトロール実行 ---
def start_patrol():
    print("\n" + "="*40)
    print("オーキド博士「クラウド日本語調査パトロール、出発じゃ！」")
    print("="*40)
    replied_ids = load_replied_ids()

    search_list = list(CORRECTION_RULES.items())
    random.shuffle(search_list)

    for wrong, right in search_list:
        print(f"\n『{wrong}』を調査中...")
        tweets = search_tweets_external(wrong)
        
        if tweets == "LIMIT": break

        count = 0 
        for tweet in tweets:
            if count >= 3: 
                break

            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str') or tweet.get('id'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids:
                continue
            
            if wrong in text:
                if right in text:
                    print(f"  [スキップ] {user_name}くんは既に正解（{right}）も書いているようじゃな。")
                    continue

                try:
                    msg = generate_okido_msg(user_name, wrong, right)
                    client.create_tweet(text=msg, in_reply_to_tweet_id=tweet_id)
                    
                    print(f"  【成功】{user_name}くんに教えたぞ！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    count += 1

                    # クラウド環境では動作時間に制限があるため、休憩を少し短く（1分〜3分）するぞい
                    interval = random.randint(60, 180)
                    print(f"  [待機] 門番に見つからぬよう、{interval}秒休むぞい...")
                    time.sleep(interval)

                except Exception as e:
                    if "429" in str(e):
                        print("  [🚨] X側の速度制限を検知した！今回の調査は打ち切りじゃ。")
                        return 
                    print(f"  [!] 送信失敗: {e}")
                    time.sleep(10)

    print("\n" + "-"*40)
    print("今回のパトロールは終了じゃ！また次回の予約時間に会おうぞ！")

# --- 5. メイン（クラウド実行用） ---
if __name__ == "__main__":
    # クラウド（GitHub Actions）がこのファイルを呼び出すと、
    # 1回だけパトロールを実行して、すぐに終了するようになっているぞ。
    # 予約（8時・20時）はGitHub側の「cron設定」が担当するのじゃ！
    start_patrol()