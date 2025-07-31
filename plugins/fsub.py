import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from bot import Bot
from config import OWNER_ID
from database.database import *
from helper_func import is_admin, is_owner_or_admin

@Bot.on_message(filters.command('fsub') & filters.private & is_owner_or_admin)
async def fsub_command(client: Bot, message: Message):
    """Manage FSub channels"""
    args = message.text.split()
    
    if len(args) < 2:
        buttons = [
            [InlineKeyboardButton("Add Channel", callback_data="fsub_add")],
            [InlineKeyboardButton("Remove Channel", callback_data="fsub_remove")],
            [InlineKeyboardButton("List Channels", callback_data="fsub_list")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
        
        await message.reply_text(
            "<b>Force Subscription Management</b>\n\n"
            "Choose an option below:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return
    
    subcmd = args[1].lower()
    
    if subcmd == "add":
        if len(args) < 3:
            await message.reply_text(
                "<b>Usage:</b> <code>/fsub add channel_id</code>",
                parse_mode=ParseMode.HTML
            )
            return
            
        try:
            channel_id = int(args[2])
            chat = await client.get_chat(channel_id)
            
            if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                await message.reply_text(
                    "<b>❌ Only channels and supergroups can be added as FSub channels.</b>",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Check if bot is admin
            try:
                bot_member = await client.get_chat_member(channel_id, "me")
                if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    await message.reply_text(
                        "<b>❌ I must be admin in that channel to add it as FSub.</b>",
                        parse_mode=ParseMode.HTML
                    )
                    return
            except Exception as e:
                await message.reply_text(
                    f"<b>❌ Failed to check admin status: {e}</b>",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Add to database
            success = await add_fsub_channel(channel_id)
            if success:
                await message.reply_text(
                    f"<b>✅ Successfully added channel:</b>\n"
                    f"<b>Title:</b> {chat.title}\n"
                    f"<b>ID:</b> <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.reply_text(
                    "<b>❌ Failed to add channel to database.</b>",
                    parse_mode=ParseMode.HTML
                )
                
        except Exception as e:
            await message.reply_text(
                f"<b>❌ Error adding channel:</b>\n<code>{e}</code>",
                parse_mode=ParseMode.HTML
            )
            
    elif subcmd == "remove":
        if len(args) < 3:
            await message.reply_text(
                "<b>Usage:</b> <code>/fsub remove channel_id</code>",
                parse_mode=ParseMode.HTML
            )
            return
            
        try:
            channel_id = int(args[2])
            success = await remove_fsub_channel(channel_id)
            
            if success:
                await message.reply_text(
                    f"<b>✅ Successfully removed channel:</b> <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.reply_text(
                    f"<b>❌ Channel not found in FSub list:</b> <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML
                )
                
        except Exception as e:
            await message.reply_text(
                f"<b>❌ Error removing channel:</b>\n<code>{e}</code>",
                parse_mode=ParseMode.HTML
            )
            
    elif subcmd == "list":
        fsub_channels = await get_fsub_channels()
        
        if not fsub_channels:
            await message.reply_text(
                "<b>No FSub channels configured.</b>",
                parse_mode=ParseMode.HTML
            )
            return
            
        response = "<b>📢 Force Subscription Channels:</b>\n\n"
        
        for channel_id in fsub_channels:
            try:
                chat = await client.get_chat(channel_id)
                response += f"• <b>{chat.title}</b> [<code>{channel_id}</code>]\n"
            except:
                response += f"• <i>Unavailable Channel</i> [<code>{channel_id}</code>]\n"
                
        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML
        )
        
    else:
        await message.reply_text(
            "<b>Invalid subcommand. Use /fsub without arguments for menu.</b>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex("^fsub_"))
async def fsub_callback_handler(client: Bot, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID and not await is_admin(user_id):
        await callback_query.answer("You don't have permission to do this.", show_alert=True)
        return
        
    if data == "fsub_add":
        await callback_query.message.edit_text(
            "<b>To add a channel to FSub:</b>\n\n"
            "<code>/fsub add channel_id</code>\n\n"
            "Example:\n"
            "<code>/fsub add -100123456789</code>",
            parse_mode=ParseMode.HTML
        )
        
    elif data == "fsub_remove":
        await callback_query.message.edit_text(
            "<b>To remove a channel from FSub:</b>\n\n"
            "<code>/fsub remove channel_id</code>\n\n"
            "Example:\n"
            "<code>/fsub remove -100123456789</code>",
            parse_mode=ParseMode.HTML
        )
        
    elif data == "fsub_list":
        fsub_channels = await get_fsub_channels()
        
        if not fsub_channels:
            await callback_query.message.edit_text(
                "<b>No FSub channels configured.</b>",
                parse_mode=ParseMode.HTML
            )
            return
            
        response = "<b>📢 Force Subscription Channels:</b>\n\n"
        
        for channel_id in fsub_channels:
            try:
                chat = await client.get_chat(channel_id)
                response += f"• <b>{chat.title}</b> [<code>{channel_id}</code>]\n"
            except:
                response += f"• <i>Unavailable Channel</i> [<code>{channel_id}</code>]\n"
                
        await callback_query.message.edit_text(
            response,
            parse_mode=ParseMode.HTML
        )

@Bot.on_chat_member_updated()
async def handle_chat_member_update(client: Bot, chat_member_updated):
    """Handle when a user leaves a channel"""
    if chat_member_updated.old_chat_member and chat_member_updated.old_chat_member.status == ChatMemberStatus.MEMBER:
        if chat_member_updated.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
            channel_id = chat_member_updated.chat.id
            user_id = chat_member_updated.from_user.id
            
            # Check if this is an FSub channel
            fsub_channels = await get_fsub_channels()
            if channel_id in fsub_channels:
                # You could add additional handling here if needed
                pass