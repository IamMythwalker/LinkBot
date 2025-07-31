
import os
import asyncio
from config import *
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, ChatAdminRequired, RPCError
from database.database import set_approval_off, is_approval_off, add_admin, remove_admin, list_admins

@Client.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("ᴜsᴀɢᴇ: <code>/addadmin {user_id}</code>")
    user_id = int(message.command[1])
    success = await add_admin(user_id)
    if success:
        await message.reply_text(f"✅ ᴜsᴇʀ <code>{user_id}</code> ᴀᴅᴅᴇᴅ ᴀs ᴀᴅᴍɪɴ.")
    else:
        await message.reply_text(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴀᴅᴍɪɴ <code>{user_id}</code>.")

@Client.on_message(filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("ᴜsᴀɢᴇ: <code>/deladmin {user_id}</code>")
    user_id = int(message.command[1])
    success = await remove_admin(user_id)
    if success:
        await message.reply_text(f"✅ ᴜsᴇʀ <code>{user_id}</code> ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀᴅᴍɪɴs.")
    else:
        await message.reply_text(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ <code>{user_id}</code>.")

@Client.on_message(filters.command("admins") & filters.user(OWNER_ID))
async def list_admins_command(client, message: Message):
    admins = await list_admins()
    if not admins:
        return await message.reply_text("⚠️ ɴᴏ ᴀᴅᴍɪɴs ꜰᴏᴜɴᴅ.")
    text = "<b> ᴀᴅᴍɪɴ ᴜsᴇʀ ɪᴅs:</b>\n" + "\n".join([f"<code>{uid}</code>" for uid in admins])
    await message.reply_text(text)
