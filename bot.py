import discord
import mysql.connector
import os # セキュリティのためosモジュールを追記
import typing
from discord import app_commands
from load_dotenv import load_dotenv

# Discord Botのトークン
# .env の DISCORD_BOT_TOKEN を使う
load_dotenv('.env')

# .env からトークンを取得する
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
# 開発中にコマンドを即時反映させたいサーバーのID
GUILD_ID = int(os.getenv('GUILD_ID'))

if not TOKEN:
    print(
        '環境変数 DISCORD_BOT_TOKEN が設定されていません。\n'
        'プロジェクトルートに .env を作成し、次の形式でトークンを保存してください: \n'
        "DISCORD_BOT_TOKEN = 'your_token_here'\n"
        # 'または systemd の Environment/EnvironmentFile で設定してください。'
    )
    raise SystemExit(1)

if not GUILD_ID:
    print(
        '環境変数 GUILD_ID が設定されていません。\n'
        'プロジェクトルートに .env を作成し、次の形式でサーバーIDを保存してください: \n'
        "GUILD_ID = 'your_guild_id_here'\n"
    )
    raise SystemExit(1)

# MySQLデータベースの接続情報
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE')
}


# Botの接続に必要なオブジェクトを生成
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
    print('/ping - 動作確認用コマンド')
    print('/addbook <書籍タイトル> - 新しい本を登録')
    print('/addmemo <書籍ID> <メモ内容> - 読書メモを登録')
    print('/books - 登録されている本の一覧を表示')
    print('/memos <書籍ID> - 特定のIDの本のメモ一覧を表示')
    print('------')

    await tree.sync(guild=discord.Object(id=GUILD_ID))


@tree.command(name="ping", description="動作確認用コマンド", guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name="addbook", description="新しい本を登録", guild=discord.Object(id=GUILD_ID))
async def addbook(interaction: discord.Interaction, title: str):
    conn = get_db_connection()
    if not conn:
        await interaction.response.send_message("データベースに接続できませんでした。")
        return

    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title) VALUES (%s)", (title,))
    conn.commit()
    await interaction.response.send_message(f"書籍「{title}」を登録しました。 (ID: {cursor.lastrowid})")

@tree.command(name="addmemo", description="読書メモを登録", guild=discord.Object(id=GUILD_ID))
async def addmemo(interaction: discord.Interaction, book_id: int, memo: str):
    conn = get_db_connection()
    if not conn:
        await interaction.response.send_message("データベースに接続できませんでした。")
        return

    cursor = conn.cursor()
    cursor.execute("INSERT INTO memos (book_id, memo) VALUES (%s, %s)", (book_id, memo))
    conn.commit()
    await interaction.response.send_message(f"書籍ID:{book_id} に新しいメモを登録しました。")

@tree.command(name="books", description="登録されている本の一覧を表示", guild=discord.Object(id=GUILD_ID))
async def books(interaction: discord.Interaction):
    conn = get_db_connection()
    if not conn:
        await interaction.response.send_message("データベースに接続できませんでした。")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM books ORDER BY id")
    results = cursor.fetchall()
    if not results:
        await interaction.response.send_message("登録されている書籍はありません。")
    else:
        response = "**登録書籍一覧**\n```\n"
        for row in results:
            response += f"ID: {row[0]}, タイトル: {row[1]}\n"
        response += "```"
        await interaction.response.send_message(response)

@tree.command(name="memos", description="特定のIDの本のメモ一覧を表示", guild=discord.Object(id=GUILD_ID))
async def memos(interaction: discord.Interaction, book_id: int):
    conn = get_db_connection()
    if not conn:
        await interaction.response.send_message("データベースに接続できませんでした。")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT title FROM books WHERE id = %s", (book_id,))
    book_title = cursor.fetchone()

    if not book_title:
        await interaction.response.send_message(f"ID:{book_id} の書籍は見つかりませんでした。")
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
        await interaction.response.send_message(response)


# Botの起動
try:
    client.run(TOKEN)
except Exception as e:
    print(f"Botの起動に失敗しました: {e}")
