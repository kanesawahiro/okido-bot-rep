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
            print("  [!] RapidAPI制限中...")
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

# --- 4. 実行コアロジック ---
def start_patrol():
    print("\n" + "="*40)
    print("オーキド博士「まずは通信テストじゃ！」")
    
    # 【重要】まずはリプライではなく「普通の投稿」ができるかテスト
    try:
        test_text = f"日本語調査パトロール、通信テスト中じゃぞい！({time.strftime('%H:%M:%S')})"
        client.create_tweet(text=test_text)
        print("  【成功】普通の投稿（ツイート）が成功したぞい！通信は生きておる！")
    except Exception as e:
        print(f"  【致命的失敗】普通の投稿すら403エラーで弾かれたぞい。")
        print(f"  エラー詳細: {e}")
        print("\n  博士のアドバイス：Portalで『Read and Write』の権限を確認し、")
        print("  キーをRegenerate（再生成）してGitHubに設定し直すのじゃ！")
        return # テスト失敗ならここで終了

    print("\n  通信テスト合格！続いてパトロールを開始するぞい...")
    print("="*40)
    
    MAX_REPLIES_PER_RUN = 2
    replied_count = 0
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
            
            if any(k in text for k in ["botお断り", "通報", "ブロック"]): continue

            if wrong in text and right not in text:
                try:
                    msg = generate_okido_msg(user_name, wrong, right)
                    # リプライ実行
                    client.create_tweet(text=msg, in_reply_to_tweet_id=int(tweet_id))
                    
                    print(f"  【成功】{user_name}くんにリプライ完了！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    replied_count += 1
                    time.sleep(random.randint(60, 120)) # 間隔をあける

                except Exception as e:
                    print(f"  [!] リプライに失敗: {e}")
                    # リプライだけ失敗する場合は、APIプランの「リプライ制限」が濃厚
                    return 

    print("\n今回の全工程が終了じゃ！")

if __name__ == "__main__":
    start_patrol()
