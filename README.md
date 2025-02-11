# Sandeepbot

# Telegram Group Moderator Bot  

A powerful Telegram bot for group moderation, automatic user management, and spam control. This bot helps admins maintain group discipline by blocking spam, muting users, banning words, and more.  

## Features  

✅ Auto-save members when they send a message  
✅ Anti-spam with banned word detection  
✅ Block/allow media & links  
✅ Auto-mute and unmute users  
✅ Auto-forward messages based on trigger words  
✅ Group member list export in CSV format  
✅ Admin-only commands for better control  

## Commands  

### Admin Commands  

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/set <trigger>` | Set a forwarding trigger (reply to a message) |
| `/remove <trigger>` | Remove a forwarding trigger |
| `/block_media` | Block non-admins from sending media |
| `/allow_media` | Allow media for everyone |
| `/block_link` | Block non-admins from sending links |
| `/allow_link` | Allow links for everyone |
| `/ban` (reply to a message) | Ban a word from being sent in the group |
| `/unban <word>` | Remove a word from the banned list |
| `/setwords` | Show the list of trigger words |
| `/banwords` | Show the list of banned words |
| `/adduser <user_id>` | Add an admin user to use commands |
| `/removeuser <user_id>` | Remove an admin user |
| `/members` | Download a CSV file of group members |
| `/set_timer <seconds>` | Set a message spam timer |
| `/remove_timer` | Remove the spam timer |
| `/mute` (reply to a user) | Mute a user for 2 hours |
| `/unmute <user_id>` | Unmute a user |

## Installation  

1. **Clone this repository**  
   ```sh
   git clone https://github.com/yourusername/telegram-group-moderator-bot.git
   cd telegram-group-moderator-bot

2. Install dependencies

pip install python-telegram-bot python-dotenv


3. Set up environment variables

Create a .env file

Add your bot token inside .env file:

BOT_TOKEN=your_telegram_bot_token



4. Run the bot

python bot.py



Deployment

For hosting on a cloud server:

Use Pella.app for easy deployment

Or deploy on Heroku, Railway, or VPS


License

This bot is open-source and available under the MIT License.

Contributing

Feel free to contribute! If you find any bugs or want to improve features, create a pull request.


---

⚡ Made with ❤️ by Sandeep

## 📢 Connect with Me  
[![Instagram](https://img.shields.io/badge/📸-Follow_Me_on_Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/sandeep_yadav_._._/)
---


