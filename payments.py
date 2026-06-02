import re
from datetime import datetime
from db import db as mongo_db  # We need this to check the telebirr_transactions collection

# --------------------------
# CONFIG
# --------------------------
MERCHANT_PHONE = "0998480054"

def get_merchant_phone_partials():
    p = MERCHANT_PHONE
    local_partial = p[:4] + "****" + p[-2:]
    intl = "251" + p[1:]
    intl_partial = intl[:4] + "****" + intl[-4:]
    return [local_partial, intl_partial]

# --------------------------
# TRANSACTION HELPERS
# --------------------------
def is_transaction_used(transaction_id: str) -> bool:
    """Checks if a Telebirr transaction ID was already used to prevent double-depositing."""
    return mongo_db["telebirr_transactions"].find_one({"transaction_id": transaction_id}) is not None

def mark_transaction_used(transaction_id: str, user_id: int, amount: float):
    """Saves the transaction ID so it can't be used again."""
    mongo_db["telebirr_transactions"].update_one(
        {"transaction_id": transaction_id},
        {"$setOnInsert": {
            "transaction_id": transaction_id, 
            "user_id": user_id, 
            "amount": amount, 
            "created_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }},
        upsert=True
    )

# --------------------------
# SMS VERIFICATION LOGIC
# --------------------------
def verify_telebirr_sms(sms_text: str, expected_amount: int) -> dict:
    """
    Pure logic to verify a Telebirr SMS.
    Returns a dictionary with 'valid' (bool) and 'reason' (string).
    """
    sms_text = sms_text.strip()
    
    # 1. Check if it looks like a Telebirr transfer SMS
    if "transferred ETB" not in sms_text:
        return {
            'valid': False,
            'reason': (
                "❌ SMS format not recognized.\n\n"
                "Please paste the *exact* SMS you received from Telebirr after sending money.\n\n"
                "Example:\n"
                "_Dear Habtamu You have transferred ETB 100.00 to ..._"
            )
        }
    
    # 2. Extract Amount
    amount_match = re.search(r'transferred ETB\s*([\d,]+\.?\d*)', sms_text)
    if not amount_match:
        return {'valid': False, 'reason': "❌ Could not read amount from SMS. Please paste the full SMS."}
    amount = float(amount_match.group(1).replace(',', ''))
    
    # 3. Extract Transaction ID
    txn_match = re.search(r'transaction number is\s*([A-Z0-9]+)', sms_text)
    if not txn_match:
        return {'valid': False, 'reason': "❌ Could not find transaction number in SMS. Please paste the full SMS."}
    transaction_id = txn_match.group(1).strip()
    
    # 4. Verify Recipient Phone
    phone_match = re.search(r'\((\d{4}\*+\d{2,4})\)', sms_text)
    if phone_match:
        receiver_partial = phone_match.group(1)
        allowed_partials = get_merchant_phone_partials()
        if receiver_partial not in allowed_partials:
            return {
                'valid': False,
                'reason': (
                    f"❌ Wrong recipient!\n\n"
                    f"Money was not sent to our account.\n"
                    f"Please send to: `{MERCHANT_PHONE}`"
                )
            }
    
    # 5. Extract Date/Time
    date_match = re.search(r'on\s*(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2}:\d{2})', sms_text)
    date_str = date_match.group(1) if date_match else ''
    time_str = date_match.group(2) if date_match else ''
    
    # 6. Check if Amount matches what user claimed
    if abs(amount - expected_amount) > 1:
        return {
            'valid': False,
            'reason': (
                f"❌ Amount mismatch!\n\n"
                f"You said you'd send *{expected_amount} ETB* "
                f"but SMS shows *{amount:.2f} ETB*.\n\n"
                f"Please make sure you send the exact amount."
            )
        }
        
    # 7. Check if Transaction ID was already used (Anti-Fraud)
    if is_transaction_used(transaction_id):
        return {
            'valid': False,
            'reason': (
                f"❌ Transaction already used!\n\n"
                f"Transaction `{transaction_id}` was already submitted.\n"
                f"Each SMS can only be used once."
            )
        }
        
    # If all checks pass!
    return {
        'valid': True,
        'reason': 'OK',
        'transaction_id': transaction_id,
        'amount': amount,
        'date': date_str,
        'time': time_str,
    }
