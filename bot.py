import os
from dotenv import load_dotenv

# Load the secrets from the .env file
load_dotenv()

from telegram import ReplyKeyboardMarkup, KeyboardButton, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import threading

# --------------------------
# IMPORT OUR NEW MODULAR FILES
# --------------------------
import db
from translations import t
from payments import verify_telebirr_sms, mark_transaction_used
from socket_server import flask_app, run_socket_server
from api import api_bp

# --------------------------
# CONFIG
# --------------------------
TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "adwabingiobot"
ADMIN_IDS = [7627811244, 1119881250]
MINI_APP_URL = "https://sebez733-png.github.io/bingio-mini-app/"

# --------------------------
# STATE & COUNTERS
# --------------------------
user_state = {}
request_counter = 0
withdraw_requests = {}

# --------------------------
# HELPER: Normalize Phone
# --------------------------
def normalize_phone(phone):
    phone = phone.replace(" ", "").replace("+", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("251"): phone = "0" + phone[3:]
    if not phone.startswith("0") and len(phone) == 9: phone = "0" + phone
    return phone

# --------------------------
# HELPER: Get Main Menu
# --------------------------
def get_main_menu(lang='am'):
    if lang == 'en':
        return ReplyKeyboardMarkup([["🎮 Open Game"], ["💳 Deposit", "💰 Balance"], ["🐝 Withdraw", "📜 History"], ["👤 Profile", "🏢 Support"], ["🎁 Invite Friends", "🤖 Agent Panel"], ["🔄 Transfer", "ℹ️ Info"]], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([["🎮 Open Game / ይጫወቱ"], ["💳 Deposit / ያስገቡ", "💰 Balance / ሂሳብ"], ["🐝 Withdraw / ያውጡ", "📜 History / ታሪክ"], ["👤 Profile / መገለጫ", "🏢 Support / ድጋፍ"], ["🎁 Invite Friends / ጓደኛ ይጋብዙ", "🤖 Agent Panel"], ["🔄 Transfer / ይላኩ", "ℹ️ Info / መረጃ"]], resize_keyboard=True)

# --------------------------
# START
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or ''
    ref_id = context.args[0] if context.args else None
    context.user_data["ref_by"] = ref_id

    if db.user_exists(user_id):
        lang = db.get_user_language(user_id)
        db.update_user_name(user_id, first_name)
        await update.message.reply_text(t('welcome_back', lang), reply_markup=get_main_menu(lang))
        return

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"), InlineKeyboardButton("🇸🇸 English", callback_data="lang_en")]])
    await update.message.reply_text(t('select_language'), reply_markup=keyboard)

# --------------------------
# CONTACT REGISTER
# --------------------------
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or ''
    phone = normalize_phone(update.message.contact.phone_number)
    lang = context.user_data.get("lang", 'am')

    if db.user_exists(user_id):
        lang = db.get_user_language(user_id)
        user = db.get_user(user_id)
        main = db.get_main_balance(user_id)
        play = db.get_play_balance(user_id)
        ref_count = db.get_referral_count(user_id)
        text = t('already_registered', lang, phone=user[1], main=main, play=play, ref_count=ref_count)
        await update.message.reply_text(text)
        await update.message.reply_text("⬇️ Menu:", reply_markup=get_main_menu(lang))
        return

    ref_by = context.user_data.get("ref_by")
    db.add_user(user_id, phone, first_name)
    db.set_user_language(user_id, lang)
    if ref_by: db.set_referral(user_id, ref_by)

    main = db.get_main_balance(user_id)
    play = db.get_play_balance(user_id)
    text = t('register_success', lang, phone=phone, main=main, play=play)
    await update.message.reply_text(text)
    await update.message.reply_text("⬇️ Menu:", reply_markup=get_main_menu(lang))

# --------------------------
# TEXT HANDLER 
# --------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_text=None):
    user_id = update.effective_user.id
    text = custom_text if custom_text is not None else update.message.text
    first_name = update.effective_user.first_name or ''
    
    if first_name and db.user_exists(user_id): db.update_user_name(user_id, first_name)
    lang = db.get_user_language(user_id) if db.user_exists(user_id) else context.user_data.get("lang", 'am')

    if text in ["🎮 Open Game / ይጫወቱ", "🎮 Open Game"]:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Play Bingo Now", web_app=WebAppInfo(url=MINI_APP_URL))]])
        game_msg = "🎮 Tap the button below to open the Bingo Game:" if lang == 'en' else "🎮 የቢንጎ ጨዋታውን ለመክፈት ከታች ያለውን ቁልፍ ይጫኑ:"
        await update.message.reply_text(game_msg, reply_markup=keyboard)
        return

    if text in ["💰 Balance / ሂሳብ", "💰 Balance"]:
        main = db.get_main_balance(user_id)
        play = db.get_play_balance(user_id)
        await update.message.reply_text(t('balance_msg', lang, main=main, play=play))
        return

    await update.message.reply_text("👇 Please use the menu buttons" if lang == 'en' else "👇 የሜኑ ቁልፎችን ይጠቀሙ")

# --------------------------
# CALLBACK HANDLER
# --------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    first_name = query.from_user.first_name or ''
    
    if first_name and db.user_exists(user_id): db.update_user_name(user_id, first_name)

    if data in ["lang_am", "lang_en"]:
        lang = 'am' if data == "lang_am" else 'en'
        context.user_data["lang"] = lang
        if db.user_exists(user_id):
            db.set_user_language(user_id, lang)
            await query.message.edit_text(t('lang_changed', lang))
            await context.bot.send_message(chat_id=user_id, text=t('welcome_back', lang), reply_markup=get_main_menu(lang))
        return

# --------------------------
# LANG COMMAND
# --------------------------
async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"), InlineKeyboardButton("🇸🇸 English", callback_data="lang_en")]])
    await update.message.reply_text(t('select_language', 'en'), reply_markup=keyboard)

# --------------------------
# WEB APP DATA
# --------------------------
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = update.message.web_app_data.data
    print(f"🎮 Bingo win received from {user_name} ({user_id})! Data: {data}")
    await update.message.reply_text(f"🎉 Congratulations! Your bingo result has been recorded!\n\nData: {data}")


# --------------------------
# MISSING FUNCTIONS FIX
# --------------------------
async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"),
            InlineKeyboardButton("🇸🇬 English", callback_data="lang_en")
        ]
    ])
    await update.message.reply_text(t('select_language', 'en'), reply_markup=keyboard)

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = update.message.web_app_data.data
    print(f"🎮 Bingo win received from {user_name} ({user_id})! Data: {data}")
    await update.message.reply_text(f"🎉 Congratulations! Your bingo result has been recorded!\n\nData: {data}")

# ==========================
# APP SETUP & START
# ==========================
builder = ApplicationBuilder().token(TOKEN).connect_timeout(60.0).read_timeout(60.0).write_timeout(60.0).pool_timeout(60.0)
app = builder.build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lang", change_lang))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
app.add_handler(MessageHandler(filters.CONTACT, get_contact))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# --------------------------
# CONNECT MODULES & RUN
# --------------------------
flask_app.register_blueprint(api_bp)

flask_thread = threading.Thread(target=run_socket_server, daemon=True)
flask_thread.start()

print("✅ Modular Bot is running with SocketIO + API + MongoDB Cloud...")
app.run_polling()
