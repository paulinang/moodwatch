# from model import db, connect_to_db, User, Day
# from server import app
# from datetime import datetime


# def is_today_logged(user_id):
#     """Checks if today is logged for this user"""

#     today = datetime.today().date()
#     print today
#     logged_days = db.session.query(Day.date).filter(Day.user_id == user_id)
#     username = db.session.query(User.username).filter(User.user_id == 1).one()
#     if not today in logged_days:
#         with open('python_cron_test.txt', 'w') as f:
#             f.write('%s has not logged today: %s' % (username, today))


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    # connect_to_db(app)
    # print "Connected to DB."

    with open('python_cron_test.txt', 'a') as f:
        f.write('Python file ran!')
    # is_today_logged(1)
