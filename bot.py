import json, os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- CONFIG ----------
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
ADMIN_ID = config["admin_id"]
LOG_CHANNEL = config["log_channel_id"]

# ---------- USERS FILE ----------
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        json.dump({}, f)

def load_users():
    with open("users.json") as f:
        return json.load(f)

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

app = Client("bot", bot_token=BOT_TOKEN)

# ---------- START ----------
START_TEXT = """
✨ Thank you for reaching out!

🤖 You are now connected to our support system.
Please send your message, and admin will reply soon.

━━━━━━━━━━━━━━━

🚀 Developed by @TALK_WITH_STEALED
"""

start_btn = InlineKeyboardMarkup([
    [InlineKeyboardButton("📩 Send Message", callback_data="send")]
])

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(START_TEXT, reply_markup=start_btn)

# ---------- BUTTON ----------
@app.on_callback_query(filters.regex("send"))
async def send_msg(client, callback):
    await callback.message.reply_text("📩 Send your message now")

# ---------- MESSAGE ----------
@app.on_message(filters.private & ~filters.command("start"))
async def handle_msg(client, message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name
    username = message.from_user.username or "no_username"

    users = load_users()

    if user_id not in users:
        users[user_id] = {
            "name": name,
            "username": username,
            "log_msg_id": None,
            "messages": []
        }

    users[user_id]["messages"].append(f"📩 {message.text}")

    text = f"👤 {name} (@{username})\n🆔 {user_id}\n\n"
    for m in users[user_id]["messages"]:
        text += m + "\n"

    if users[user_id]["log_msg_id"] is None:
        msg = await app.send_message(LOG_CHANNEL, text)
        users[user_id]["log_msg_id"] = msg.id
    else:
        try:
            await app.edit_message_text(LOG_CHANNEL, users[user_id]["log_msg_id"], text)
        except:
            pass

    save_users(users)

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reply", callback_data=f"reply_{user_id}")]
    ])

    await app.send_message(
        ADMIN_ID,
        f"📩 {name} (@{username})\nID: {user_id}\n\n{message.text}",
        reply_markup=btn
    )

# ---------- ADMIN REPLY ----------
reply_mode = {}

@app.on_callback_query(filters.regex("reply_"))
async def reply_user(client, callback):
    uid = callback.data.split("_")[1]
    reply_mode[callback.from_user.id] = uid
    await callback.message.reply_text("✍️ Send reply")

@app.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_reply(client, message):
    if message.from_user.id in reply_mode:
        uid = reply_mode[message.from_user.id]

        await app.send_message(int(uid), f"🤖 Admin:\n{message.text}")

        users = load_users()
        users[uid]["messages"].append(f"🤖 {message.text}")

        text = f"👤 {users[uid]['name']} (@{users[uid]['username']})\n🆔 {uid}\n\n"
        for m in users[uid]["messages"]:
            text += m + "\n"

        try:
            await app.edit_message_text(LOG_CHANNEL, users[uid]["log_msg_id"], text)
        except:
            pass

        save_users(users)

app.run()
