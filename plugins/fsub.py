import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from bot import Bot
from config import OWNER_ID
from database.database import *
from helper_func import is_admin, is_owner_or_admin


async def generate_fsub_link(client: Bot, channel_id: int) -> str:
    """Generate appropriate FSub link based on mode"""
    mode = await get_fsub_mode(channel_id)
    
    try:
        if mode == "join":
            # Create direct join link
            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                member_limit=1,
                creates_join_request=False  # Explicitly disable join requests
            )
            return invite.invite_link
        else:
            # Create request link with admin approval
            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                creates_join_request=True  # Enable join requests
            )
            return invite.invite_link
    except Exception as e:
        print(f"Error creating {mode} link for channel {channel_id}: {e}")
        return None


async def verify_user_subscription(client: Bot, user_id: int, channel_id: int) -> bool:
    """Verify if user is subscribed to channel based on mode"""
    try:
        # Check if user is already a member
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                return True
        except UserNotParticipant:
            pass
            
        # Get the appropriate link based on channel mode
        mode = await get_fsub_mode(channel_id)
        fsub_link = await generate_fsub_link(client, channel_id)
        
        if not fsub_link:
            return False
            
        # Send the appropriate message based on mode
        if mode == "request":
            text = "📛 You need to request to join our channel first!"
            btn_text = "📨 Request to Join"
        else:
            text = "📛 You need to join our channel first!"
            btn_text = "✨ Join Channel"
            
        try:
            await client.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(btn_text, url=fsub_link)
                ]])
                )
        except Exception as e:
            print(f"Error sending FSub message: {e}")
            
        return False
        
    except Exception as e:
        print(f"FSub verification error: {e}")
        return False


@Bot.on_message(filters.command('fsub') & filters.private & is_owner_or_admin)
async def fsub_command(client: Bot, message: Message):
    """Manage FSub channels"""
    args = message.text.split()

    if len(args) < 2:
        buttons = [
            [InlineKeyboardButton("Add Channel", callback_data="fsub_add")],
            [InlineKeyboardButton("Remove Channel", callback_data="fsub_remove")],
            [InlineKeyboardButton("List Channels", callback_data="fsub_list")],
            [InlineKeyboardButton("Set Mode", callback_data="fsub_mode")],
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
                if bot_member.status not in [
                        ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
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
                mode = await get_fsub_mode(channel_id)
                response += f"• <b>{chat.title}</b> [<code>{channel_id}</code>] - Mode: <code>{mode}</code>\n"
            except BaseException:
                response += f"• <i>Unavailable Channel</i> [<code>{channel_id}</code>]\n"

        await message.reply_text(
            response,
            parse_mode=ParseMode.HTML
        )

    elif subcmd == "mode":
        await fsub_mode_command(client, message)

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
        buttons = [
            [
                InlineKeyboardButton("Back", callback_data="fsub_back"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]
        await callback_query.message.edit_text(
            "<b>Usage of /fsub add command:</b>\n\n"
            "<code>/fsub add channel_id</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/fsub add -100123456789</code>\n\n"
            "<b>Note:</b> The bot must be admin in the channel you're adding.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_remove":
        buttons = [
            [
                InlineKeyboardButton("Back", callback_data="fsub_back"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]
        await callback_query.message.edit_text(
            "<b>Usage of /fsub remove command:</b>\n\n"
            "<code>/fsub remove channel_id</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/fsub remove -100123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_list":
        buttons = [
            [
                InlineKeyboardButton("Back", callback_data="fsub_back"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]
        fsub_channels = await get_fsub_channels()

        if not fsub_channels:
            await callback_query.message.edit_text(
                "<b>No FSub channels configured.</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        response = "<b>📢 Force Subscription Channels:</b>\n\n"

        for channel_id in fsub_channels:
            try:
                chat = await client.get_chat(channel_id)
                mode = await get_fsub_mode(channel_id)
                response += f"• <b>{chat.title}</b> [<code>{channel_id}</code>] - Mode: <code>{mode}</code>\n"
            except BaseException:
                response += f"• <i>Unavailable Channel</i> [<code>{channel_id}</code>]\n"

        await callback_query.message.edit_text(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    elif data == "fsub_back":
        buttons = [
            [InlineKeyboardButton("Add Channel", callback_data="fsub_add")],
            [InlineKeyboardButton("Remove Channel", callback_data="fsub_remove")],
            [InlineKeyboardButton("List Channels", callback_data="fsub_list")],
            [InlineKeyboardButton("Set Mode", callback_data="fsub_mode")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
        await callback_query.message.edit_text(
            "<b>Force Subscription Management</b>\n\n"
            "Choose an option below:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    
    elif data == "fsub_mode":
        await fsub_mode_command(client, callback_query.message)


@Bot.on_chat_member_updated()
async def handle_chat_member_update(client: Bot, chat_member_updated):
    """Handle when a user leaves a channel"""
    if (chat_member_updated.old_chat_member and 
        chat_member_updated.old_chat_member.status == ChatMemberStatus.MEMBER and
        chat_member_updated.new_chat_member and
        chat_member_updated.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]):
        
        channel_id = chat_member_updated.chat.id
        user_id = chat_member_updated.from_user.id

        # Check if this is an FSub channel
        fsub_channels = await get_fsub_channels()
        if channel_id in fsub_channels:
            # You could add additional handling here if needed
            pass


# FSub Mode Configuration Handlers
@Bot.on_message(filters.command('fsubmode') & filters.private & is_owner_or_admin)
async def fsub_mode_command(client: Bot, message: Message):
    """Set FSub channel mode (join/request)"""
    fsub_channels = await get_fsub_channels()
    
    if not fsub_channels:
        await message.reply_text(
            "<b>No FSub channels configured. Add some channels first.</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    buttons = []
    for channel_id in fsub_channels:
        try:
            chat = await client.get_chat(channel_id)
            current_mode = await get_fsub_mode(channel_id)
            
            # Green dot for enabled mode, red for disabled
            mode_indicator = "🟢" if current_mode == "join" else "🔴"
            
            buttons.append([
                InlineKeyboardButton(
                    f"{chat.title} [{mode_indicator}]",
                    callback_data=f"fsubmode_select_{channel_id}"
                )
            ])
        except Exception:
            buttons.append([
                InlineKeyboardButton(
                    f"Channel {channel_id}",
                    callback_data=f"fsubmode_select_{channel_id}"
                )
            ])
    
    buttons.append([InlineKeyboardButton("Back", callback_data="fsub_back")])
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])
    
    await message.reply_text(
        "<b>FSub Channel Modes</b>\n\n"
        "Select a channel to configure its mode:\n"
        "🟢 = Join Mode\n"
        "🔴 = Request Mode",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex(r"^fsubmode_select_(-?\d+)$"))
async def fsub_mode_select_handler(client: Bot, callback_query: CallbackQuery):
    channel_id = int(callback_query.matches[0].group(1))
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID and not await is_admin(user_id):
        await callback_query.answer("You don't have permission to do this.", show_alert=True)
        return
    
    try:
        chat = await client.get_chat(channel_id)
        current_mode = await get_fsub_mode(channel_id)
        
        # Green dot for enabled mode, red for disabled
        join_ball = "🟢" if current_mode == "join" else "🔴"
        request_ball = "🟢" if current_mode == "request" else "🔴"
        
        buttons = [
            [
                InlineKeyboardButton(
                    f"Join {join_ball}", 
                    callback_data=f"fsubmode_set_{channel_id}_join"
                ),
                InlineKeyboardButton(
                    f"Request {request_ball}", 
                    callback_data=f"fsubmode_set_{channel_id}_request"
                )
            ],
            [
                InlineKeyboardButton("Back", callback_data="fsub_mode"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]
        
        await callback_query.message.edit_text(
            f"<b>Configure Mode for:</b> {chat.title}\n\n"
            f"<b>Current Mode:</b> <code>{current_mode}</code>\n\n"
            "Select the mode you want to set:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"<b>Error:</b> <code>{e}</code>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^fsubmode_set_(-?\d+)_(join|request)$"))
async def fsub_mode_set_handler(client: Bot, callback_query: CallbackQuery):
    channel_id = int(callback_query.matches[0].group(1))
    mode = callback_query.matches[0].group(2)
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID and not await is_admin(user_id):
        await callback_query.answer("You don't have permission to do this.", show_alert=True)
        return
    
    if mode == "request":
        # Create a test link to verify admin approval can be enabled
        try:
            test_link = await client.create_chat_invite_link(
                chat_id=channel_id,
                creates_join_request=True
            )
            # Revoke the test link immediately
            await client.revoke_chat_invite_link(channel_id, test_link.invite_link)
        except Exception as e:
            await callback_query.answer(
                "Failed to enable admin approval. Make sure bot has 'Invite Users via Link' permission!",
                show_alert=True
            )
            return
    
    success = await set_fsub_mode(channel_id, mode)
    if success:
        await callback_query.answer(f"Mode set to {mode}!", show_alert=False)
        # Refresh the mode selection menu
        await fsub_mode_select_handler(client, callback_query)
    else:
        await callback_query.answer("Failed to set mode!", show_alert=True)

@Bot.on_callback_query(filters.regex("^fsub_mode$"))
async def fsub_mode_back_handler(client: Bot, callback_query: CallbackQuery):
    await fsub_mode_command(client, callback_query.message)


@Bot.on_message(
    filters.private & 
    filters.create(lambda _, __, m: not m.text.startswith('/')) &
    ~filters.user(OWNER_ID)
)
async def handle_private_messages(client: Bot, message: Message):
    """Handle private messages and check FSub requirements"""
    user_id = message.from_user.id
    
    # Skip if message is from admin
    if await is_admin(user_id):
        return
        
    # Check FSub for all configured channels
    fsub_channels = await get_fsub_channels()
    for channel_id in fsub_channels:
        if not await verify_user_subscription(client, user_id, channel_id):
            # Stop processing if user hasn't subscribed
            await message.stop_propagation()
            return