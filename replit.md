# Telegram File Store Bot Project

## Overview
Advanced Telegram file store bot with comprehensive admin controls, file sharing, batch link generation, user management, and force subscribe features. Built with Pyrogram and MongoDB.

## Recent Changes
- **2025-11-26**: Initial project setup with all core features
  - Implemented 25+ commands for file management, admin controls, and user management
  - Set up MongoDB database integration
  - Created force subscribe system
  - Added broadcast and auto-delete features

## Project Architecture

### Main Components
- `bot.py` - Main bot application with all command handlers
- `database.py` - MongoDB database operations and queries
- `helpers.py` - Helper functions for authorization, force subscribe, and utilities
- `config.py` - Configuration loader from environment variables
- `.env` - Environment variables (not in git)

### Tech Stack
- **Framework**: Pyrogram (Telegram MTProto API)
- **Database**: MongoDB (via motor - async driver)
- **Language**: Python 3.11
- **Encryption**: TgCrypto for faster Pyrogram operations

### Key Features
1. File store with link generation (single and batch)
2. Admin system with owner and multiple admins
3. User management (ban/unban)
4. Force subscribe system
5. Broadcasting with auto-delete
6. MongoDB for persistent storage
7. Log channel integration

## Configuration Required

### Environment Variables
- `API_ID` - Telegram API ID from my.telegram.org
- `API_HASH` - Telegram API Hash from my.telegram.org
- `BOT_TOKEN` - Bot token from @BotFather
- `OWNER_ID` - Telegram user ID of the bot owner
- `MONGODB_URI` - MongoDB connection string
- `LOG_CHANNEL` - Telegram channel ID for file logs (negative ID)
- `DATABASE_NAME` - MongoDB database name (default: telegram_file_store)

## User Preferences
- No specific preferences set yet

## Notes
- The bot uses MongoDB for data persistence
- All files are stored in a log channel
- Force subscribe system helps grow channels
- Auto-delete feature protects content
