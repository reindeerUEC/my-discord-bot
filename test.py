import mysql.connector
import os # セキュリティのためosモジュールを追記
import typing

def load_dotenv(path: str = '.env') -> None:
    """Load simple KEY = 'value' or KEY="value" pairs from a .env file into os.environ

    This is a minimal loader that ignores blank lines and comments. It will not
    overwrite existing environment variables (so shell/systemd env takes precedence).
    """
    if not os.path.exists(path):
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                # remove surrounding quotes if present
                if (val.startswith(('"', "'")) and val.endswith(('"', "'"))):
                    val = val[1:-1]
                # only set if not already provided by environment
                os.environ.setdefault(key, val)
    except Exception:
        # Don't crash on dotenv parse errors; caller will handle missing token later.
        pass

# Discord Botのトークン
# .env の DISCORD_BOT_TOKEN を使う（.env ファイルを優先的に読み込む）
load_dotenv('.env')

# .env からトークンを取得する
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    print(
        'プロジェクトルートに .env を作成し、次の形式でトークンを保存してください: \n'
        "DISCORD_BOT_TOKEN = 'your_token_here'\n"
    )
    raise SystemExit(1)

# 接続設定
config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE')
}

try:
    # 接続
    print("接続試行中...")
    conn = mysql.connector.connect(**config)
    
    # 接続成功
    print("接続成功!")
    
    # テーブル一覧
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    print("テーブル一覧:")
    for table in cursor:
        print(f"- {table[0]}")
    
    # テーブル構造
    cursor.execute("DESCRIBE books")
    print("\nbooks テーブル構造:")
    for column in cursor:
        print(f"- {column[0]}: {column[1]}")
    
    cursor.execute("DESCRIBE memos")
    print("\nmemos テーブル構造:")
    for column in cursor:
        print(f"- {column[0]}: {column[1]}")
    
    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"エラー: {err}")
