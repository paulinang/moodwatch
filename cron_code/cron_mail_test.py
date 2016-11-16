from server import app, mail
from flask_mail import Message
from model import db, connect_to_db, User, Day
from datetime import datetime


def is_today_logged(user_id):
    """Checks if today is logged for this user"""

    today = datetime.today().date()
    logged_days = db.session.query(Day.date).filter(Day.user_id == user_id)
    username = db.session.query(User.username).filter(User.user_id == 1).one()
    return '%s has logged today (%s) : %s' % (username, today, today in logged_days)


def send_test_mail():
    """Sends mail to myself"""

    body = is_today_logged(1)

    # allows usage of app outside server.py
    with app.app_context():
        # keeps connection to email host alive until messages are all sent
        # good for external processes like command-line scripts or cronjobs
        with mail.connect() as conn:

            msg = Message('Testing cron mail',
                          body=body,
                          sender='qwnpng@gmail.com',
                          recipients=['qwnpng@gmail.com'])

            conn.send(msg)


if __name__ == "__main__":
    connect_to_db(app)
    send_test_mail()
