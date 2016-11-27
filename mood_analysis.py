from model import User
import numpy as np
import pandas as pd


def rolling_analysis(user_id, analysis_type='mean', r_window=20):
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
    if analysis_type == 'mean':
        r_moods = r.mean()
    elif analysis_type == 'std':
        r_moods = r.std()
    else:
        rolling_std = moods.rolling(window=5).std()[4:]
        compare_moods = moods[4:]
        comparison = abs(compare_moods-compare_moods.mean()) > (rolling_std)
        outliers_index = comparison[comparison].index
        outliers = [moods[i] for i in outliers_index]
        dates = [dates[i] for i in outliers_index]

        return pd.Series(outliers, index=dates)

    r_mood_list = [mean for mean in r_moods[(r_window-1):]]

    while (np.isnan(r_mood_list[-1])):
        del r_mood_list[-1]
        del dates[-1]

    mood_list = list(moods[:(r_window-1)]) + r_mood_list
    mood_list = [int(mood) for mood in mood_list]

    smooth = pd.Series(mood_list, index=dates)

    return smooth


def find_outliers(user_id, window=5):

    user = User.query.get(user_id)
    days = user.days
    overall_moods = [day.overall_mood for day in days]
    overall_moods.reverse()
    dates = [day.date for day in days]
    dates.reverse()
    moods = pd.Series(overall_moods)
    comparison = abs(moods) > (moods.std() * 2)
    outliers_index = comparison[comparison].index
    outliers = [moods[i] for i in outliers_index]
    dates = [dates[i] for i in outliers_index]

    return pd.Series(outliers, index=dates)
