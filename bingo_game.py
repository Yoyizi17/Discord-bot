import random

class Player:
    def __init__(self, user_id):
        self.user_id = user_id
        self.card = []
        self.marked = []

class Game:
    def __init__(self, name, creator_id):
        self.name = name
        self.creator_id = creator_id
        self.status = "preparing"
        self.words = []
        self.players = {}
        self.dimension = 0

    def add_player(self, user_id):
        if user_id not in self.players:
            self.players[user_id] = Player(user_id)
            self.generate_player_card(user_id)

    def generate_player_card(self, user_id):
        if self.dimension > 0:
            player = self.players[user_id]
            shuffled_words = random.sample(self.words, len(self.words))
            player.card = [shuffled_words[i:i+self.dimension] for i in range(0, len(shuffled_words), self.dimension)]
            player.marked = [[False for _ in range(self.dimension)] for _ in range(self.dimension)]

games = {}