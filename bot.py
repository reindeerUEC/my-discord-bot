import discord
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

# --- ▽▽▽ ご自身の環境に合わせて変更してください ▽▽▽ ---

# Discord Botのトークン
# 安全のため環境変数から読み込むことを推奨します
# .env の DISCORD_BOT_TOKEN を使う（.env ファイルを優先的に読み込む）
load_dotenv('.env')

# 環境変数または .env からトークンを取得する
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    print(
        '環境変数 DISCORD_BOT_TOKEN が設定されていません。\n'
        'プロジェクトルートに .env を作成し、次の形式でトークンを保存してください: \n'
        "DISCORD_BOT_TOKEN = 'your_token_here'\n"
        # 'または systemd の Environment/EnvironmentFile で設定してください。'
    )
    raise SystemExit(1)

# MySQLデータベースの接続情報
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE')
}

# --- △△△ ここまで △△△ ---

# Botの接続に必要なオブジェクトを生成
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# データベース接続を管理する関数
def get_db_connection():
    try:
        # デバッグ用: 接続設定を表示
        print("DB接続設定:")
        print(f"  user: {DB_CONFIG.get('user')}")
        print(f"  host: {DB_CONFIG.get('host')}")
        print(f"  database: {DB_CONFIG.get('database')}")
        
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"データベース接続エラー: {err}")
        return None

# 起動時にターミナルに表示される
@client.event
async def on_ready():
    print(f'{client.user} としてログインしました')
    print('------')
    print('コマンド一覧:')
    print('!help - このヘルプを表示')
    print('!addbook <書籍タイトル> - 新しい本を登録')
    print('!addmemo <書籍ID> <メモ内容> - 読書メモを登録')
    print('!books - 登録されている本の一覧を表示')
    print('!memos <書籍ID> - 特定のIDの本のメモ一覧を表示')
    print('------')

# メッセージ受信時に実行される処理
@client.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author == client.user:
        return

    # コマンドの解析
    if message.content.startswith('!'):
        command_parts = message.content.split(' ', 2)
        command = command_parts[0]

        conn = get_db_connection()
        if not conn:
            await message.channel.send("データベースに接続できませんでした。")
            return
        
        cursor = conn.cursor()

        try:
            # --- !help: ヘルプコマンド ---
            if command == '!help':
                help_text = (
                    "**読書メモBot コマンド一覧**\n"
                    "```\n"
                    "!help              - このヘルプを表示\n"
                    "!addbook <書籍名>  - 新しい本を登録\n"
                    "!addmemo <書籍ID> <メモ> - 読書メモを登録\n"
                    "!books             - 登録済みの本を一覧表示\n"
                    "!memos <書籍ID>    - 特定の本のメモを一覧表示\n"
                    "!ping              - 動作確認用コマンド\n"
                    "```"
                )
                await message.channel.send(help_text)

            # --- !addbook: 書籍の追加 ---
            elif command == '!addbook':
                if len(command_parts) < 2:
                    await message.channel.send("書籍のタイトルを指定してください。例: `!addbook 新しいPythonの本`")
                else:
                    title = command_parts[1]
                    cursor.execute("INSERT INTO books (title) VALUES (%s)", (title,))
                    conn.commit()
                    await message.channel.send(f"書籍「{title}」を登録しました。 (ID: {cursor.lastrowid})")

            # --- !addmemo: メモの追加 ---
            elif command == '!addmemo':
                if len(command_parts) < 3:
                    await message.channel.send("書籍IDとメモ内容を指定してください。例: `!addmemo 1 とても面白かった。`")
                else:
                    book_id = command_parts[1]
                    memo = command_parts[2]
                    cursor.execute("INSERT INTO memos (book_id, memo) VALUES (%s, %s)", (book_id, memo))
                    conn.commit()
                    await message.channel.send(f"書籍ID:{book_id} に新しいメモを登録しました。")
            
            # --- !books: 書籍一覧の表示 ---
            elif command == '!books':
                cursor.execute("SELECT id, title FROM books ORDER BY id")
                results = cursor.fetchall()
                if not results:
                    await message.channel.send("登録されている書籍はありません。")
                else:
                    response = "**登録書籍一覧**\n```\n"
                    for row in results:
                        response += f"ID: {row[0]}, タイトル: {row[1]}\n"
                    response += "```"
                    await message.channel.send(response)

            # --- !memos: メモ一覧の表示 ---
            elif command == '!memos':
                if len(command_parts) < 2:
                    await message.channel.send("書籍IDを指定してください。例: `!memos 1`")
                else:
                    book_id = command_parts[1]
                    cursor.execute("SELECT title FROM books WHERE id = %s", (book_id,))
                    book_title = cursor.fetchone()

                    if not book_title:
                        await message.channel.send(f"ID:{book_id} の書籍は見つかりませんでした。")
                    else:
                        cursor.execute("SELECT memo, created_at FROM memos WHERE book_id = %s ORDER BY id", (book_id,))
                        memos = cursor.fetchall()
                        response = f"**書籍「{book_title[0]}」のメモ一覧**\n"
                        if not memos:
                            response += "この書籍にはまだメモがありません。"
                        else:
                            response += "```\n"
                            for memo in memos:
                                response += f"- {memo[0]} ({memo[1].strftime('%Y-%m-%d')})\n"
                            response += "```"
                        await message.channel.send(response)

            # --- !ping: 動作確認用コマンド ---
            elif command == '!ping':
                await message.channel.send('pong')

        except mysql.connector.Error as err:
            await message.channel.send(f"データベースエラーが発生しました: {err}")
        finally:
            cursor.close()
            conn.close()

# Botの起動
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Botの起動に失敗しました: {e}")
