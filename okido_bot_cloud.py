import os
import time
import random
import requests
from dotenv import load_dotenv
import tweepy
from messages import CORRECTION_RULES, generate_stealth_msg 

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
    """RapidAPIを使用してXのタイムラインをリアルタイム検索。"""
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
        return response.json().get('timeline', []) if response.status_code == 200 else []
    except Exception as e:
        print(f"  [!] 検索エラー: {e}")
        return []

# --- 3. 永続化管理（送信履歴） ---
REPLIED_FILE = "replied_tweets.txt"

def load_replied_ids():
    """既読ポストIDの読み込み。二重送信防止用のキャッシュを生成。"""
    if not os.path.exists(REPLIED_FILE): return set()
    with open(REPLIED_FILE, "r", encoding="utf-8") as f: 
        return set(line.strip() for line in f if line.strip())

def save_replied_id(tweet_id):
    """リプライ済みのポストIDを履歴ファイルへ追記。"""
    with open(REPLIED_FILE, "a+", encoding="utf-8") as f:
        f.write(f"{tweet_id}\n")

# --- 4. パトロール実行コアロジック ---
def start_patrol():
    """
    パトロール実行メイン処理。
    Xのスパム検知回避（ステルス機能）とオーキド博士のログ出力を両立。
    """
    print("\n" + "="*40)
    print("オーキド「日本語調査パトロール、出発じゃ！」")
    print("="*40)
    
    replied_ids = load_replied_ids()
    search_list = list(CORRECTION_RULES.items())
    
    # 実行ごとのパターン固定化を避けるためランダム化
    random.shuffle(search_list)

    for wrong, right in search_list:
        print(f"\n『{wrong}』を調査中...")
        tweets = search_tweets_external(wrong)
        if tweets == "LIMIT": break

        count = 0 
        for tweet in tweets:
            # 1単語あたりの上限を3件に設定。
            if count >= 3: break 

            tweet_id = str(tweet.get('tweet_id') or tweet.get('id_str') or tweet.get('id'))
            user_name = tweet.get('screen_name') or tweet.get('user', {}).get('screen_name')
            text = tweet.get('text', '')

            if not tweet_id or not user_name or tweet_id in replied_ids:
                continue
            
            # 安全策：ボット拒否ユーザー等をフィルタリング
            ignore_keywords = ["botお断り", "通報", "スパム", "ブロック"]
            if any(k in text for k in ignore_keywords):
                print(f"  [スキップ] {user_name}くんはボットを好まないようじゃ。")
                continue

            # 誤用があり、かつ正解がまだ書かれていない場合のみ実行
            if wrong in text and right not in text:
                try:
                    # メッセージ動的生成：凍結リスク軽減
                    msg = generate_stealth_msg(user_name, wrong, right)
                    client.create_tweet(text=msg, in_reply_to_tweet_id=tweet_id)
                    
                    print(f"  【成功】{user_name}くんに教えたぞ！")
                    save_replied_id(tweet_id)
                    replied_ids.add(tweet_id)
                    count += 1

                    # 人間らしい操作をシミュレートするためのランダム待機（90秒〜300秒）
                    wait_time = random.randint(90, 300)
                    print(f"  [待機] 門番に見つからぬよう、{wait_time}秒休むぞい...")
                    time.sleep(wait_time)

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        print("  [🚨] X側の速度制限を検知した！今回の調査は打ち切りじゃ。")
                        return 
                    elif "403" in error_msg:
                        penalty = random.randint(600, 900)
                        print(f"  [!] 送信失敗: 403 Forbidden。{penalty}秒間、姿を隠すぞい...")
                        time.sleep(penalty)
                        break
                    else:
                        print(f"  [!] 送信失敗: {e}")
                        time.sleep(60)

    print("\n" + "-"*40)
    print("今回のパトロールは終了じゃ！また次回の予約時間に会おう！")

if __name__ == "__main__":
    start_patrol()
