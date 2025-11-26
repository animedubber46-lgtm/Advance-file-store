from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, UsernameNotOccupied
from config import Config
from database import Database

db = Database()

async def is_owner(user_id):
    return user_id == Config.OWNER_ID

async def is_admin_or_owner(user_id):
    return await db.is_admin(user_id) or user_id == Config.OWNER_ID

async def check_force_sub(client: Client, user_id):
    fsub_enabled = await db.get_setting('fsub_mode', True)
    
    if not fsub_enabled:
        return True, None
    
    channels = await db.get_all_fsub_channels()
    
    if not channels:
        return True, None
    
    not_joined = []
    buttons = []
    
    for channel in channels:
        try:
            member = await client.get_chat_member(channel['channel_id'], user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except UserNotParticipant:
            not_joined.append(channel)
        except Exception:
            continue
    
    if not_joined:
        for channel in not_joined:
            try:
                chat = await client.get_chat(channel['channel_id'])
                invite_link = chat.invite_link
                if not invite_link:
                    invite_link = f"https://t.me/{chat.username}" if chat.username else None
                
                if invite_link:
                    channel_name = channel.get('channel_name') or chat.title
                    buttons.append([InlineKeyboardButton(f"Join {channel_name}", url=invite_link)])
            except Exception:
                continue
        
        buttons.append([InlineKeyboardButton("✅ Refresh", callback_data="refresh_fsub")])
        return False, InlineKeyboardMarkup(buttons)
    
    return True, None

def get_readable_time(seconds):
    periods = [
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
        ('s', 1)
    ]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)}{period_name}")
    return ' '.join(result) if result else '0s'
