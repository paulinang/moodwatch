from model import db, connect_to_db, User, Day
from server import app

if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    connect_to_db(app)
    # print "Connected to DB."
    user = User.query.get(1).username
    with open('cron_db.txt', 'a') as f:
        f.write(user)
    # is_today_logged(1)
