from model import connect_to_db, db, User, Prescription, Drug, Day, Event, EventDay, Professional, Contract
from server import app
from datetime import datetime, timedelta
from random import choice
from math import sin
from bcrypt import hashpw, gensalt


def load_drugs():
    """ Add drugs to drug table"""

    print "Drugs"

    Drug.query.delete()

    with open('Product.txt') as products:
        drugs = []
        for product in products:
            drug_name, active_ingredients = product.rstrip().split('\t')[7:]
            drugs.append((drug_name, active_ingredients))

    for drug in set(drugs):
        drug_record = Drug(drug_name=drug[0], active_ingredients=drug[1])
        db.session.add(drug_record)

    db.session.commit()


def load_users():
    """ Add users to user table"""

    print "Users"

    User.query.delete()

    loki = User(username='loki',
                password=hashpw('fenrir_hel_jormungand', gensalt()),
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


def load_days():
    """ Add days to days table"""

    print "Days"

    Day.query.delete()

    # create a list of numbers to randomly choose from
    # steps up/down from overall_mood to create min/max
    MOOD_STEP = range(5, 30, 5)

    # Create a list of dates starting from 10 days ago to 300 days ago
    dates = [datetime.today().date() - timedelta(days=x) for x in range(10, 301)]
    # Create a list of overall_moods based on a sine wave limited to (-15,15)
    # Corresponds to amount of dates (290)
    overall_moods = [int(15 * sin(x * 0.1)) for x in range(0, 291)]

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


if __name__ == "__main__":
    connect_to_db(app, 'projectdb')

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_drugs()
    load_users()
    load_professionals()
    load_contracts()
    load_days()
    load_events()
