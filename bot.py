from telegram import ReplyKeyboardMarkup, KeyboardButton, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import threading

# --------------------------
# IMPORT OUR NEW MODULAR FILES
# --------------------------
import db
from translations import t
from payments import verify_telebirr_sms, mark_transaction_used
from socket_server import flask_app, socketio, run_socket_server, games, BingoGame
from api import api_bp  # Import the API blueprint

# --------------------------
# CONFIG
# --------------------------
TOKEN = "8607291518:AAG1IFDDL4CrB8puYNkG8ZWbOTxOl8uK6xo"
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
    if phone.startswith("251"):
        phone = "0" + phone[3:]
    if not phone.startswith("0") and len(phone) == 9:
        phone = "0" + phone
    return phone

# --------------------------
# HELPER: Get Main Menu
# --------------------------
def get_main_menu(lang='am'):
    if lang == 'en':
        return ReplyKeyboardMarkup([
            ["🎮 Open Game"], ["💳 Deposit", "💰 Balance"],
            ["🐝 Withdraw", "📜 History"], ["👤 Profile", "🏢 Support"],
            ["🎁 Invite Friends", "🤖 Agent Panel"], ["🔄 Transfer", "ℹ️ Info"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["🎮 Open Game / ይጫወቱ"], ["💳 Deposit / ያስገቡ", "💰 Balance / ሂሳብ"],
            ["🐝 Withdraw / ያውጡ", "📜 History / ታሪክ"], ["👤 Profile / መገለጫ", "🏢 Support / ድጋፍ"],
            ["🎁 Invite Friends / ጓደኛ ይጋብዙ", "🤖 Agent Panel"], ["🔄 Transfer / ይላኩ", "ℹ️ Info / መረጃ"]
        ], resize_keyboard=True)

# --------------------------
# HELPER: Get Inline Menu
# --------------------------
def get_inline_menu(lang='am'):
    if lang == 'en':
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Open Game", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton("💳 Deposit", callback_data="menu_deposit"), InlineKeyboardButton("💰 Balance", callback_data="menu_balance")],
            [InlineKeyboardButton("🐝 Withdraw", callback_data="menu_withdraw"), InlineKeyboardButton("📜 History", callback_data="menu_history")],
            [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"), InlineKeyboardButton("🏢 Support", callback_data="menu_support")],
            [InlineKeyboardButton("🎁 Invite Friends", callback_data="menu_invite"), InlineKeyboardButton("🤖 Agent Panel", callback_data="menu_agent")],
            [InlineKeyboardButton("🔄 Transfer", callback_data="menu_transfer"), InlineKeyboardButton("ℹ️ Info", callback_data="menu_info")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Open Game / ይጫወቱ", web_app=WebAppInfo(url=MINI_APP_URL))],
            [InlineKeyboardButton("💳 Deposit / ያስገቡ", callback_data="menu_deposit"), InlineKeyboardButton("💰 Balance / ሂሳብ", callback_data="menu_balance")],
            [InlineKeyboardButton("🐝 Withdraw / ያውጡ", callback_data="menu_withdraw"), InlineKeyboardButton("📜 History / ታሪክ", callback_data="menu_history")],
            [InlineKeyboardButton("👤 Profile / መገለጫ", callback_data="menu_profile"), InlineKeyboardButton("🏢 Support / ድጋፍ", callback_data="menu_support")],
            [InlineKeyboardButton("🎁 Invite Friends / ጓደኛ ይጋብዙ", callback_data="menu_invite"), InlineKeyboardButton("🤖 Agent Panel", callback_data="menu_agent")],
            [InlineKeyboardButton("🔄 Transfer / ይላኩ", callback_data="menu_transfer"), InlineKeyboardButton("ℹ️ Info / መረጃ", callback_data="menu_info")]
        ])

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
        menu = get_main_menu(lang)
        await update.message.reply_text(t('welcome_back', lang), reply_markup=menu)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"), InlineKeyboardButton("🇸🇸 English", callback_data="lang_en")]
    ])
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
        await update.message.reply_text(text, reply_markup=get_inline_menu(lang))
        await update.message.reply_text("⬇️ Menu:", reply_markup=get_main_menu(lang))
        return

    ref_by = context.user_data.get("ref_by")
    db.add_user(user_id, phone, first_name)
    db.set_user_language(user_id, lang)

    if ref_by:
        db.set_referral(user_id, ref_by)

    main = db.get_main_balance(user_id)
    play = db.get_play_balance(user_id)
    text = t('register_success', lang, phone=phone, main=main, play=play)

    await update.message.reply_text(text, reply_markup=get_inline_menu(lang))
    await update.message.reply_text("⬇️ Menu:", reply_markup=get_main_menu(lang))

# --------------------------
# TEXT HANDLER (Simplified using translations.py)
# --------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_text=None):
    global request_counter
    user_id = update.effective_user.id
    text = custom_text if custom_text is not None else update.message.text
    first_name = update.effective_user.first_name or ''
    
    if first_name and db.user_exists(user_id):
        db.update_user_name(user_id, first_name)

    lang = db.get_user_language(user_id) if db.user_exists(user_id) else context.user_data.get("lang", 'am')

    # Clear states on main menu clicks
    main_menu_buttons = ["🎮 Open Game", "💳 Deposit", "💰 Balance", "🐝 Withdraw", "📜 History", "👤 Profile", "🏢 Support", "🎁 Invite Friends", "🤖 Agent Panel", "🔄 Transfer", "ℹ️ Info",
                         "🎮 Open Game / ይጫወቱ", "💳 Deposit / ያስገቡ", "💰 Balance / ሂሳብ", "🐝 Withdraw / ያውጡ", "📜 History / ታሪክ", "👤 Profile / መገለጫ", "🏢 Support / ድጋፍ", "🎁 Invite Friends / ጓደኛ ይጋብዙ", "🔄 Transfer / ይላኩ", "ℹ️ Info / መረጃ"]
    if text in main_menu_buttons:
        user_state.pop(user_id, None)
        user_state.pop(f"{user_id}_amount", None)
        user_state.pop(f"{user_id}_withdraw_amount", None)
        user_state.pop(f"{user_id}_method", None)
        user_state.pop(f"{user_id}_transfer_wallet", None)
        user_state.pop(f"{user_id}_transfer_target", None)

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

    if text in ["💳 Deposit / ያስገቡ", "💳 Deposit"]:
        user_state[user_id] = "deposit_amount"
        await update.message.reply_text(t('deposit_prompt', lang))
        return

    if text in ["🐝 Withdraw / ያውጡ", "🐝 Withdraw"]:
        total_lifetime_deposits = db.get_total_deposits(user_id)
        if total_lifetime_deposits < 50:
            await update.message.reply_text(t('withdraw_locked', lang))
            return
        user_state[user_id] = "withdraw_amount"
        play_bal = db.get_play_balance(user_id)
        main_bal = db.get_main_balance(user_id)
        await update.message.reply_text(t('withdraw_prompt', lang, play_bal=play_bal, main_bal=main_bal))
        return

    # ... [KEEP ALL YOUR OTHER TEXT HANDLING LOGIC FOR PROFILE, HISTORY, TRANSFER ETC HERE] ...
    # [I am shortening it for readability, but copy-paste your logic for those here, just replace hardcoded text with t('key', lang)]
    
    # DEPOSIT SMS VERIFICATION (Now using our modular payments.py!)
    if user_state.get(user_id) == "deposit_confirm":
        amount = user_state.get(f"{user_id}_amount", 0)
        method = user_state.get(f"{user_id}_method", "Unknown")

        if text == "🔙 Back":
            user_state[user_id] = "deposit_method"
            keyboard = ReplyKeyboardMarkup([["Telebirr"], ["🔙 Back"]], resize_keyboard=True)
            await update.message.reply_text("💳 Select Payment Method:", reply_markup=keyboard)
            return

        # Call our new modular payment function!
        result = verify_telebirr_sms(sms_text=text, expected_amount=amount)

        if not result['valid']:
            await update.message.reply_text(result['reason'], parse_mode="Markdown")
            return

        transaction_id = result['transaction_id']
        confirmed_amount = int(result['amount'])
        bonus = int(confirmed_amount * 0.10)
        total = confirmed_amount + bonus

        # Mark as used in our modular payment function!
        mark_transaction_used(transaction_id, user_id, confirmed_amount)

        db.update_play_balance(user_id, total)
        db.add_transaction(user_id, "deposit", total)
        new_balance = db.get_play_balance(user_id)

        # Handle Referral Bonuses (kept in bot because it interacts with Telegram context to send messages)
        user = db.get_user(user_id)
        ref_by = user[4] if user and len(user) > 4 else None
        if ref_by:
            if db.is_user_agent(int(ref_by)):
                ref_bonus = int(confirmed_amount * 0.10)
                db.update_main_balance(int(ref_by), ref_bonus)
                try: await context.bot.send_message(chat_id=int(ref_by), text=f"🤝 Agent Cash Commission!\n\n👤 Your referral deposited: {confirmed_amount} ETB\n💰 You earned: {ref_bonus} ETB (10% Cash)")
                except: pass
            else:
                ref_bonus = int(confirmed_amount * 0.10)
                db.update_play_balance(int(ref_by), ref_bonus)
                try: await context.bot.send_message(chat_id=int(ref_by), text=f"🎉 Referral Deposit Bonus!\n\n👤 Your referral deposited: {confirmed_amount} ETB\n💰 You earned: {ref_bonus} ETB (10%)")
                except: pass

        user_state.pop(user_id, None)
        user_state.pop(f"{user_id}_amount", None)
        user_state.pop(f"{user_id}_method", None)

        await update.message.reply_text(
            t('deposit_success', lang, method=method, amount=confirmed_amount, bonus=bonus, total=total, new_balance=new_balance),
            reply_markup=get_main_menu(lang)
        )
        return

# --------------------------
# CALLBACK HANDLER (Inline Menus)
# --------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    first_name = query.from_user.first_name or ''
    
    if first_name and db.user_exists(user_id):
        db.update_user_name(user_id, first_name)

    if data in ["lang_am", "lang_en"]:
        lang = 'am' if data == "lang_am" else 'en'
        context.user_data["lang"] = lang
        if db.user_exists(user_id):
            db.set_user_language(user_id, lang)
            await query.message.edit_text(t('lang_changed', lang))
            await context.bot.send_message(chat_id=user_id, text=t('welcome_back', lang), reply_markup=get_main_menu(lang))
        else:
            button_text = t('share_phone_btn', lang)
            button = KeyboardButton(button_text, request_contact=True)
            keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
            await query.message.edit_text(t('select_language'))
            await context.bot.send_message(chat_id=user_id, text=t('welcome_new', lang), reply_markup=keyboard)
        return

    lang = db.get_user_language(user_id) if db.user_exists(user_id) else context.user_data.get("lang", 'am')

    if data == "menu_open_game":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Play Bingo Now", web_app=WebAppInfo(url=MINI_APP_URL))]])
        await query.message.reply_text("🎮 Tap below to open:", reply_markup=keyboard)
    elif data == "menu_balance":
        main = db.get_main_balance(user_id)
        play = db.get_play_balance(user_id)
        await query.message.reply_text(t('balance_msg', lang, main=main, play=play))
    # ... [ADD OTHER CALLBACK HANDLERS LIKE menu_deposit, menu_withdraw HERE] ...

# --------------------------
# COMMAND SHORTCUTS
# --------------------------
async def cmd_play(update, context): await handle_text(update, context, custom_text="🎮 Open Game")
async def cmd_deposit(update, context): await handle_text(update, context, custom_text="💳 Deposit")
async def cmd_balance(update, context): await handle_text(update, context, custom_text="💰 Balance")
# ... add the rest of your shortcut commands here ...

# ==========================
# APP SETUP & START
# ==========================
builder = ApplicationBuilder().token(TOKEN).connect_timeout(60.0).read_timeout(60.0).write_timeout(60.0).pool_timeout(60.0)
app = builder.build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lang", change_lang)) # Ensure change_lang is defined as in your old file
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)) # Ensure this is defined
app.add_handler(MessageHandler(filters.CONTACT, get_contact))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# --------------------------
# CONNECT MODULES & RUN
# --------------------------
# 1. Register the API Blueprint into the Flask App
flask_app.register_blueprint(api_bp)

# 2. Start Flask/SocketIO in a background thread
flask_thread = threading.Thread(target=run_socket_server, daemon=True)
flask_thread.start()

print("✅ Modular Bot is running with SocketIO + API + MongoDB Cloud...")
app.run_polling()
