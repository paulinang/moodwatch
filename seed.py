from model import connect_to_db, db, User, Prescription, Drug, Day, Event, EventDay
from server import app


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

    chicken = User(username='not_chicken', password='am_duck', email='actually@goose.com')
    duck = User(username='not_duck', password='am_chicken', email='actually@mongoose.com')
    turkey = User(username='not_turkey', password='am_vulture', email='actually@catgoose.com')

    db.session.add(chicken)
    db.session.add(duck)
    db.session.add(turkey)
    db.session.commit()


def load_days():
    """ Add days to days table"""

    print "Days"

    Day.query.delete()

    for i in range(1, 30):
        day = Day(user_id=1, date='2016-10-%s' % i, overall_mood=5)
        db.session.add(day)

    db.session.commit()



if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_drugs()
    load_users()
    load_days()
