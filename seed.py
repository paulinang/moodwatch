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


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_drugs()
