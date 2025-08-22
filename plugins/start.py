import asyncio
import base64
import time
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors import FloodWait, UserNotParticipant, InviteHashExpired
from config import START_PIC
from bot import Bot
from datetime import datetime, timedelta
from config import *
from database.database import *
from plugins.newpost import revoke_invite_after_5_minutes
from helper_func import *

user_banned_until = {}
cancel_lock = asyncio.Lock()
is_canceled = False
user_message_count = defaultdict(int)
last_message_time = {}


async def show_loading(message, text="ᴘʀᴏᴄᴇssɪɴɢ..."):
    """Show smooth loading animation"""
    loading_msg = await message.reply_text(
        f"<b><i>{text}</i></b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(0.8)
    return loading_msg


async def check_subscription_status(client: Bot, user_id: int, fsub_channels: list) -> tuple:
    """Check if user is subscribed to all FSub channels"""
    buttons = []
    unsubscribed_channels = []

    for channel_id in fsub_channels:
        try:
            chat = await client.get_chat(channel_id)
            mode = await get_fsub_mode(channel_id)
            try:
                member = await client.get_chat_member(channel_id, user_id)
                if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                    unsubscribed_channels.append((chat, mode))
            except UserNotParticipant:
                unsubscribed_channels.append((chat, mode))
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            continue

    if not unsubscribed_channels:
        return True, "", None

    message = "<blockquote><b>📢 ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ꜰɪʀsᴛ!</b></blockquote>\n\n"
    message += "<i>ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇsᴇ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴜsᴇ ᴍᴇ:</i>\n\n"

    for chat, mode in unsubscribed_channels:
        try:
            if mode == "join":
                # Create direct join link
                invite = await client.create_chat_invite_link(
                    chat_id=chat.id,
                    member_limit=1,
                    creates_join_request=False
                )
                invite_link = invite.invite_link
                btn_text = f"🔗 ᴊᴏɪɴ {chat.title}"
            else:
                # Create request link with admin approval
                invite = await client.create_chat_invite_link(
                    chat_id=chat.id,
                    creates_join_request=True
                )
                invite_link = invite.invite_link
                btn_text = f"📨 ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title}"
        except:
            invite_link = f"https://t.me/{chat.username}" if chat.username else f"Chat ID: {chat.id}"
            btn_text = f"🔗 ᴊᴏɪɴ {chat.title}"

        message += f"<b>•</b> <code>{chat.title}</code>\n"
        buttons.append([InlineKeyboardButton(btn_text, url=invite_link)])

    buttons.append([InlineKeyboardButton("✅ ɪ'ᴠᴇ ᴊᴏɪɴᴇᴅ", callback_data="check_sub")])

    return False, message, InlineKeyboardMarkup(buttons)


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id
    current_time = datetime.now()

    # Check FSub requirements
    fsub_channels = await get_fsub_channels()
    if fsub_channels:
        loading_msg = await show_loading(message, "ᴄʜᴇᴄᴋɪɴɢ sᴜʙsᴄʀɪᴘᴛɪᴏɴs...")
        is_subscribed, subscription_message, subscription_buttons = await check_subscription_status(client, user_id, fsub_channels)
        await loading_msg.delete()

        if not is_subscribed:
            return await message.reply_text(
                subscription_message,
                reply_markup=subscription_buttons,
                parse_mode=ParseMode.HTML
            )

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            is_request = base64_string.startswith("req_")

            if is_request:
                base64_string = base64_string[4:]
                channel_id = await get_channel_by_encoded_link2(base64_string)
            else:
                channel_id = await get_channel_by_encoded_link(base64_string)

            if not channel_id:
                return await message.reply_text(
                    "<blockquote><b>ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )

            # Check if this is a /genlink link
            original_link = await get_original_link(channel_id)
            if original_link:
                button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        "• ᴘʀᴏᴄᴇᴇᴅ ᴛᴏ ʟɪɴᴋ •", url=original_link)]]
                )
                return await message.reply_text(
                    "<blockquote><b>ᴛʜɪs ɪs ʏᴏᴜʀ ʟɪɴᴋ !! ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴊᴏɪɴ 👇</b></blockquote>",
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )

            # Show loading while processing link
            wait_msg = await show_loading(message, "🔗 ɢᴇɴᴇʀᴀᴛɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...")

            # Revoke old link if exists
            old_link_info = await get_current_invite_link(channel_id)
            if old_link_info:
                try:
                    await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                    print(f"Revoked old link for channel {channel_id}")
                except Exception as e:
                    print(f"Failed to revoke old link: {e}")

            # Get FSub mode for this channel
            fsub_mode = await get_fsub_mode(channel_id)
            creates_join_request = fsub_mode == "request" or is_request

            # Generate new invite link with longer expiry
            try:
                invite = await client.create_chat_invite_link(
                    chat_id=channel_id,
                    expire_date=datetime.now() + timedelta(minutes=10),  # Increased to 10 minutes
                    creates_join_request=creates_join_request
                )

                await save_invite_link(channel_id, invite.invite_link, creates_join_request)
                await wait_msg.delete()

                button_text = "• ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ •" if creates_join_request else "• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •"
                button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(button_text, url=invite.invite_link)]])

                msg = await message.reply_text(
                    "<blockquote><b>ᴛʜɪs ɪs ʏᴏᴜʀ ʟɪɴᴋ !! ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴊᴏɪɴ 👇</b></blockquote>",
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )

                note_msg = await message.reply_text(
                    "<blockquote><i>⚠️ ɴᴏᴛᴇ: ɪꜰ ᴛʜᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴇxᴘɪʀᴇs, 🔁 ᴛᴀᴘ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ᴘᴏsᴛ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ᴀ ɴᴇᴡ ᴏɴᴇ.</i></blockquote>",
                    parse_mode=ParseMode.HTML
                )

                # Schedule cleanup
                asyncio.create_task(delete_after_delay(note_msg, 300))
                asyncio.create_task(
                    revoke_invite_after_5_minutes(
                        client,
                        channel_id,
                        invite.invite_link,
                        creates_join_request
                    )
                )

            except Exception as e:
                await wait_msg.delete()
                await message.reply_text(
                    "<blockquote><b>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
                print(f"Invite generation error: {e}")

        except InviteHashExpired:
            await message.reply_text(
                "<blockquote><b>⛔ ᴛʜɪs ʟɪɴᴋ ʜᴀs ᴇxᴘɪʀᴇᴅ. ᴘʟᴇᴀsᴇ ɢᴇᴛ ᴀ ɴᴇᴡ ᴏɴᴇ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await message.reply_text(
                "<blockquote><b>⚠️ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟs", callback_data="channels")],
                [InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]
            ]
        )

        try:
            await message.reply_photo(
                photo=START_PIC,
                caption=START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error sending start picture: {e}")
            await message.reply_text(
                START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )

# ugh man


@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()


@Bot.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id

    loading_msg = await callback_query.message.edit_text(
        "<b><i>🔎 ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ sᴜʙsᴄʀɪᴘᴛɪᴏɴs... ⏳ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.</i></b>",
        parse_mode=ParseMode.HTML
    )

    fsub_channels = await get_fsub_channels()
    if not fsub_channels:
        await loading_msg.edit_text(
            "<blockquote><b>⚠️ ɴᴏ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟs ᴄᴏɴꜰɪɢᴜʀᴇᴅ!</b></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return

    is_subscribed, subscription_message, subscription_buttons = await check_subscription_status(client, user_id, fsub_channels)
    await loading_msg.delete()

    if is_subscribed:
        await callback_query.message.edit_text(
            "<blockquote><b>✅ ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ! ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ.</b></blockquote>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback_query.message.edit_text(
            subscription_message,
            reply_markup=subscription_buttons,
            parse_mode=ParseMode.HTML
        )


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    if data == "close":
        await query.answer()
        await query.message.delete()

    elif data == "about":
        await query.answer()
        loading_msg = await query.message.edit_text(
            "<b><i>⏳ ʟᴏᴀᴅɪɴɢ...</i></b>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(0.8)

        user = await client.get_users(OWNER_ID)
        user_link = f"https://t.me/{
    user.username}" if user.username else f"tg://openmessage?user_id={OWNER_ID}"

        await loading_msg.edit_media(
            InputMediaPhoto(
                "https://envs.sh/Wdj.jpg",
                ABOUT_TXT
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'),
                 InlineKeyboardButton('ᴄʟᴏsᴇ •', callback_data='close')]
            ]),
        )

    elif data == "channels":
        await query.answer()
        loading_msg = await query.message.edit_text(
            "<b><i>⏳ ʟᴏᴀᴅɪɴɢ...</i></b>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(0.8) 

        user = await client.get_users(OWNER_ID)
        user_link = f"https://t.me/{
    user.username}" if user.username else f"tg://openmessage?user_id={OWNER_ID}"
        ownername = f"<a href={user_link}>{
    user.first_name}</a>" if user.first_name else f"<a href={user_link}>⚠️ ɴᴏ ɴᴀᴍᴇ !</a>"

        await loading_msg.edit_media(
            InputMediaPhoto("https://envs.sh/Wdj.jpg", CHANNELS_TXT),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʙᴀᴄᴋ', callback_data='start'),
                 InlineKeyboardButton('ʜᴏᴍᴇ•', callback_data='setting')]
            ]),
        )

    elif data in ["start", "home"]:
        await query.answer()
        loading_msg = await query.message.edit_text(
            "<b><i>📂 ʟᴏᴀᴅɪɴɢ ᴍᴀɪɴ ᴍᴇɴᴜ...</i></b>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(0.8)  

        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟs", callback_data="channels")],
                [InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]
            ]
        )

        try:
            await loading_msg.edit_media(
                InputMediaPhoto(START_PIC, START_MSG),
                reply_markup=inline_buttons
            )
        except Exception:
            await loading_msg.edit_text(
                START_MSG,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )


@Bot.on_message(filters.command('status') &
                filters.private & is_owner_or_admin)
async def info(client: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]])

    start_time = time.time()
    temp_msg = await message.reply("<b><i>⚙️ ᴘʀᴏᴄᴇssɪɴɢ...</i></b>", quote=True, parse_mode=ParseMode.HTML)
    end_time = time.time()

    ping_time = (end_time - start_time) * 1000

    users = await full_userbase()
    now = datetime.now()
    delta = now - client.uptime
    bottime = get_readable_time(delta.seconds)

    await temp_msg.edit(
        f"<blockquote><b>Users: {
    len(users)}\n\nUptime: {bottime}\n\nPing: {
        ping_time:.2f} ms</b></blockquote>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


@Bot.on_message(filters.command('broadcast') &
                filters.private & is_owner_or_admin)
async def send_text(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = False
    mode = False
    broad_mode = ''
    store = message.text.split()[1:]

    if store and len(store) == 1 and store[0] == 'silent':
        mode = True
        broad_mode = 'Silent '

    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = len(query)
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>📢 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴇssᴀɢᴇ... ⏳ ᴛʜɪs ᴡɪʟʟ ᴛᴀᴋᴇ sᴏᴍᴇ ᴛɪᴍᴇ.</i>", parse_mode=ParseMode.HTML)
        bar_length = 20
        final_progress_bar = "●" * bar_length
        complete_msg = f"🤖 {broad_mode} ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ✅"
        progress_bar = ''
        last_update_percentage = 0
        percent_complete = 0
        update_interval = 0.05

        for i, chat_id in enumerate(query, start=1):
            async with cancel_lock:
                if is_canceled:
                    final_progress_bar = progress_bar
                    complete_msg = f"🤖 {broad_mode} ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴀɴᴄᴇʟᴇᴅ ❌"
                    break
            try:
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1

            percent_complete = i / total

            if percent_complete - \
                last_update_percentage >= update_interval or last_update_percentage == 0:
                num_blocks = int(percent_complete * bar_length)
                progress_bar = "●" * num_blocks + \
                    "○" * (bar_length - num_blocks)

                status_update = f"""<blockquote><b>🤖 {broad_mode}📢 ʙʀᴏᴀᴅᴄᴀsᴛ ɪɴ ᴘʀᴏɢʀᴇss...</b></blockquote>

<b>📊 ᴘʀᴏɢʀᴇss:{progress_bar}] {percent_complete:.0%}

<b>👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> {total}
<b>✅ sᴜᴄᴄᴇssꜰᴜʟ:</b> {successful}
<b>🚫 ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> {blocked}
<b>🗑️ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:</b> {deleted}
<b>❌ ᴜɴsᴜᴄᴄᴇssꜰᴜʟ:</b> {unsuccessful}

<i>🛑 ᴛᴏ sᴛᴏᴘ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛ, ᴜsᴇ: /ᴄᴀɴᴄᴇʟ</i>"""
                await pls_wait.edit(status_update, parse_mode=ParseMode.HTML)
                last_update_percentage = percent_complete

        final_status = f"""<blockquote><b>✅ {complete_msg}</b></blockquote>

<b>📊 ᴘʀᴏɢʀᴇss:</b> [{final_progress_bar}] {percent_complete:.0%}

<b>👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs:</b> {total}
<b>✅ sᴜᴄᴄᴇssꜰᴜʟ:</b> {successful}
<b>🚫 ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs:</b> {blocked}
<b>🗑️ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs:</b> {deleted}
<b>❌ ᴜɴsᴜᴄᴄᴇssꜰᴜʟ:</b> {unsuccessful}"""
        return await pls_wait.edit(final_status, parse_mode=ParseMode.HTML)

    else:
        msg = await message.reply("<code>ℹ️ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs.</code>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(8)
        await msg.delete()