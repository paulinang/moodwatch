from model import connect_to_db, db, User, Prescription, Drug, Day, Event, EventDay
from server import app
from datetime import datetime


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

    for i in range(1, 5):
        user = User(username='user%s' % i,
                    password='password',
                    email='user%s@email.com' % i)
        db.session.add(user)

    db.session.commit()


def load_days():
    """ Add days to days table"""

    print "Days"

    Day.query.delete()

    for i in range(1, 30):
        day = Day(user_id=1,
                  date='2016-10-%s' % i,
                  overall_mood=5,
                  max_mood=10,
                  min_mood=0)
        db.session.add(day)

    db.session.commit()


def load_events():
    """ Add event to events table"""

    print "Events"

    Event.query.delete()

    event = Event(user_id=1,
                  event_name='event1',
                  overall_mood=2)
    db.session.add(event)
    db.session.commit()

    start_date = datetime.strptime('2016-10-05', '%Y-%m-%d').date()
    end_date = datetime.strptime('2016-10-20', '%Y-%m-%d').date()
    event.associate_days(start_date, end_date)


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_drugs()
    load_users()
    load_days()
    load_events()
