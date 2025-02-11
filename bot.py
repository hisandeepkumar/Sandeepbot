import os
import json
import logging
import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


USERS_FILE = "users.json"

MEMBERS_FILE = "members.json"



# Load members from JSON file
def load_members():
    try:
        with open(MEMBERS_FILE, "r") as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data  # Agar JSON dictionary hai to use load karo
            else:
                return {}  # Agar format galat hai to empty dictionary return karo
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Agar file nahi hai ya corrupt hai to empty return karo

# Save members to JSON file
def save_members(members):
    with open(MEMBERS_FILE, "w") as file:
        json.dump(members, file, indent=4)

# Load members at startup
GROUP_MEMBERS = load_members()

# Load allowed users from JSON file
def load_users():
    try:
        with open(USERS_FILE, "r") as file:
            data = json.load(file)
            return set(data.get("allowed_users", []))  # Convert list to set
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

# Save allowed users to JSON file
def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump({"allowed_users": list(users)}, file)

# Load users at startup
ALLOWED_USERS = load_users()

# File to store triggers
SETTINGS_FILE = "settings.json"
TRIGGERS_FILE = "triggers.json"

# Default settings
settings = {
    "block_links": False,
    "block_media": False,
    "message_timer": 0,
    "muted_users": {},
    "banned_words": []
}

# Load settings from JSON file
def load_settings():
    global settings
    try:
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        save_settings()
    
    # Ensure all keys exist
    for key, default in {
        "block_links": False,
        "block_media": False,
        "message_timer": 0,
        "muted_users": {},
        "banned_words": []
    }.items():
        settings.setdefault(key, default)
    
    save_settings()

# Save settings to JSON file
def save_settings():
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file)

# Load triggers from JSON file
def load_triggers():
    global forwarding_triggers
    try:
        with open(TRIGGERS_FILE, "r") as file:
            forwarding_triggers = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        forwarding_triggers = {}

# Save triggers to JSON file
def save_triggers():
    with open(TRIGGERS_FILE, "w") as file:
        json.dump(forwarding_triggers, file)



# Decorator to restrict commands to admin/owner
def allowed_users_only(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            await update.message.reply_text("❌ You are not allowed to use this command!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper





#fetch members data




# ✅ Auto-Save Member When They Send a Message
async def save_user_data(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    chat_id = str(chat.id)  

    if chat.type in ["group", "supergroup"]:
        members = load_members()  # Load previous data

        # Agar group ka data nahi hai to ek empty list create karo
        if chat_id not in members:
            members[chat_id] = []

        user = update.effective_user
        user_data = {
            "id": user.id,
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "mobile": "Not Available"
        }

        # ✅ User already saved hai ya nahi check karo
        if not any(member["id"] == user.id for member in members[chat_id]):
            members[chat_id].append(user_data)  # Naya member add karo
            save_members(members)  # File update karo
            print(f"✅ New Member Saved: {user.full_name} ({user.id})")




# Check if user is admin or owner
async def is_admin(update: Update) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True

    chat_member = await chat.get_member(user.id)
    return chat_member.status in ["administrator", "creator"]


# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm your bot. Use /help to see available commands.")

# Help command (Admin Only)
@allowed_users_only
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Available commands (Admins Only):\n"
        "/start - Start bot\n"
        "/help - Help message\n"
        "/set <trigger> - Set a forwarding trigger (reply to a message)\n"
        "/remove <trigger> - Remove a forwarding trigger\n"
        "/block_media - Block non-admins from sending media\n"
        "/allow_media - Allow media for everyone\n"
        "/block_link - Block non-admins from sending links\n"
        "/allow_link - Allow links for everyone\n"
        "/ban - Ban a word (reply to a message)\n"
        "/unban <word> - Unban a word\n"
        "/mute - Mute a user (reply to a message)\n"
        "/unmute <username> - Unmute a user\n"
        "/set_timer <seconds> - Set message timer\n"
        "/remove_timer - Remove message timer"
        "/setwords - trigger words list"
        "/banwords - banned words list"
    )
    await update.message.reply_text(help_text)

# Welcome new members
async def welcome(update: Update, context: CallbackContext) -> None:
    if update.message:
        for new_member in update.message.new_chat_members:
            # Welcome in group
            await update.message.reply_text(f"Welcome {new_member.first_name} to the group!")
            # Welcome in private
            try:
                await context.bot.send_message(
                    chat_id=new_member.id,
                    text=f"Welcome {new_member.first_name}! Feel free to ask questions."
                )
            except Exception as e:
                logger.error(f"Error sending private welcome: {e}")

# Set trigger command (Admin Only)
@allowed_users_only
async def set_trigger(update: Update, context: CallbackContext) -> None:
    if not update.message.reply_to_message or not context.args:
        await update.message.reply_text("Usage: Reply to a message with /set <trigger>")
        return

    trigger = ' '.join(context.args).lower().strip()
    forwarding_triggers[trigger] = {
        'chat_id': update.message.reply_to_message.chat_id,
        'message_id': update.message.reply_to_message.message_id
    }
    save_triggers()
    await update.message.reply_text(f"Trigger '{trigger}' set successfully!")

# Remove trigger command (Admin Only)
@allowed_users_only
async def remove_trigger(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /remove <trigger>")
        return

    trigger = ' '.join(context.args).lower().strip()
    if trigger in forwarding_triggers:
        del forwarding_triggers[trigger]
        save_triggers()
        await update.message.reply_text(f"Trigger '{trigger}' removed!")
    else:
        await update.message.reply_text(f"Trigger '{trigger}' not found!")

# Block/Allow Media
@allowed_users_only
async def block_media(update: Update, context: CallbackContext) -> None:
    settings["block_media"] = True
    save_settings()
    await update.message.reply_text("Media messages blocked for non-admins!")

@allowed_users_only
async def allow_media(update: Update, context: CallbackContext) -> None:
    settings["block_media"] = False
    save_settings()
    await update.message.reply_text("Media messages allowed for everyone!")

# Block/Allow Links
@allowed_users_only
async def block_link(update: Update, context: CallbackContext) -> None:
    settings["block_links"] = True
    save_settings()
    await update.message.reply_text("Links blocked for non-admins!")

@allowed_users_only
async def allow_link(update: Update, context: CallbackContext) -> None:
    settings["block_links"] = False
    save_settings()
    await update.message.reply_text("Links allowed for everyone!")

# Ban word (Auto-delete)
@allowed_users_only
async def ban_word(update: Update, context: CallbackContext) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message with /ban")
        return

    banned_text = update.message.reply_to_message.text.lower()
    if banned_text not in settings["banned_words"]:
        settings["banned_words"].append(banned_text)
        save_settings()
        await update.message.reply_text(f"Banned: '{banned_text}'")

# Unban word
@allowed_users_only
async def unban_word(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /unban <word>")
        return

    word = ' '.join(context.args).lower()
    if word in settings["banned_words"]:
        settings["banned_words"].remove(word)
        save_settings()
        await update.message.reply_text(f"Unbanned: '{word}'")
    else:
        await update.message.reply_text(f"'{word}' not in banned list")


#set words list
@allowed_users_only
async def setwords(update: Update, context: CallbackContext) -> None:
    if not forwarding_triggers:
        await update.message.reply_text("📜 No triggers set!")
        return

    trigger_list = "\n".join([f"- {trigger}" for trigger in forwarding_triggers.keys()])
    await update.message.reply_text(f"📌 **Set Triggers:**\n{trigger_list}", parse_mode="Markdown")
#ban words list
@allowed_users_only
async def banwords(update: Update, context: CallbackContext) -> None:
    if not settings["banned_words"]:
        await update.message.reply_text("🚫 No banned words!")
        return

    banned_list = "\n".join([f"- {word}" for word in settings["banned_words"]])
    await update.message.reply_text(f"🚫 **Banned Words:**\n{banned_list}", parse_mode="Markdown")


#add users 
@allowed_users_only
async def add_user(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /adduser <user_id>")
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        save_users(ALLOWED_USERS)
        await update.message.reply_text(f"✅ User {user_id} added to allowed users!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
#remove users
@allowed_users_only
async def remove_user(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /removeuser <user_id>")
        return

    try:
        user_id = int(context.args[0])
        if user_id in ALLOWED_USERS:
            ALLOWED_USERS.remove(user_id)
            save_users(ALLOWED_USERS)
            await update.message.reply_text(f"❌ User {user_id} removed from allowed users!")
        else:
            await update.message.reply_text("⚠️ User not found in allowed list!")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

# members list 
import io
import csv
import json
import zipfile

@allowed_users_only
async def members(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # **Check Karo Ki Command Private Chat Se Aayi Hai Ya Nahi**
    if update.effective_chat.type != "private":
        await update.message.reply_text("⚠️ This command can only be used in bot's private chat!")
        return

    # **JSON File Se Members Load Karo**
    try:
        with open("members.json", "r", encoding="utf-8") as file:
            all_groups = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        await update.message.reply_text("⚠️ Members file not found or corrupted!")
        return

    if not all_groups:
        await update.message.reply_text("⚠️ No group members found!")
        return

    output = io.StringIO()
    writer = csv.writer(output)

    # **Header likho**
    writer.writerow(["Group ID", "User ID", "Name", "Username", "Mobile"])

    # **Sabhi Groups Ke Members Likho with Category-wise Format**
    for chat_id, members in all_groups.items():
        writer.writerow([f"Group ID: {chat_id}", "", "", "", ""])  # **Group Separator Row**
        writer.writerow(["User ID", "Name", "Username", "Mobile"])  # **Column Headers for Each Group**
        
        for member in members:
            writer.writerow([
                str(member.get("id", "Unknown")),  # User ID as string
                member.get("name", "Unknown"),
                member.get("username", "N/A"),
                member.get("mobile", "N/A")
            ])
        
        writer.writerow([])  # **Empty Row for Separation Between Groups**

    # **Cursor Reset Karo**
    output.seek(0)

    # **Telegram Pe CSV Send Karo**
    await update.message.reply_document(
        document=io.BytesIO(output.getvalue().encode()),
        filename="group_members.csv",
        caption="📄 Here is the list of all group members."
    )

# Set/Remove Spam Timer
@allowed_users_only
async def set_timer(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /set_timer <seconds>")
        return

    try:
        settings["message_timer"] = int(context.args[0])
        save_settings()
        await update.message.reply_text(f"Message timer set to {settings['message_timer']}s")
    except ValueError:
        await update.message.reply_text("Invalid number!")

@allowed_users_only
async def remove_timer(update: Update, context: CallbackContext) -> None:
    settings["message_timer"] = 0
    save_settings()
    await update.message.reply_text("Message timer disabled!")

# Message filtering
async def filter_messages(update: Update, context: CallbackContext) -> None:
    if update.message.text:
        text = update.message.text.lower()

        # ⚡️ Agar message trigger hai, to pehle `auto_forward` run hone do
        if text in forwarding_triggers:
            await auto_forward(update, context)  # Pehle forward karne do
              
            return

        # 🚀 Banned words ka check
        if any(word in text for word in settings["banned_words"]):
            await update.message.delete()
            return

        # 🌐 Links ka check
        if settings["block_links"] and ("http://" in text or "https://" in text):
            if not await is_admin(update):
                await update.message.delete()
                return

   

    # Check media
    if settings["block_media"] and (update.message.photo or update.message.video or update.message.document):
        if not await is_admin(update):
            await update.message.delete()
            return

# Auto-forward messages
async def auto_forward(update: Update, context: CallbackContext) -> None:
    if update.message.text:
        text = update.message.text.lower().strip()
        if text in forwarding_triggers:
            data = forwarding_triggers[text]
            try:
                await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=data['chat_id'],
                    message_id=data['message_id']
                )
            except Exception as e:
                logger.error(f"Forward error: {e}")



# Mute user (Admin Only)
@allowed_users_only
async def mute_user(update: Update, context: CallbackContext) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /mute to mute them.")
        return

    user_id = update.message.reply_to_message.from_user.id
    username = update.message.reply_to_message.from_user.username or update.message.reply_to_message.from_user.first_name
    settings["muted_users"][str(user_id)] = time.time() + 7200  # Auto unmute in 2 hours
    save_settings()

    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text(f"Muted @{username} for 2 hours!")

# Unmute user (Admin Only)
@allowed_users_only
async def unmute_user(update: Update, context: CallbackContext) -> None:
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("Reply to a muted user's message with /unmute or use /unmute <user_id>")
        return

    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Invalid user ID!")
            return

    if str(user_id) in settings["muted_users"]:
        del settings["muted_users"][str(user_id)]
        save_settings()

        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

        await update.message.reply_text(f"User {user_id} has been manually unmuted!")
    else:
        await update.message.reply_text("User is not muted or invalid user ID!")

# Auto-unmute function (Runs Every 10 Minutes)
async def auto_unmute_task(context: CallbackContext) -> None:
    while True:
        current_time = time.time()
        unmuted_users = []

        for user_id, unmute_time in list(settings["muted_users"].items()):
            if current_time >= unmute_time:  # If 2 hours are over
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=context.job.chat_id,
                        user_id=int(user_id),
                        permissions=ChatPermissions(can_send_messages=True)
                    )
                    unmuted_users.append(user_id)
                except Exception as e:
                    logger.error(f"Auto-unmute failed for {user_id}: {e}")

        # Remove auto-unmuted users from the list
        for user_id in unmuted_users:
            del settings["muted_users"][user_id]
        
        save_settings()

        await asyncio.sleep(600)  # Check every 10 minutes

# Main function
def main() -> None:
    # Load persisted data
    load_settings()
    load_triggers()

    # Create application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set", set_trigger))
    application.add_handler(CommandHandler("remove", remove_trigger))
    application.add_handler(CommandHandler("block_media", block_media))
    application.add_handler(CommandHandler("allow_media", allow_media))
    application.add_handler(CommandHandler("block_link", block_link))
    application.add_handler(CommandHandler("allow_link", allow_link))
    application.add_handler(CommandHandler("ban", ban_word))
    application.add_handler(CommandHandler("unban", unban_word))
    application.add_handler(CommandHandler("setwords", setwords))
    application.add_handler(CommandHandler("banwords", banwords))
    application.add_handler(CommandHandler("adduser", add_user))
    application.add_handler(CommandHandler("removeuser", remove_user))
    application.add_handler(CommandHandler("members", members))
    
    application.add_handler(CommandHandler("set_timer", set_timer))
    application.add_handler(CommandHandler("remove_timer", remove_timer))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(MessageHandler(filters.ALL, save_user_data), group=-1)
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
   
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_forward))


    # Start auto-unmute background task
    application.job_queue.run_repeating(auto_unmute_task, interval=600, first=10)
    # Start bot
    logger.info("Bot started")
    application.run_polling()

if __name__ == "__main__":
    main()
