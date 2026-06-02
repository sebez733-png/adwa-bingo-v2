import time
import random
import threading
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from game_engine import BingoGame  # Import our secure Brain!

# --------------------------
# FLASK & SOCKET SETUP
# --------------------------
flask_app = Flask(__name__)
CORS(flask_app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode='threading')

# --------------------------
# GAME STATE MANAGER
# --------------------------
# We manage the rooms securely here
games = {
    '10': BingoGame(room='10'),
    '20': BingoGame(room='20')
}

# --------------------------
# SOCKET EVENTS
# --------------------------

@socketio.on('connect')
def on_connect():
    print(f'🔌 Client connected: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    print(f'🔌 Client disconnected: {request.sid}')

@socketio.on('join_room')
def on_join_room(data):
    room = data.get('room', '10')
    socket_room = f'bingo_room_{room}'
    join_room(socket_room)
    print(f'👤 Player joined room: {socket_room}')

@socketio.on('leave_room')
def on_leave_room(data):
    room = data.get('room', '10')
    socket_room = f'bingo_room_{room}'
    leave_room(socket_room)

@socketio.on('player_ready')
def on_player_ready(data):
    """
    SECURE CARD GENERATION:
    When player pays and is ready, the server generates the cards and sends them back.
    The frontend can no longer fake the cards!
    """
    room = data.get('room', '10')
    user_id = data.get('user_id')
    name = data.get('name', 'Player')
    num_cards = len(data.get('cards', [1])) # Frontend tells us how many cards they bought
    
    game = games.get(room)
    if not game: return

    # Generate secure cards on the server
    secure_cards = []
    for _ in range(num_cards):
        secure_cards.append(game.generate_card())
    
    # Save cards to the server memory (tied to user_id)
    game.player_cards[user_id] = secure_cards

    # Send the secure cards back to the player's frontend so they can see them
    emit('secure_cards_assigned', {
        'user_id': user_id,
        'cards': secure_cards
    })

    # Tell the room a player joined
    total_players = len(game.player_cards)
    emit('player_joined', {
        'room': room,
        'total_players': total_players,
        'player_name': name,
    }, room=f'bingo_room_{room}')


@socketio.on('declare_winner')
def on_declare_winner(data):
    """
    SECURE WIN VERIFICATION:
    When a player claims BINGO, the server checks the math before giving money!
    """
    room = data.get('room', '10')
    user_id = data.get('user_id')
    card_index = data.get('card_index', 0) # Which card are they claiming win on?

    game = games.get(room)
    if not game: return

    # 1. Get the secure card from server memory
    player_secure_cards = game.player_cards.get(user_id, [])
    if card_index >= len(player_secure_cards):
        return # Invalid card index (possible hack attempt)

    claimed_card = player_secure_cards[card_index]

    # 2. Verify the win using our Game Engine Brain!
    is_valid_win = game.verify_win(claimed_card)

    if is_valid_win:
        print(f"✅ VALID WIN by User {user_id} in Room {room}!")
        # TODO: We will call db.update_main_balance() here later to give them their money!
        
        # Tell everyone we have a winner
        emit('winner_found', {
            'room': room,
            'user_id': user_id,
            'winner_name': data.get('name', 'Player'),
            'card_num': data.get('card_num', '—'),
            'prize': 100, # We will calculate real prize later based on db
        }, room=f'bingo_room_{room}')
    else:
        print(f"❌ INVALID WIN CLAIM by User {user_id} in Room {room}. Possible hack attempt.")
        # Optionally emit an error back to the cheater
        emit('invalid_win_claim', {'reason': 'Card does not match called numbers'}, room=request.sid)


# --------------------------
# ADMIN EVENTS
# --------------------------
@socketio.on('admin_pause_game')
def on_admin_pause_game(data):
    room = data.get('room', '10')
    game = games.get(room)
    if game:
        game.running = not game.running
        emit('game_paused', {'room': room, 'paused': not game.running}, room=f'bingo_room_{room}')

@socketio.on('admin_cancel_game')
def on_admin_cancel_game(data):
    room = data.get('room', '10')
    # Reset the game securely
    games[room] = BingoGame(room=room)
    emit('game_cancelled', {'room': room, 'reason': 'admin_cancelled'}, room=f'bingo_room_{room}')


# --------------------------
# AUTO CALL LOOP (The Ball Dropper)
# --------------------------
def auto_call_loop():
    CALL_INTERVAL = 3 # Seconds between ball drops
    while True:
        time.sleep(CALL_INTERVAL)
        for room_id, game in games.items():
            if game.running and len(game.called_numbers) < 75:
                # Call the next ball from the secure Game Engine
                number = game.call_number()
                if number:
                    socketio.emit('ball_called', {
                        'room': room_id,
                        'number': number
                    }, room=f'bingo_room_{room_id}')

# Start the auto-caller in a background thread
call_thread = threading.Thread(target=auto_call_loop, daemon=True)
call_thread.start()


# --------------------------
# RUN SERVER
# --------------------------
def run_socket_server():
    print("🔌 Socket Server starting on port 5000...")
    socketio.run(flask_app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

# This allows us to run this file directly for testing
if __name__ == '__main__':
    run_socket_server()
