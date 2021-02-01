from django import forms

from games.models import Game, Player


class PlayerForm(forms.Form):
    name = forms.CharField(max_length=60)

    def create_player(self):
        return Player(**self.cleaned_data)


class GameForm(PlayerForm):
    total_time_to_guess = forms.IntegerField(min_value=1, max_value=300)
    should_randomize_fields = forms.BooleanField(required=False)

    def create_game(self):
        return Game(**self.cleaned_data)
