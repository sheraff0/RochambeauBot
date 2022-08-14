from random import randint

MAX_ATTEMPTS_SCORE = 3
FIGURES_LIST = ["КАМЕНЬ", "НОЖНИЦЫ", "БУМАГА"]
MATCH_MAP = {
    "КАМЕНЬ": {
        "КАМЕНЬ": 0,
        "НОЖНИЦЫ": 1,
        "БУМАГА": -1,
    },
    "НОЖНИЦЫ": {
        "КАМЕНЬ": -1,
        "НОЖНИЦЫ": 0,
        "БУМАГА": 1,
    },
    "БУМАГА": {
        "КАМЕНЬ": 1,
        "НОЖНИЦЫ": -1,
        "БУМАГА": 0,
    },
}


class Roshambo:
    def __init__(self, rounds=3):
        self.rounds = rounds
        self.rounds_count = 0
        self.attempts_score, self.rounds_score = [[0, 0]] * 2
        self.attempt_match, self.round_winner, self.game_winner = [None] * 3
        self.player_move, self.opponent_move = [None] * 2

    def get_figure(self):
        idx = randint(0, len(FIGURES_LIST) - 1)
        return FIGURES_LIST[idx]

    def get_match(self, player_move, opponent_move):
        match = MATCH_MAP[player_move][opponent_move]
        self.attempt_match = match
        return match

    def update_attempts_score(self, match):
        self.attempts_score = [x + max(
            0, (-1) ** i * match) for i, x in enumerate(self.attempts_score)]

    def update_rounds_score(self):
        self.rounds_count += 1
        self.round_winner = self.attempts_score.index(MAX_ATTEMPTS_SCORE)
        self.rounds_score[self.round_winner] += 1
        if max(self.rounds_score) == self.rounds:
            self.game_winner = self.rounds_score.index(self.rounds)
            return
        self.attempts_score = [0, 0]  # reset if the game goes on

    def update_score(self, match):
        self.update_attempts_score(match)
        if max(self.attempts_score) == MAX_ATTEMPTS_SCORE:
            self.update_rounds_score()

    def next_move(self, player_move):
        self.player_move = player_move
        if self.game_winner or player_move not in FIGURES_LIST:
            return
        self.round_winner = None  # reset as the game goes on
        self.opponent_move = self.get_figure()
        match = self.get_match(player_move, self.opponent_move)
        self.update_score(match)
