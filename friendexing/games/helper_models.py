class PlayerScore:
    def __init__(self, name, score, player_id):
        self.name = name
        self.score = score
        self.player_id = player_id

    def serialize_as_json(self):
        return {
            'name': self.name,
            'score': self.score,
        }
