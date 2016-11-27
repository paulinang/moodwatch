from model import User
# import numpy as np
import pandas as pd


def analyze_moods(user_id):
    r_window = 14
    user = User.query.get(user_id)
    days = user.days
    overall_moods = [day.overall_mood for day in days]
    moods = pd.Series(overall_moods)
    roll = moods.rolling(window=r_window)
    roll_mean = roll.mean()
    roll_std = roll.std()

    return [roll_mean, roll_std]
