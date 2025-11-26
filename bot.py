import asyncio
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from config import Config
from database import Database
from helpers import is_owner, is_admin_or_owner, check_force_sub, get_readable_time

Config.validate()

app = Client(
    "file_store_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

db = Database()
START_TIME = time.time()

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if await db.is_banned(user_id):
        await message.reply_text("❌ You are banned from using this bot.")
        return
    
    await db.add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    args = message.text.split(None, 1)
    
    if len(args) > 1:
        token = args[1]
        
        passed, markup = await check_force_sub(client, user_id)
        if not passed:
            await message.reply_text(
                "⚠️ You must join the following channels to use this bot:",
                reply_markup=markup
            )
            return
        
        file_data = await db.get_file_by_token(token)
        if file_data:
            try:
                forwarded = await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=file_data['channel_id'],
                    message_id=file_data['message_id']
                )
                
                delete_time = await db.get_setting('auto_delete_time', 0)
                if delete_time > 0:
                    asyncio.create_task(delete_message_after(forwarded, delete_time))
                
            except Exception as e:
                await message.reply_text(f"❌ Error retrieving file: {str(e)}")
            return
        
        batch_data = await db.get_batch_by_token(token)
        if batch_data:
            delete_time = await db.get_setting('auto_delete_time', 0)
            
            for msg_id in range(batch_data['first_msg_id'], batch_data['last_msg_id'] + 1):
                try:
                    forwarded = await client.copy_message(
                        chat_id=user_id,
                        from_chat_id=batch_data['channel_id'],
                        message_id=msg_id
                    )
                    
                    if delete_time > 0:
                        asyncio.create_task(delete_message_after(forwarded, delete_time))
                    
                    await asyncio.sleep(1)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    continue
            
            await message.reply_text("✅ Batch files sent successfully!")
            return
        
        await message.reply_text("❌ Invalid or expired link.")
        return
    
    is_admin = await is_admin_or_owner(user_id)
    
    welcome_text = f"**Hey {message.from_user.mention}!** 👋\n\n"
    welcome_text += "**Welcome to the File Store Bot!**\n\n"
    welcome_text += "I can store and share files securely. Use shared links to access your files.\n\n"
    
    if is_admin:
        welcome_text += "🔧 **Admin Commands:**\n"
        welcome_text += "`/genlink` - Generate link for a single post\n"
        welcome_text += "`/batch` - Generate batch link\n"
        welcome_text += "`/custom_batch` - Create custom batch\n"
        welcome_text += "`/broadcast` - Broadcast to all users\n"
        welcome_text += "`/stats` - Check bot statistics\n"
        welcome_text += "`/ban` `/unban` - User management\n"
        
        if user_id == Config.OWNER_ID:
            welcome_text += "\n👑 **Owner Commands:**\n"
            welcome_text += "`/add_admin` `/deladmin` - Admin management\n"
            welcome_text += "`/addchnl` `/delchnl` - Force subscribe\n"
            welcome_text += "`/fsub_mode` - Toggle force subscribe\n"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/Shivam_Dubber"),
            InlineKeyboardButton("📢 Updates", url="https://t.me/Shivam_Animes")
        ]
    ])
    
    try:
        await message.reply_photo(
            photo="welcome_image.png",
            caption=welcome_text,
            reply_markup=buttons
        )
    except Exception:
        await message.reply_text(welcome_text, reply_markup=buttons)
    
    try:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"#NewUser\n\n👤 User: {message.from_user.mention}\n🆔 ID: {user_id}\n📝 Username: @{message.from_user.username or 'None'}"
        )
    except:
        pass

async def delete_message_after(message: Message, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except:
        pass

@app.on_message(filters.command("genlink") & filters.private)
async def gen_link(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("❌ Please reply to a message to generate a link.")
        return
    
    try:
        forwarded = await reply.copy(Config.LOG_CHANNEL)
        
        token = await db.save_file(
            reply.id,
            reply.media.value if reply.media else 'text',
            forwarded.id,
            Config.LOG_CHANNEL,
            message.from_user.id
        )
        
        bot_username = (await client.get_me()).username
        link = f"https://t.me/{bot_username}?start={token}"
        
        await message.reply_text(
            f"✅ **Link Generated!**\n\n🔗 Link: {link}\n📋 Message ID: {forwarded.id}",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("batch") & filters.private)
async def batch_link(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.reply_text(
            "❌ Usage: /batch <first_message_id> <last_message_id>\n\n"
            "Example: /batch 100 150\n\n"
            "This will create a batch link for messages 100 to 150 from the log channel."
        )
        return
    
    try:
        first_id = int(args[1])
        last_id = int(args[2])
        
        if first_id > last_id:
            first_id, last_id = last_id, first_id
        
        token = await db.save_batch(
            first_id,
            last_id,
            Config.LOG_CHANNEL,
            message.from_user.id
        )
        
        bot_username = (await client.get_me()).username
        link = f"https://t.me/{bot_username}?start={token}"
        
        await message.reply_text(
            f"✅ **Batch Link Generated!**\n\n"
            f"🔗 Link: {link}\n"
            f"📊 Total Files: {last_id - first_id + 1}\n"
            f"📋 Range: {first_id} to {last_id}",
            disable_web_page_preview=True
        )
        
    except ValueError:
        await message.reply_text("❌ Invalid message IDs. Please provide valid numbers.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("custom_batch") & filters.private)
async def custom_batch(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.reply_text(
            "❌ Usage: /custom_batch <channel_id> <first_message_id> <last_message_id>\n\n"
            "Example: /custom_batch -1001234567890 100 150\n\n"
            "This will copy messages 100 to 150 from the specified channel to the log channel and create a batch link."
        )
        return
    
    try:
        channel_id = int(args[1])
        first_id = int(args[2])
        last_id = int(args[3])
        
        if first_id > last_id:
            first_id, last_id = last_id, first_id
        
        status_msg = await message.reply_text("⏳ Processing batch...")
        
        saved_first = None
        saved_last = None
        count = 0
        
        for msg_id in range(first_id, last_id + 1):
            try:
                msg = await client.get_messages(channel_id, msg_id)
                if msg and not msg.empty:
                    forwarded = await msg.copy(Config.LOG_CHANNEL)
                    
                    if saved_first is None:
                        saved_first = forwarded.id
                    saved_last = forwarded.id
                    count += 1
                    
                    await asyncio.sleep(1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                continue
        
        if saved_first and saved_last:
            token = await db.save_batch(
                saved_first,
                saved_last,
                Config.LOG_CHANNEL,
                message.from_user.id
            )
            
            bot_username = (await client.get_me()).username
            link = f"https://t.me/{bot_username}?start={token}"
            
            await status_msg.edit_text(
                f"✅ **Custom Batch Created!**\n\n"
                f"🔗 Link: {link}\n"
                f"📊 Total Files: {count}\n"
                f"📋 Range: {saved_first} to {saved_last}",
                disable_web_page_preview=True
            )
        else:
            await status_msg.edit_text("❌ No messages found in the specified range.")
        
    except ValueError:
        await message.reply_text("❌ Invalid input. Please provide valid numbers.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("users") & filters.private)
async def users_stats(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    total_users = await db.total_users_count()
    banned_users = len(await db.get_all_banned_users())
    
    stats_text = f"📊 **Bot Statistics**\n\n"
    stats_text += f"👥 Total Users: {total_users}\n"
    stats_text += f"🚫 Banned Users: {banned_users}\n"
    stats_text += f"✅ Active Users: {total_users - banned_users}"
    
    await message.reply_text(stats_text)

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("❌ Please reply to a message to broadcast.")
        return
    
    users = await db.get_all_users()
    status_msg = await message.reply_text("⏳ Broadcasting...")
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await reply.copy(user['user_id'])
            success += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            failed += 1
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📤 Sent: {success}\n"
        f"❌ Failed: {failed}"
    )

@app.on_message(filters.command("dbroadcast") & filters.private)
async def dbroadcast_message(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("❌ Please reply to a message to broadcast with auto-delete.")
        return
    
    delete_time = await db.get_setting('auto_delete_time', 300)
    
    users = await db.get_all_users()
    status_msg = await message.reply_text(f"⏳ Broadcasting with {delete_time}s auto-delete...")
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            sent_msg = await reply.copy(user['user_id'])
            asyncio.create_task(delete_message_after(sent_msg, delete_time))
            success += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            failed += 1
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📤 Sent: {success}\n"
        f"❌ Failed: {failed}\n"
        f"⏱️ Auto-delete: {delete_time}s"
    )

@app.on_message(filters.command("pbroadcast") & filters.private)
async def pin_broadcast(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("❌ Please reply to a message to pin broadcast.")
        return
    
    users = await db.get_all_users()
    status_msg = await message.reply_text("⏳ Broadcasting and pinning...")
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            sent_msg = await reply.copy(user['user_id'])
            await sent_msg.pin(disable_notification=True)
            success += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
            failed += 1
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Pin Broadcast Completed!**\n\n"
        f"📤 Sent & Pinned: {success}\n"
        f"❌ Failed: {failed}"
    )

@app.on_message(filters.command("stats") & filters.private)
async def bot_stats(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    uptime = get_readable_time(time.time() - START_TIME)
    total_users = await db.total_users_count()
    
    stats_text = f"📈 **Bot Statistics**\n\n"
    stats_text += f"⏱️ Uptime: {uptime}\n"
    stats_text += f"👥 Total Users: {total_users}\n"
    stats_text += f"🤖 Bot: Running"
    
    await message.reply_text(stats_text)

@app.on_message(filters.command("ban") & filters.private)
async def ban_user(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    args = message.text.split(None, 2)
    if len(args) < 2:
        await message.reply_text("❌ Usage: /ban <user_id> [reason]")
        return
    
    try:
        user_id = int(args[1])
        reason = args[2] if len(args) > 2 else "No reason provided"
        
        if user_id == Config.OWNER_ID:
            await message.reply_text("❌ Cannot ban the owner!")
            return
        
        if await is_admin_or_owner(user_id):
            await message.reply_text("❌ Cannot ban an admin!")
            return
        
        success = await db.ban_user(user_id, message.from_user.id, reason)
        
        if success:
            await message.reply_text(f"✅ User {user_id} has been banned.\n📝 Reason: {reason}")
        else:
            await message.reply_text("❌ User is already banned.")
    
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("unban") & filters.private)
async def unban_user(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Usage: /unban <user_id>")
        return
    
    try:
        user_id = int(args[1])
        success = await db.unban_user(user_id)
        
        if success:
            await message.reply_text(f"✅ User {user_id} has been unbanned.")
        else:
            await message.reply_text("❌ User is not banned.")
    
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("banlist") & filters.private)
async def ban_list(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    banned = await db.get_all_banned_users()
    
    if not banned:
        await message.reply_text("✅ No banned users.")
        return
    
    text = "🚫 **Banned Users:**\n\n"
    for user in banned:
        text += f"👤 User ID: {user['user_id']}\n"
        text += f"📝 Reason: {user.get('reason', 'N/A')}\n"
        text += f"📅 Banned: {user['banned_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
    
    await message.reply_text(text)

@app.on_message(filters.command("dlt_time") & filters.private)
async def set_delete_time(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Usage: /dlt_time <seconds>\n\nExample: /dlt_time 300 (for 5 minutes)")
        return
    
    try:
        seconds = int(args[1])
        if seconds < 0:
            await message.reply_text("❌ Time must be a positive number.")
            return
        
        await db.set_setting('auto_delete_time', seconds)
        
        if seconds == 0:
            await message.reply_text("✅ Auto-delete disabled.")
        else:
            await message.reply_text(f"✅ Auto-delete time set to {get_readable_time(seconds)}")
    
    except ValueError:
        await message.reply_text("❌ Invalid number. Please provide seconds as a number.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("check_dlt_time") & filters.private)
async def check_delete_time(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    delete_time = await db.get_setting('auto_delete_time', 0)
    
    if delete_time == 0:
        await message.reply_text("⏱️ Auto-delete is currently **disabled**.")
    else:
        await message.reply_text(f"⏱️ Current auto-delete time: **{get_readable_time(delete_time)}**")

@app.on_message(filters.command("add_admin") & filters.private)
async def add_admin(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Usage: /add_admin <user_id>")
        return
    
    try:
        user_id = int(args[1])
        
        if user_id == Config.OWNER_ID:
            await message.reply_text("❌ Owner is already the supreme admin!")
            return
        
        success = await db.add_admin(user_id)
        
        if success:
            await message.reply_text(f"✅ User {user_id} has been added as admin.")
        else:
            await message.reply_text("❌ User is already an admin.")
    
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("deladmin") & filters.private)
async def del_admin(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Usage: /deladmin <user_id>")
        return
    
    try:
        user_id = int(args[1])
        
        if user_id == Config.OWNER_ID:
            await message.reply_text("❌ Cannot remove owner from admin list!")
            return
        
        success = await db.remove_admin(user_id)
        
        if success:
            await message.reply_text(f"✅ User {user_id} has been removed from admin list.")
        else:
            await message.reply_text("❌ User is not an admin.")
    
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("admins") & filters.private)
async def list_admins(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    admins = await db.get_all_admins()
    
    text = "👑 **Admin List:**\n\n"
    text += f"👤 Owner: {Config.OWNER_ID}\n\n"
    
    if admins:
        text += "🔧 Admins:\n"
        for admin in admins:
            text += f"• {admin['user_id']}\n"
    else:
        text += "No additional admins."
    
    await message.reply_text(text)

@app.on_message(filters.command("addchnl") & filters.private)
async def add_channel(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    args = message.text.split(None, 2)
    if len(args) < 2:
        await message.reply_text("❌ Usage: /addchnl <channel_id> [name]")
        return
    
    try:
        channel_id = int(args[1])
        channel_name = args[2] if len(args) > 2 else None
        
        try:
            chat = await client.get_chat(channel_id)
            if not channel_name:
                channel_name = chat.title
        except Exception:
            pass
        
        success = await db.add_fsub_channel(channel_id, channel_name)
        
        if success:
            await message.reply_text(f"✅ Channel added to force subscribe list.\n📝 Name: {channel_name}")
        else:
            await message.reply_text("❌ Channel is already in the list.")
    
    except ValueError:
        await message.reply_text("❌ Invalid channel ID. Please provide a numeric channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("delchnl") & filters.private)
async def del_channel(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Usage: /delchnl <channel_id>")
        return
    
    try:
        channel_id = int(args[1])
        success = await db.remove_fsub_channel(channel_id)
        
        if success:
            await message.reply_text(f"✅ Channel {channel_id} removed from force subscribe list.")
        else:
            await message.reply_text("❌ Channel is not in the list.")
    
    except ValueError:
        await message.reply_text("❌ Invalid channel ID. Please provide a numeric channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("listchnl") & filters.private)
async def list_channels(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    channels = await db.get_all_fsub_channels()
    
    if not channels:
        await message.reply_text("✅ No force subscribe channels added.")
        return
    
    text = "📢 **Force Subscribe Channels:**\n\n"
    for channel in channels:
        text += f"📌 {channel.get('channel_name', 'Unknown')}\n"
        text += f"🆔 ID: {channel['channel_id']}\n\n"
    
    await message.reply_text(text)

@app.on_message(filters.command("fsub_mode") & filters.private)
async def toggle_fsub_mode(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for the owner.")
        return
    
    current = await db.get_setting('fsub_mode', True)
    new_mode = not current
    await db.set_setting('fsub_mode', new_mode)
    
    status = "enabled" if new_mode else "disabled"
    await message.reply_text(f"✅ Force subscribe mode {status}.")

@app.on_message(filters.command("delreq") & filters.private)
async def delete_requests(client: Client, message: Message):
    if not await is_admin_or_owner(message.from_user.id):
        await message.reply_text("❌ This command is only for admins.")
        return
    
    channels = await db.get_all_fsub_channels()
    
    if not channels:
        await message.reply_text("❌ No force subscribe channels configured.")
        return
    
    users = await db.get_all_users()
    status_msg = await message.reply_text("⏳ Checking users...")
    
    removed = 0
    
    for user in users:
        user_id = user['user_id']
        left_all = True
        
        for channel in channels:
            try:
                member = await client.get_chat_member(channel['channel_id'], user_id)
                if member.status not in ['left', 'kicked']:
                    left_all = False
                    break
            except Exception:
                continue
        
        if left_all:
            removed += 1
    
    await status_msg.edit_text(f"✅ Found {removed} users who left all channels.")

@app.on_callback_query(filters.regex("^refresh_fsub$"))
async def refresh_fsub(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    passed, markup = await check_force_sub(client, user_id)
    
    if passed:
        await callback.message.delete()
        await callback.message.reply_text("✅ You have joined all required channels! Please use /start again.")
    else:
        await callback.answer("❌ You still haven't joined all channels!", show_alert=True)

print("Bot is starting...")
app.run()
