from model import connect_to_db, db, User, Prescription, Drug, Day, Event, EventDay, Professional, Contract
from server import app
from random import choice
from math import sin
from bcrypt import hashpw, gensalt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone


def load_drugs():
    """ Add drugs to drug table"""

    print "Drugs"

    Drug.query.delete()

    meds = get_meds_from_txt('psych_meds.txt')
    for med in meds:
        drug = Drug(generic_name=med[0], brand_name=med[1], uses=med[2])
        db.session.add(drug)

    db.session.commit()


def load_users():
    """ Add users to user table"""

    print "Users"

    User.query.delete()

    loki = User(username='loki',
                password=hashpw('jormungand', gensalt()),
                email='loki@jotunheim.com')

    tyr = User(username='tyr',
               password=hashpw('fenrirBITme', gensalt()),
               email='tyr@asgard.com')

    heimdall = User(username='heimdall',
                    password=hashpw('Igot9MUMS', gensalt()),
                    email='heimdall@bifrost.com')

    odin = User(username='odin',
                password=hashpw('sleipnirISMYride', gensalt()),
                email='odin@valhalla.com')

    db.session.add(loki)
    db.session.add(tyr)
    db.session.add(heimdall)
    db.session.add(odin)

    db.session.commit()


def load_professionals():
    print 'Professionals'

    Professional.query.delete()

    for i in range(3, 5):
        pro = Professional(user_id=i)
        db.session.add(pro)

    db.session.commit()


def load_contracts():
    print 'Contracts'
    Contract.query.delete()

    heimdallTyr = Contract(pro_id=3, client_id=2, active=True)
    odinTyr = Contract(pro_id=4, client_id=2, active=True)
    odinLoki = Contract(pro_id=4, client_id=1, active=True)

    db.session.add_all([heimdallTyr, odinTyr, odinLoki])
    db.session.commit()


def load_prescriptions():
    print 'Prescriptions'
    Prescription.query.delete()

    med1 = Prescription(client_id=2,
                        pro_id=3,
                        drug_id=4,
                        start_date='2016-09-10',
                        end_date='2016-09-15',
                        instructions='Take 5mg daily')
    med2 = Prescription(client_id=2,
                        pro_id=3,
                        drug_id=4,
                        start_date='2016-09-15',
                        instructions='Take 10mg daily')
    med3 = Prescription(client_id=2,
                        pro_id=4,
                        drug_id=1,
                        start_date='2016-11-10',
                        instructions='Take 50mg 2x a day (morning and night)')
    med4 = Prescription(client_id=1,
                        pro_id=4,
                        drug_id=6,
                        start_date='2016-01-17',
                        instructions='Take 100mg daily, before bed')
    db.session.add_all([med1, med2, med3, med4])
    db.session.commit()


def load_days():
    """ Add days to days table"""

    print "Days"

    Day.query.delete()

    dates, overall_moods = rand_day_moods()

    # DAY_STEPS = range(1, 16)
    # EXTREME_MOODS = [49, 47, 36, -38, -42, -43, -44, - 45, -48]
    # day_step = choice(DAY_STEPS)

    # give tyr random moods
    for i, date in enumerate(dates):
        # if i == day_step:
        #     overall_mood = choice(EXTREME_MOODS)
        #     day_step += choice(DAY_STEPS)
        # else:
        overall_mood = int(overall_moods[i])
        day = Day(user_id=2,
                  date=date,
                  overall_mood=overall_mood)
        db.session.add(day)

    # create a list of numbers to randomly choose from
    # steps up/down from overall_mood to create min/max
    MOOD_STEP = range(5, 30, 5)

    overall_moods = [int(15 * sin(x * 0.1)) for x in range(0, 1001)]

    # give loki moods based on sine wave
    for i, date in enumerate(dates):
        overall_mood = overall_moods[i]
        day = Day(user_id=1,
                  date=date,
                  overall_mood=overall_mood,
                  max_mood=overall_mood + choice(MOOD_STEP),
                  min_mood=overall_mood - choice(MOOD_STEP))
        db.session.add(day)
    db.session.commit()


def load_events():
    """ Add event to events table"""

    print "Events"

    Event.query.delete()

    user = User.query.get(1)
    nums = [1, -1, -2, 2]
    for x, i in enumerate(range(0, len(user.days), 3)):
        day = user.days[i]
        event = Event(user_id=1,
                      event_name='event %s' % x,
                      overall_mood=(day.overall_mood + choice(nums)))
        db.session.add(event)
        db.session.commit()
        event_day = EventDay(event_id=event.event_id, day_id=day.day_id)
        db.session.add(event_day)
        db.session.commit()
#     start_date = datetime.strptime('2016-10-05', '%Y-%m-%d').date()
#     end_date = datetime.strptime('2016-10-20', '%Y-%m-%d').date()
#     event.associate_days(start_date, end_date)


########################################################
################ HELPER FUNCTIONS ######################
########################################################


def get_meds_from_txt(txt_file):
    """ Prepares a list of meds from txt file to be made into 'drug' objects

    Meant to process a txt file created using pdftotext command-line utility
    on pdf (http://www.namihelps.org/assets/PDFs/fact-sheets/Medications/Commonly-Psyc-Medications.pdf)
    """

    with open(txt_file, 'r') as med_txt:
        # ultimately want a master list of drugs
        drugs = []
        # each drug represented by a list [generic, brand, uses]
        drug = []

        drug_data = {}
        i = 0
        labels = ['GENERIC', 'BRAND', 'USES']
        category = ''
        for line in med_txt:
            line = line.strip()
            if line in labels:
                category = line
            elif category:
                drug_data.setdefault(category, []).append(line)
            elif i < 3:
                drug.append(line)
                i += 1
            else:
                drugs.append(drug)
                drug = [line]
                i = 1

        for i in range(0, len(drug_data['GENERIC'])):
            drug = [drug_data['GENERIC'][i], drug_data['BRAND'][i], drug_data['USES'][i]]
            drugs.append(drug)

    return drugs


def rand_day_moods(num_days=1000, tz='US/Pacific'):
    """ Creates a list of days with random moods """

    ca_tz = timezone(tz)
    most_recent = datetime.now(ca_tz).date() - timedelta(days=1)
    first_day = most_recent - timedelta(days=num_days-1)

    random_moods = pd.Series((np.random.rand(num_days) * 20) - (20/2))
    offsets = [(x * .03 - 15) for x in range(1, 1001)]
    # for i in range(985, 1000):
    #     offsets[i] = 30

    # for x, i in enumerate(range(954, 985)):
    #     offsets[i] = x
    # weird_moods = random_moods + offsets
    sine_nums = [(int(5) * sin(x * 0.1)) for x in range(1, 1001)]
    weird_moods = random_moods + sine_nums + offsets
    mood_list = list(weird_moods)

    pd_dates = pd.date_range(first_day, periods=num_days)
    dates_str = [datetime.strftime(date, '%Y-%m-%d') for date in pd_dates]

    # moods = pd.Series(random_moods)
    # r_window = 60
    # r = moods.rolling(window=r_window)
    # r_mean_moods = r.mean()
    # r_mean_mood_list = [int(mean) for mean in r_mean_moods[(r_window-1):]]
    # mood_list = list(moods[:(r_window-1)]) + r_mean_mood_list

    return (dates_str, mood_list)


if __name__ == "__main__":
    connect_to_db(app, 'asgard_db')

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_drugs()
    load_users()
    load_professionals()
    load_contracts()
    load_prescriptions()
    load_days()
    load_events()
