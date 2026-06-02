from flask import Blueprint, request, jsonify
import db

# --------------------------
# BLUEPRINT SETUP
# --------------------------
# This creates a modular Flask Blueprint. All routes here will start with /api/
api_bp = Blueprint('api', __name__)

# Helper to handle CORS and OPTIONS requests easily
def options_response():
    resp = jsonify({'success': True})
    resp.headers['ngrok-skip-browser-warning'] = 'true'
    return resp

@api_bp.after_request
def add_headers(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response


# ==========================================
# USER & WALLET API ROUTES
# ==========================================

@api_bp.route('/api/ping', methods=['GET', 'OPTIONS'])
def api_ping():
    if request.method == 'OPTIONS': return options_response()
    return jsonify({'success': True, 'message': 'API is running'})

@api_bp.route('/api/update_name', methods=['POST', 'OPTIONS'])
def api_update_name():
    if request.method == 'OPTIONS': return options_response()
    data = request.json or {}
    user_id = data.get('user_id')
    first_name = data.get('first_name', '')
    if not user_id or not first_name:
        return jsonify({'success': False, 'error': 'user_id and first_name required'}), 400
    try: user_id = int(user_id)
    except: return jsonify({'success': False, 'error': 'invalid user_id'}), 400
    
    if db.user_exists(user_id):
        db.update_user_name(user_id, first_name)
    return jsonify({'success': True})


@api_bp.route('/api/balance', methods=['GET', 'OPTIONS'])
def api_balance():
    user_id = request.args.get('user_id', type=int)
    if not user_id or not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404

    user_data = db.get_user_full(user_id)
    return jsonify({
        'success': True,
        'main_balance': db.get_main_balance(user_id),
        'play_balance': db.get_play_balance(user_id),
        'is_banned': user_data.get('status') == 'banned',
        'is_frozen': user_data.get('status') == 'frozen',
        'is_vip': user_data.get('is_vip', 0) == 1
    })


@api_bp.route('/api/bet', methods=['POST', 'OPTIONS'])
def api_bet():
    if request.method == 'OPTIONS': return options_response()
    data = request.json or {}
    user_id = data.get('user_id')
    amount = data.get('amount', 0)
    
    try: user_id = int(user_id)
    except: return jsonify({'success': False, 'error': 'invalid user_id'}), 400

    if not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404

    user_data = db.get_user_full(user_id)
    if user_data.get('status') in ['banned', 'frozen']:
        return jsonify({'success': False, 'error': f'Account {user_data.get("status")}'}), 403

    success = db.deduct_bet_smart(user_id, amount)
    if not success:
        return jsonify({'success': False, 'error': 'Insufficient balance'}), 400

    db.add_transaction(user_id, 'bingo_bet', amount)
    return jsonify({
        'success': True,
        'main_balance': db.get_main_balance(user_id),
        'play_balance': db.get_play_balance(user_id)
    })


@api_bp.route('/api/win', methods=['POST', 'OPTIONS'])
def api_win():
    if request.method == 'OPTIONS': return options_response()
    data = request.json or {}
    user_id = data.get('user_id')
    amount = data.get('amount', 0)
    game_id = data.get('game_id', '')

    try: user_id = int(user_id)
    except: return jsonify({'success': False, 'error': 'invalid user_id'}), 400

    if not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Add money to Main Wallet
    db.update_main_balance(user_id, amount)
    db.add_transaction(user_id, 'bingo_win', amount)
    db.complete_game_session(user_id, game_id, result=f'+{amount} Br', prize=amount)
    
    return jsonify({
        'success': True,
        'main_balance': db.get_main_balance(user_id),
        'play_balance': db.get_play_balance(user_id)
    })


@api_bp.route('/api/game_played', methods=['POST', 'OPTIONS'])
def api_game_played():
    if request.method == 'OPTIONS': return options_response()
    data = request.json or {}
    user_id = data.get('user_id')
    game_id = data.get('game_id', '')
    cards = data.get('cards', [])
    entry = data.get('stake', 10)
    
    try: user_id = int(user_id)
    except: return jsonify({'success': False, 'error': 'invalid user_id'}), 400

    if not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    db.add_game_session(user_id, game_id, cards, entry)
    return jsonify({'success': True})


# ==========================================
# PROFILE & LEADERBOARD API ROUTES
# ==========================================

@api_bp.route('/api/profile_stats', methods=['GET', 'OPTIONS'])
def api_profile_stats():
    user_id = request.args.get('user_id', type=int)
    if not user_id or not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404

    user_data = db.get_user_full(user_id)
    return jsonify({
        'success': True,
        'games_played': db.get_games_played_count(user_id),
        'games_won': db.get_games_won_count(user_id),
        'total_won': db.get_total_won(user_id),
        'invited': db.get_referral_count(user_id),
        'is_vip': user_data.get('is_vip', 0) == 1
    })

@api_bp.route('/api/transactions', methods=['GET', 'OPTIONS'])
def api_transactions():
    user_id = request.args.get('user_id', type=int)
    if not user_id or not db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    rows = db.get_all_transactions(user_id, limit=20)
    txs = [{'type': r[0], 'amount': r[1], 'status': r[2], 'time': r[3]} for r in rows]
    return jsonify({'success': True, 'transactions': txs})

@api_bp.route('/api/top_winners', methods=['GET', 'OPTIONS'])
def api_top_winners():
    period = request.args.get('period', 'week')
    category = request.args.get('category', 'deposit')
    
    if category == 'deposit': rows = db.get_top_by_deposit(period, 30)
    elif category == 'invite': rows = db.get_top_by_invitations(period, 30)
    elif category == 'wins': rows = db.get_top_by_wins(period, 30)
    else: rows = db.get_top_by_games(period, 30)
        
    winners = [{'name': r[1] or 'User', 'value': r[2]} for r in rows]
    return jsonify({'success': True, 'winners': winners})

# Note: You can add the /api/admin/... routes here later using the exact same Blueprint pattern!
