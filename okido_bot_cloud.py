import os
import tweepy
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# --- 1. X API 認証設定 (API v2 専用) ---
# お主が新アカウントで発行し、GitHubに登録したカギを使うぞい！
client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)

def start_test():
    print("博士「さあ、新しい体（アカウント）での第一声、届くかのう...？」")
    
    try:
        # リプライではなく、まずはシンプルな「新規投稿」を試すのじゃ！
        # これが通れば、Read/Write権限とカギは100%正しいことが証明されるぞい。
        status_text = "博士の日本語ラボ、これより開講じゃ！まずはテスト投稿、ゲットじゃぞ〜！"
        
        response = client.create_tweet(text=status_text)
        
        print("-" * 30)
        print(f"博士「成功じゃ！！投稿に成功したぞい！」")
        print(f"博士「投稿ID: {response.data['id']} が発行されたわい。」")
        print("-" * 30)
        print("博士「これが通ったということは、設定もカギも完璧ということじゃぞ！」")

    except tweepy.errors.Forbidden as e:
        print("-" * 30)
        print(f"博士「これでも 403 Forbidden か...。お主の設定は画像で見ても完璧じゃった。」")
        print(f"博士「となると、X側の反映遅延か、Freeプランの初期制限の可能性が高いわい。」")
        print(f"詳細理由: {e}")
        print("-" * 30)
        
    except Exception as e:
        print(f"博士「想定外のエラーが発生したぞい... 理由: {e}")

if __name__ == "__main__":
    start_test()
