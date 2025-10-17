import discord
import os
import sys
from load_dotenv import load_dotenv

# Discord Botのトークン
# .env の DISCORD_BOT_TOKEN を使う
load_dotenv('.env')

# Enable mock GPIO mode if not running on a Raspberry Pi or if specified via environment variable
USE_MOCK_GPIO = os.environ.get('USE_MOCK_GPIO', 'false').lower() == 'true' or not os.path.exists('/dev/gpiomem')

if USE_MOCK_GPIO:
    print("Running in GPIO mock mode (no hardware GPIO access)")
    
    # Create a mock MotionSensor class
    class MockMotionSensor:
        def __init__(self, pin):
            self.pin = pin
            self._motion_detected = False
            print(f"Mock motion sensor initialized on pin {pin}")
            
        @property
        def motion_detected(self):
            # This could be extended to simulate motion via commands
            return self._motion_detected
            
        def toggle_motion(self):
            self._motion_detected = not self._motion_detected
            return self._motion_detected
    
    # Use the mock sensor
    pir = MockMotionSensor(37)
else:
    try:
        from gpiozero import MotionSensor
        
        # 人感センサーを接続したGPIOピン番号
        PIR_PIN = 37

        # センサーの初期化
        pir = MotionSensor(PIR_PIN)
    except Exception as e:
        print(f"Error initializing GPIO: {e}")
        print("Try running with sudo or set USE_MOCK_GPIO=true environment variable")
        sys.exit(1)

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Discordボットのトークン（ご自身のものに置き換えてください）
if not DISCORD_TOKEN:
    print("環境変数 DISCORD_BOT_TOKEN が設定されていません。")
    sys.exit(1)

# Discordボットの接続準備
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """ボットがログインしたときに実行される処理"""
    print(f'{client.user}としてログインしました')

@client.event
async def on_message(message):
    """メッセージを受信したときに実行される処理"""
    # 自分のメッセージは無視
    if message.author == client.user:
        return

    # '/status' というメッセージに反応
    if message.content == '/status':
        if pir.motion_detected:
            await message.channel.send('✅ **部屋に人がいます**')
        else:
            await message.channel.send('❎ **部屋に人はいません**')
    
    # In mock mode, allow toggling the motion state with a command
    elif USE_MOCK_GPIO and message.content == '/toggle':
        if hasattr(pir, 'toggle_motion'):
            state = pir.toggle_motion()
            status = '✅ **部屋に人がいます**' if state else '❎ **部屋に人はいません**'
            await message.channel.send(f'Motion state toggled. Now: {status}')

# ボットを実行
client.run(DISCORD_TOKEN)
