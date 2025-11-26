from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import Config
import uuid

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.users = self.db['users']
        self.admins = self.db['admins']
        self.files = self.db['files']
        self.settings = self.db['settings']
        self.banned_users = self.db['banned_users']
        self.fsub_channels = self.db['fsub_channels']
    
    async def add_user(self, user_id, username=None, first_name=None):
        user_data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'joined_at': datetime.now()
        }
        existing = await self.users.find_one({'user_id': user_id})
        if not existing:
            await self.users.insert_one(user_data)
            return True
        return False
    
    async def get_user(self, user_id):
        return await self.users.find_one({'user_id': user_id})
    
    async def get_all_users(self):
        users = []
        async for user in self.users.find({}):
            users.append(user)
        return users
    
    async def total_users_count(self):
        return await self.users.count_documents({})
    
    async def add_admin(self, user_id):
        admin_data = {'user_id': user_id, 'added_at': datetime.now()}
        existing = await self.admins.find_one({'user_id': user_id})
        if not existing:
            await self.admins.insert_one(admin_data)
            return True
        return False
    
    async def remove_admin(self, user_id):
        result = await self.admins.delete_one({'user_id': user_id})
        return result.deleted_count > 0
    
    async def is_admin(self, user_id):
        if user_id == Config.OWNER_ID:
            return True
        admin = await self.admins.find_one({'user_id': user_id})
        return admin is not None
    
    async def get_all_admins(self):
        admins = []
        async for admin in self.admins.find({}):
            admins.append(admin)
        return admins
    
    async def save_file(self, file_id, file_type, message_id, channel_id, added_by, unique_token=None):
        if unique_token is None:
            unique_token = str(uuid.uuid4())
        
        file_data = {
            'file_id': file_id,
            'file_type': file_type,
            'message_id': message_id,
            'channel_id': channel_id,
            'added_by': added_by,
            'unique_token': unique_token,
            'added_at': datetime.now()
        }
        await self.files.insert_one(file_data)
        return unique_token
    
    async def get_file_by_token(self, token):
        return await self.files.find_one({'unique_token': token})
    
    async def get_file(self, message_id):
        return await self.files.find_one({'message_id': message_id})
    
    async def ban_user(self, user_id, banned_by, reason=None):
        ban_data = {
            'user_id': user_id,
            'banned_by': banned_by,
            'reason': reason,
            'banned_at': datetime.now()
        }
        existing = await self.banned_users.find_one({'user_id': user_id})
        if not existing:
            await self.banned_users.insert_one(ban_data)
            return True
        return False
    
    async def unban_user(self, user_id):
        result = await self.banned_users.delete_one({'user_id': user_id})
        return result.deleted_count > 0
    
    async def is_banned(self, user_id):
        banned = await self.banned_users.find_one({'user_id': user_id})
        return banned is not None
    
    async def get_all_banned_users(self):
        banned = []
        async for user in self.banned_users.find({}):
            banned.append(user)
        return banned
    
    async def set_setting(self, key, value):
        await self.settings.update_one(
            {'key': key},
            {'$set': {'value': value, 'updated_at': datetime.now()}},
            upsert=True
        )
    
    async def get_setting(self, key, default=None):
        setting = await self.settings.find_one({'key': key})
        if setting:
            return setting['value']
        return default
    
    async def add_fsub_channel(self, channel_id, channel_name=None):
        channel_data = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'added_at': datetime.now()
        }
        existing = await self.fsub_channels.find_one({'channel_id': channel_id})
        if not existing:
            await self.fsub_channels.insert_one(channel_data)
            return True
        return False
    
    async def remove_fsub_channel(self, channel_id):
        result = await self.fsub_channels.delete_one({'channel_id': channel_id})
        return result.deleted_count > 0
    
    async def get_all_fsub_channels(self):
        channels = []
        async for channel in self.fsub_channels.find({}):
            channels.append(channel)
        return channels
    
    async def save_batch(self, first_msg_id, last_msg_id, channel_id, added_by, unique_token=None):
        if unique_token is None:
            unique_token = str(uuid.uuid4())
        
        batch_data = {
            'first_msg_id': first_msg_id,
            'last_msg_id': last_msg_id,
            'channel_id': channel_id,
            'added_by': added_by,
            'unique_token': unique_token,
            'added_at': datetime.now()
        }
        await self.db['batches'].insert_one(batch_data)
        return unique_token
    
    async def get_batch_by_token(self, token):
        return await self.db['batches'].find_one({'unique_token': token})
