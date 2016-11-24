from model import User
import numpy as np
import pandas as pd


def get_rolling_mean(user_id, r_window=10):
    """ Gets rolling mean of mood rating for a user"""
    user = User.query.get(user_id)
    days = user.days
    # import pdb; pdb.set_trace()
    overall_moods = [day.overall_mood for day in days]
    overall_moods.reverse()
    dates = [day.date for day in days]
    dates.reverse()

    moods = pd.Series(overall_moods)
    r = moods.rolling(window=r_window)
    r_mean_moods = r.mean()
    r_mean_mood_list = [mean for mean in r_mean_moods[(r_window-1):]]

    while (np.isnan(r_mean_mood_list[-1])):
        del r_mean_mood_list[-1]
        del dates[-1]

    mood_list = list(moods[:(r_window-1)]) + r_mean_mood_list
    mood_list = [int(mood) for mood in mood_list]

    smooth = pd.Series(mood_list, index=dates)

    return smooth
