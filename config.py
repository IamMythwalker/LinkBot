
import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler

# Recommended
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "22505271"))
API_HASH = os.environ.get("API_HASH", "c89a94fcfda4bc06524d0903977fc81e")

# Main
OWNER_ID = int(os.environ.get("OWNER_ID", "7562536848"))
PORT = os.environ.get("PORT", "8080")

# Database
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "linktest")

# Auto approve
CHAT_ID = [
    int(app_chat_id) if id_pattern.search(app_chat_id) else app_chat_id for app_chat_id in environ.get(
        'CHAT_ID',
        '').split()]  # dont change anything
TEXT = environ.get(
    "APPROVED_WELCOME_TEXT",
    "<b>{mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {title} ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.\n\\‣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @AnimeCrescent</b>")
APPROVED = environ.get("APPROVED_WELCOME", "on").lower()

# Default
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))
# --- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -

# Start pic
START_PIC_FILE_ID = "https://telegra.ph/file/b2fd85c2e657755974a38.jpg"
START_PIC = "https://telegra.ph/file/b2fd85c2e657755974a38.jpg"
# Messages
START_MSG = os.environ.get(
    "START_MESSAGE",
    """<b>👋 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀɴɪᴍᴇ ᴄʀᴇsᴄᴇɴᴛ'ꜱ ʟɪɴᴋ sʜᴀʀɪɴɢ ʙᴏᴛ!</b>\n
<blockquote><b>➤</b> ɪ ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ɢᴇᴛ ʟɪɴᴋs ᴏғ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ</blockquote>\n
<blockquote>🔹 ᴘʀᴏᴜᴅʟʏ ᴘᴏᴡᴇʀᴇᴅ ʙʏ <a href="https://t.me/AnimeCrescent">@AnimeCrescent</a></blockquote>\n
<blockquote>🔹 ᴍᴀɴᴀɢᴇᴅ ʙʏ <a href="https://t.me/ThatKlein">ᴅɪᴠɪɴᴇ</a></blockquote>"""
)
HELP = os.environ.get(
    "HELP_MESSAGE",
    """<b><blockquote expandable>
» ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ: <a href="https://t.me/AnimeCrescent">@ᴀɴɪᴍᴇᴄʀᴇsᴄᴇɴᴛ</a>\n
» ᴅᴇᴠᴇʟᴏᴘᴇʀ: <a href="https://t.me/ThatKlein">ᴅɪᴠɪɴᴇ</a>
</blockquote></b>"""
)
ABOUT = os.environ.get(
    "ABOUT_MESSAGE",
    """<b><blockquote expandable>
ᴛʜɪs ʙᴏᴛ ɪs ᴍᴀɴᴀɢᴇᴅ ʙʏ <a href="https://t.me/AnimeCrescent">ᴀɴɪᴍᴇ ᴄʀᴇsᴄᴇɴᴛ</a> ᴛᴏ sᴀғᴇʟʏ sʜᴀʀᴇ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋs ᴜsɪɴɢ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇs!
</blockquote></b>"""
)

ABOUT_TXT = """<b>›› ᴄᴏᴍᴍᴜɴɪᴛʏ: <a href='https://t.me/AnimeCrescent'>ᴀɴɪᴍᴇ ᴄʀᴇsᴄᴇɴᴛ</a>
<blockquote expandable>
›› ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/AnimeCrescent'>Cʟɪᴄᴋ ʜᴇʀᴇ</a>
›› ᴏᴡɴᴇʀ: <a href='https://t.me/ThatKlein'>ᴅɪᴠɪɴᴇ</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: <a href='https://t.me/ThatKlein'>ᴅɪᴠɪɴᴇ</a>
</b></blockquote>"""

CHANNELS_TXT = """<b>›› ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/AnimeCrescent'>ᴀɴɪᴍᴇ ᴄʀᴇsᴄᴇɴᴛ</a>
<blockquote expandable>
›› ᴜᴘᴅᴀᴛᴇs: <a href='https://t.me/redirectcrescent_updates'>ʀᴇᴅɪʀᴇᴄᴛ ᴄʀᴇsᴄᴇɴᴛ</a>
›› ʜ-ᴀɴɪᴍᴇ: <a href='https://t.me/culturedcrescent'>ᴄᴜʟᴛᴜʀᴇᴅ ᴄʀᴇsᴄᴇɴᴛ</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: <a href='https://t.me/ThatKlein'>ᴅɪᴠɪɴᴇ</a>
</b></blockquote>"""

# --- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -
# Default
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "👊 ʙᴀᴋᴀ! ɪ'ᴍ ʟᴏʏᴀʟ ᴛᴏ ᴍʏ ᴏᴡɴᴇʀs.\n» <a href='https://t.me/AnimeCrescent'>ᴀɴɪᴍᴇ ᴄʀᴇsᴄᴇɴᴛ</a>"

# Logging
LOG_FILE_NAME = "links-sharingbot.txt"
# Channel where user links are stored
DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL", "-1002805951723"))
# --- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -

try:
    ADMINS = []
    for x in (os.environ.get("ADMINS", "7562536848").split()):
        ADMINS.append(int(x))
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

# Admin == OWNER_ID
ADMINS.append(OWNER_ID)
ADMINS.append(7562536848)


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
