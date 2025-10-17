import os

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
# .env の DISCORD_BOT_TOKEN を使う
load_dotenv('.env')
