読書メモをdiscordから追加できるdiscord botです

別でDBサーバを立てることで、このbot経由でdiscordからメモを編集・追加することができます

My Discord Bot
===============

This repository contains a small Discord bot written in Python that stores reading memos in a MySQL database.

Quick setup
-----------

1. Create and activate a virtual environment in the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # create this if needed: discord.py, mysql-connector-python
```

2. Set the Discord token in an environment file for systemd or export it in your shell:

- Environment file (recommended for systemd): create `/etc/default/discord-bot` and add:

```bash
DISCORD_BOT_TOKEN="your_bot_token_here"
```

- Or export in your shell (for manual runs):

```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
python bot.py
```

3. Example systemd service is provided as `discord-bot.service.example`. Copy it to `/etc/systemd/system/discord-bot.service`, adjust `User` and paths if needed, then enable and start:

```bash
sudo cp discord-bot.service.example /etc/systemd/system/discord-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now discord-bot.service
sudo journalctl -u discord-bot.service -f
```

Troubleshooting
---------------
- If the bot fails to start, check `journalctl -u discord-bot.service` for logs.
- Ensure `DISCORD_BOT_TOKEN` is set; the bot exits with code 1 if it's missing.
- Verify MySQL credentials in `bot.py` and that the database is reachable from the host.

Notes
-----
- Do not commit your token to version control. Keep it in an environment file or a secret manager.
- Consider using system users with limited permissions for running services.
