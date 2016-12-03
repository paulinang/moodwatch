from server import app
from flask_mail import Mail, Message
import os

sender_email = os.environ.get('FLASK_MAIL_SENDER_EMAIL')
sender_password = os.environ.get('FLASK_MAIL_SENDER_PASSWORD')

app.config.update(dict(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=sender_email,
    MAIL_PASSWORD=sender_password))

mail = Mail(app)

with app.app_context():
        # keeps connection to email host alive until messages are all sent
        # good for external processes like command-line scripts or cronjobs
        with mail.connect() as conn:

            msg = Message('Testing mail',
                          body='Hey Hey',
                          sender=sender_email,
                          recipients=['fake@email.com'])

            conn.send(msg)
