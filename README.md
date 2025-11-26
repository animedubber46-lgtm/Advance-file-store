# Telegram File Store Bot

An advanced Telegram file store bot with comprehensive admin controls, file sharing, batch link generation, user management, and force subscribe features.

## Features

### 📁 File Management
- **Single File Links** - Generate shareable links for individual files
- **Batch Links** - Create links for multiple files from the log channel
- **Custom Batch** - Import and create batch links from any channel/group
- **Auto-Delete** - Configurable auto-delete time for shared files

### 👥 User Management
- **User Statistics** - Track total users and bot statistics
- **Ban/Unban Users** - Block users from accessing the bot
- **Ban List** - View all banned users
- **User Tracking** - Log all new users with details in the log channel

### 🔧 Admin Features
- **Multiple Admins** - Owner can add/remove admins
- **Admin List** - View all current admins
- **Broadcasting** - Send messages to all users
- **Auto-Delete Broadcast** - Broadcast with automatic message deletion
- **Pin Broadcast** - Broadcast and pin messages to all users

### 🔒 Force Subscribe
- **Add Channels** - Require users to join specific channels
- **Remove Channels** - Remove force subscribe channels
- **List Channels** - View all force subscribe channels
- **Toggle Mode** - Enable/disable force subscribe system
- **Clean Up** - Remove users who left required channels

### 📊 Statistics & Monitoring
- **Bot Uptime** - Check how long the bot has been running
- **User Statistics** - View total and active users
- **Log Channel** - All files and new users logged automatically

## Commands List

### General Commands
- `/start` - Start the bot or get posts via shared links

### Admin Commands
- `/genlink` - Generate link for a single post (reply to a message)
- `/batch <first_id> <last_id>` - Create batch link for multiple posts
- `/custom_batch <channel_id> <first_id> <last_id>` - Create custom batch from channel
- `/users` - View bot statistics
- `/broadcast` - Broadcast message to all users (reply to a message)
- `/dbroadcast` - Broadcast with auto-delete (reply to a message)
- `/pbroadcast` - Broadcast and pin message (reply to a message)
- `/stats` - Check bot uptime and statistics
- `/ban <user_id> [reason]` - Ban a user from using the bot
- `/unban <user_id>` - Unban a previously banned user
- `/banlist` - Get list of all banned users
- `/dlt_time <seconds>` - Set auto-delete time for files
- `/check_dlt_time` - Check current auto-delete time setting
- `/delreq` - Remove users who left force subscribe channels

### Owner Commands
- `/add_admin <user_id>` - Add a new admin
- `/deladmin <user_id>` - Remove an admin
- `/admins` - List all current admins
- `/addchnl <channel_id> [name]` - Add a channel for force subscription
- `/delchnl <channel_id>` - Remove a force subscribe channel
- `/listchnl` - View all added force subscribe channels
- `/fsub_mode` - Toggle force subscribe on or off

## Setup Instructions

### Prerequisites
1. **Telegram API Credentials**
   - Visit https://my.telegram.org/apps
   - Create a new application
   - Note down your `API_ID` and `API_HASH`

2. **Bot Token**
   - Chat with [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot using `/newbot`
   - Save the bot token

3. **MongoDB Database**
   - Get a free MongoDB database from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Or use any MongoDB connection string

4. **Log Channel**
   - Create a new private channel on Telegram
   - Add your bot as an admin with post messages permission
   - Get the channel ID (it will be negative, like -1001234567890)

5. **Owner ID**
   - Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

### Environment Variables

Create a `.env` file with the following variables:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_user_id
MONGODB_URI=mongodb://your_mongodb_connection_string
LOG_CHANNEL=-1001234567890
DATABASE_NAME=telegram_file_store
```

### Installation (Local)

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.env` file with all required credentials
4. Run the bot:
   ```bash
   python bot.py
   ```

## Deploy to Render

This bot includes a `render.yaml` file for easy deployment to [Render](https://render.com).

### Step-by-Step Render Deployment

1. **Create a Render Account**
   - Go to [render.com](https://render.com) and sign up for a free account
   - Connect your GitHub account

2. **Push Code to GitHub**
   - Create a new GitHub repository
   - Push all the bot files to your repository:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git remote add origin https://github.com/yourusername/your-repo.git
     git push -u origin main
     ```

3. **Create New Web Service on Render**
   - Click "New" > "Blueprint" in Render dashboard
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

4. **Configure Environment Variables**
   - After deployment, go to your service's "Environment" tab
   - Add the following environment variables:

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `API_ID` | Your Telegram API ID | `12345678` |
   | `API_HASH` | Your Telegram API Hash | `abcdef1234567890...` |
   | `BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
   | `OWNER_ID` | Your Telegram user ID | `123456789` |
   | `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
   | `LOG_CHANNEL` | Your log channel ID | `-1001234567890` |

5. **Deploy**
   - Click "Manual Deploy" > "Deploy latest commit"
   - Wait for the build to complete
   - Your bot should now be running 24/7!

### Alternative: Deploy via Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" > "Background Worker"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `telegram-file-store-bot`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Add all environment variables in the "Environment" section
6. Click "Create Background Worker"

### Render Free Tier Notes

- Free tier services spin down after 15 minutes of inactivity
- For 24/7 uptime, consider upgrading to a paid plan ($7/month for Starter)
- Free tier includes 750 hours/month which is enough for one always-on service

## Usage Guide

### For Admins

#### Generating Single File Links
1. Forward or send a file to the bot in private chat
2. Reply to that file with `/genlink`
3. Bot will save it to log channel and generate a shareable link

#### Creating Batch Links
1. Use `/batch <first_id> <last_id>` with message IDs from your log channel
2. Example: `/batch 100 150` creates a link for messages 100-150
3. Share the generated link with users

#### Creating Custom Batch from Another Channel
1. Make sure the bot is a member of the source channel
2. Use `/custom_batch <channel_id> <first_id> <last_id>`
3. Example: `/custom_batch -1001234567890 100 150`
4. Bot will copy those messages to log channel and create a batch link

#### Broadcasting Messages
1. Prepare your message
2. Forward or send it to the bot
3. Reply to it with `/broadcast`, `/dbroadcast`, or `/pbroadcast`

### For Users

1. Click on a shared link from admin
2. Start the bot
3. If force subscribe is enabled, join required channels
4. Click "Refresh" button
5. Receive your file(s)

## How It Works

1. **File Storage**: When admins use `/genlink`, files are stored in the log channel
2. **Link Generation**: Bot creates encrypted links with message IDs
3. **File Retrieval**: Users access files via links, bot forwards from log channel
4. **Force Subscribe**: Bot checks if users joined required channels before sharing files
5. **Auto-Delete**: Files can be configured to auto-delete after specified time

## Security Features

- Owner-only commands for critical operations
- Admin verification for file management
- Banned user blocking
- Force subscribe system for channel growth
- MongoDB for secure data storage

## Database Collections

- **users** - All bot users with join timestamps
- **admins** - Admin user IDs
- **files** - File metadata and message IDs
- **banned_users** - Banned user list with reasons
- **fsub_channels** - Force subscribe channel list
- **settings** - Bot configuration (auto-delete time, fsub mode, etc.)

## Support

For issues or questions, contact the bot owner.

## License

This bot is provided as-is for educational and personal use.
