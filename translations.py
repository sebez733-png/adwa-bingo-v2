# --------------------------
# TRANSLATION DICTIONARY
# --------------------------
TEXTS = {
    'select_language': {
        'am': "👇 ቋንቋ ይምረጡ / Please select your language",
        'en': "👇 Please select your language"
    },
    'welcome_new': {
        'am': (
            "🎉 እንኳን ወደ አድዋ Bingo በደህና መጡ!\n\n"
            "1️⃣ ከታች ያለውን \"📱 ስልክ ቁጥር ያጋሩ\" ይጫኑ\n"
            "2️⃣ ስልክ ቁጥርዎን ያረጋግጡ\n"
            "3️⃣ ከዚያ በኋላ መጫወት ይጀምሩ! 🚀\n\n"
            "👇 ለመጀመር ስልክ ቁጥርዎን ያጋሩ"
        ),
        'en': (
            "🎉 Welcome to our Adwa Bingo Game!\n\n"
            "1️⃣ Click the button below to share your phone number\n"
            "2️⃣ Verify your number\n"
            "3️⃣ Start playing! 🚀\n\n"
            "👇 Share your phone number to begin:"
        )
    },
    'share_phone_btn': {
        'am': "📱 ስልክ ቁጥር ያጋሩ",
        'en': "📱 Share Phone Number"
    },
    'welcome_back': {
        'am': "👋 Welcome back!",
        'en': "👋 Welcome back!"
    },
    'already_registered': {
        'am': (
            "⚠️ እርስዎ ቀድሞ ተመዝግበዋል!\n\n"
            "📱 ስልክ: {phone}\n\n"
            "💰 Main Wallet: {main} ETB\n"
            "🎮 Play Wallet: {play} ETB\n"
            "👥 Referrals: {ref_count}\n\n"
            "👇 Choose an option below:"
        ),
        'en': (
            "⚠️ You are already registered!\n\n"
            "📱 Phone: {phone}\n\n"
            "💰 Main Wallet: {main} ETB\n"
            "🎮 Play Wallet: {play} ETB\n"
            "👥 Referrals: {ref_count}\n\n"
            "👇 Choose an option below:"
        )
    },
    'register_success': {
        'am': (
            "🎉 እንኳን ወደ አድዋ Bingo ቤተሰብ በደህና መጡ!\n\n"
            "✅ ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!\n\n"
            "📱 ስልክ ቁጥር: {phone}\n\n"
            "💰 Main Wallet: {main} ETB\n"
            "🎮 Play Wallet: {play} ETB\n\n"
            "🎯 አሁን መጫወት ለመጀመር ከታች ያለውን ቁልፍ ይጫኑ!\n"
            "🍀 መልካም እድል!"
        ),
        'en': (
            "🎉 Welcome to the Adwa Bingo Family!\n\n"
            "✅ Registration successful!\n\n"
            "📱 Phone: {phone}\n\n"
            "💰 Main Wallet: {main} ETB\n"
            "🎮 Play Wallet: {play} ETB\n\n"
            "🎯 Click the menu below to start playing!\n"
            "🍀 Good luck!"
        )
    },
    'deposit_prompt': {
        'am': "💳 ምን ያህል ማስገባት ይፈልጋሉ?\n(Enter amount)\n\nMin / ዝቅተኛ: 10 ብር / Birr",
        'en': "💳 How much would you like to deposit?\n(Enter amount)\n\nMin: 10 Birr"
    },
    'withdraw_prompt': {
        'am': (
            "🐝 ማውጣት የሚፈልጉትን መጠን ይፃፉ (ETB):\n\n"
            "🎮 Play Wallet: {play_bal} ETB\n"
            "💰 Main Wallet: {main_bal} ETB\n\n"
            "Min / ዝቅተኛ: 100 ብር"
        ),
        'en': (
            "🐝 Enter withdrawal amount (ETB):\n\n"
            "🎮 Play Wallet: {play_bal} ETB\n"
            "💰 Main Wallet: {main_bal} ETB\n\n"
            "Min: 100 Birr"
        )
    },
    'withdraw_locked': {
        'am': "❌ ማውጣት አይችሉም!\n\n⚠️ ገንዘብ ለማውጣት 50 ብር ማስገባት አለብዎት።\n\n❌ You cannot withdraw. You must deposit at least 50 ETB in total to unlock withdrawals.",
        'en': "❌ Withdrawal locked!\n\n⚠️ You must deposit at least 50 ETB in total to unlock withdrawals."
    },
    'balance_msg': {
        'am': "💰 WALLET BALANCE\n\n💰 Main Wallet: {main} ETB\n🎮 Play Wallet: {play} ETB",
        'en': "💰 WALLET BALANCE\n\n💰 Main Wallet: {main} ETB\n🎮 Play Wallet: {play} ETB"
    },
    'deposit_success': {
        'am': (
            "✅ Deposit Successful\n\n"
            "💰 Method: {method}\n"
            "💰 Sent: {amount}\n"
            "🎁 Bonus: {bonus}\n"
            "📈 Total Added: {total}\n"
            "💰 New Balance: {new_balance} ETB"
        ),
        'en': (
            "✅ Deposit Successful\n\n"
            "💰 Method: {method}\n"
            "💰 Sent: {amount}\n"
            "🎁 Bonus: {bonus}\n"
            "📈 Total Added: {total}\n"
            "💰 New Balance: {new_balance} ETB"
        )
    },
    'lang_changed': {
        'am': "✅ ቋንቋ ወደ አማርኛ ተቀይሯል!",
        'en': "✅ Language changed to English!"
    }
}

# --------------------------
# HELPER FUNCTION
# --------------------------
def t(key, lang='am', **kwargs):
    """
    Gets the translated text for a key.
    If variables like {main} or {phone} are passed, it fills them in.
    """
    # Get the text, default to Amharic if English is missing, default to the key name if both missing
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get('am', key))
    
    # Fill in variables like {phone} or {amount}
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass # Ignore if a variable is missing
            
    return text
