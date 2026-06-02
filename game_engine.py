import random

class BingoGame:
    def __init__(self, room):
        self.room = room
        self.called_numbers = set() # Keeps track of numbers drawn (1-75)
        self.current_number = None
        self.game_id = None
        self.running = False
        
        # This will store the cards securely on the server!
        # Format: { user_id: [card1, card2] }
        self.player_cards = {}

    def generate_card(self):
        """
        Securely generates a 5x5 Bingo card on the server.
        B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
        Center (index 12) is a FREE space (represented as 0).
        """
        card = [0] * 25
        ranges = [
            range(1, 16),  # B
            range(16, 31), # I
            range(31, 46), # N
            range(46, 61), # G
            range(61, 76)  # O
        ]
        
        for col, num_range in enumerate(ranges):
            # Pick 5 unique random numbers for this column
            column_numbers = random.sample(num_range, 5)
            for row in range(5):
                index = row * 5 + col
                card[index] = column_numbers[row]
        
        # Set the center FREE space to 0 (since 0 is never drawn in Bingo)
        card[12] = 0 
        return card

    def call_number(self):
        """
        Randomly selects the next number (1-75) that hasn't been called yet.
        """
        available = [n for n in range(1, 76) if n not in self.called_numbers]
        if not available:
            return None # All 75 numbers have been called
        
        number = random.choice(available)
        self.called_numbers.add(number)
        self.current_number = number
        return number

    def verify_win(self, card):
        """
        SECURE WIN VERIFICATION.
        Checks if a given card has a valid winning pattern 
        based ONLY on the numbers the server has called.
        """
        # A number is marked if it's in called_numbers OR if it's the FREE space (0)
        def is_marked(num):
            return num == 0 or num in self.called_numbers

        # 1. Check Rows
        for r in range(5):
            if all(is_marked(card[r * 5 + c]) for c in range(5)):
                return True

        # 2. Check Columns
        for c in range(5):
            if all(is_marked(card[r * 5 + c]) for r in range(5)):
                return True

        # 3. Check Diagonals
        if all(is_marked(card[i * 5 + i]) for i in range(5)):
            return True
        if all(is_marked(card[i * 5 + (4 - i)]) for i in range(5)):
            return True

        # 4. Check Four Corners
        if is_marked(card[0]) and is_marked(card[4]) and is_marked(card[20]) and is_marked(card[24]):
            return True

        return False
