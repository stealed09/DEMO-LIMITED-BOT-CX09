import json, os, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ---------- LOAD CONFIG ----------
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

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """✨ Thank you for reaching out!

🤖 You are now connected to our support system.
Please send your message, and admin will reply soon.

━━━━━━━━━━━━━━━

🚀 Developed by @TALK_WITH_STEALED
"""
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Send Message", callback_data="send")]
    ])
    await update.message.reply_text(text, reply_markup=btn)

# ---------- BUTTON ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "send":
        await query.message.reply_text("📩 Send your message now")

    elif query.data.startswith("reply_"):
        uid = query.data.split("_")[1]
        context.user_data["reply_to"] = uid
        await query.message.reply_text("✍️ Send reply now")

# ---------- USER MESSAGE ----------
async def user_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        return

    user = update.effective_user
    uid = str(user.id)

    users = load_users()

    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": user.username or "no_username",
            "log_msg_id": None,
            "messages": []
        }

    users[uid]["messages"].append(f"📩 {update.message.text}")

    # -------- LOG CHANNEL --------
    text = f"👤 {users[uid]['name']} (@{users[uid]['username']})\n🆔 {uid}\n\n"
    for m in users[uid]["messages"]:
        text += m + "\n"

    if users[uid]["log_msg_id"] is None:
        msg = await context.bot.send_message(LOG_CHANNEL, text)
        users[uid]["log_msg_id"] = msg.message_id
    else:
        try:
            await context.bot.edit_message_text(
                chat_id=LOG_CHANNEL,
                message_id=users[uid]["log_msg_id"],
                text=text
            )
        except:
            pass

    save_users(users)

    # -------- SEND TO ADMIN --------
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Reply", callback_data=f"reply_{uid}")]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 {user.first_name} (@{user.username})\nID: {uid}\n\n{update.message.text}",
        reply_markup=btn
    )

# ---------- ADMIN REPLY ----------
async def admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if "reply_to" not in context.user_data:
        return

    uid = context.user_data["reply_to"]

    await context.bot.send_message(
        chat_id=int(uid),
        text=f"🤖 Admin:\n{update.message.text}"
    )

    users = load_users()
    users[uid]["messages"].append(f"🤖 {update.message.text}")

    text = f"👤 {users[uid]['name']} (@{users[uid]['username']})\n🆔 {uid}\n\n"
    for m in users[uid]["messages"]:
        text += m + "\n"

    try:
        await context.bot.edit_message_text(
            chat_id=LOG_CHANNEL,
            message_id=users[uid]["log_msg_id"],
            text=text
        )
    except:
        pass

    save_users(users)

# ---------- MAIN ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_msg))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_msg))

print("Bot running...")
app.run_polling()
