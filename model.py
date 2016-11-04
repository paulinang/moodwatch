"""Models and database functions for Hackbright project.
    Layout taken from Ratings lab exercise"""

from flask_sqlalchemy import SQLAlchemy

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User accounts"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        """Gives username and email of record"""

        return "<User user_id=%s username=%s email=%s>" % (self.user_id, self.username, self.email)

    def group_prescriptions_by_drug(self):
        """Returns a dictionary {'drug_name': [list of prescription objects]}"""

        prescription_dict = {}
        for prescription in self.prescriptions:
            prescription_dict.setdefault(prescription.drug.drug_name, []).append(prescription)

        return prescription_dict

    def has_active_prescription(self, drug):
        """Checks if there is an active prescription for that drug"""

        # If there exists a prescription for the user, with that drug and no end date
        if db.session.query(Prescription).filter(Prescription.user_id == self.user_id,
                                                 Prescription.drug_id == drug.drug_id,
                                                 Prescription.end_date.is_(None)).first():
            return True

        return False


class Prescription(db.Model):
    """Preseciption of a drug to a user"""

    __tablename__ = "prescriptions"

    prescription_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.drug_id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    physician = db.Column(db.String(64), nullable=True)
    dosage = db.Column(db.String(64), nullable=False)
    frequency = db.Column(db.String(64), nullable=False)

    user = db.relationship('User', backref=db.backref("prescriptions", order_by="desc(Prescription.end_date)"))
    drug = db.relationship('Drug', backref=db.backref("prescriptions", order_by="desc(Prescription.end_date)"))

    def __repr__(self):
        """Gives drug_id and user_id of record"""

        return "<Prescription user_id=%s drug_id=%s>" % (self.user_id, self.drug_id)

    def is_active(self):
        """Checks if prescription is active"""

        # return True if end date exists
        if self.end_date:
            return True

        return False


class Drug(db.Model):
    """Drug information provided by FDA"""

    __tablename__ = "drugs"

    drug_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    drug_name = db.Column(db.String(128), nullable=False)
    active_ingredients = db.Column(db.Text, nullable=False)

    def __repr__(self):
        """Gives drug_name of record"""

        return "<Drug drug_id=%s drug_name=%s>" % (self.drug_id, self.drug_name)


class Day(db.Model):
    """Log for a day"""

    __tablename__ = "days"

    day_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = db.Column(db.Date, unique=True, nullable=False)
    overall_mood = db.Column(db.Integer, nullable=False)
    max_mood = db.Column(db.Integer, nullable=True)
    min_mood = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('days', order_by='desc(Day.date)'))
    db.UniqueConstraint('user_id', 'date')

    def __repr__(self):
        """Gives date and user of record"""

        return "<Day user_id =%s date=%s>" % (self.user_id, self.date)


class Event(db.Model):
    """Log for an event"""

    __tablename__ = "events"

    event_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    event_name = db.Column(db.String(64), nullable=False)
    overall_mood = db.Column(db.Integer, nullable=False)
    max_mood = db.Column(db.Integer, nullable=True)
    min_mood = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('events'))
    # Gives days associated with event from start to end date
    days = db.relationship('Day', order_by='desc(Day.date)',
                           secondary='event_days',
                           backref='events')

    def __repr__(self):
        """Gives name and user of record"""

        return "<Day user_id =%s event=%s>" % (self.user_id, self.event_name)

    def get_duration(self):
        """Get start and end date of event"""

        # It actually gives the earliest and latest dates of days associated with the event.
        return (self.days[0].date, self.days[-1].date)

    def associate_days(self, start_date, end_date):
        """Create association between event and all logged days within duration"""

        # to check if day has already been associated with event
        # not (day in self.days))

        # for each day logged by the user owning that event
        for day in self.user.days:
            # if the day falls within the event duration
            if ((start_date <= day) and (day <= end_date)):
                event_day = EventDay(event_id=self.event_id,
                                     day_id=day.day_id)
                db.session.add(event_day)
                db.session.commit()


class EventDay(db.Model):
    """Association table between days and events"""

    __tablename__ = "event_days"

    event_days_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False)
    day_id = db.Column(db.Integer, db.ForeignKey('days.day_id'), nullable=False)

    # Prevent event from being associate with a unique day more than once
    db.UniqueConstraint('event_id', 'day_id')


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///testdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
