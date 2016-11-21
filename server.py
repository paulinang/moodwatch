from jinja2 import StrictUndefined

from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, logout_user, login_required

from model import connect_to_db, db, User, Drug, Prescription, Day, Event

from bcrypt import hashpw, gensalt

# import json
# import requests
app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Deals with undefined variables passed to jinja
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

##########################################
###########   LOGIN MANAGER   ############
##########################################

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'


@login_manager.user_loader
def user_loader(user_id):
    """ User loader callback to load user object from id stored in session """
    return User.query.get(user_id)


@app.route('/')
def index():
    """Homepage."""

    return render_template('index.html')

####################################################################################
# USER ACCOUNT RELATED


@app.route('/register', methods=['POST'])
def process_registration():
    """Creates new user account"""

    username = request.form.get('new-username')
    password = request.form.get('new-password')
    hashed = hashpw(str(password), gensalt())
    email = request.form.get('email')

    # if there doesn't exist a record in the database with that email or username
    if db.session.query(User).filter(User.email == email).first():
        flash('An account with that email already exists')
    elif db.session.query(User).filter(User.username == username).first():
        flash('That username has already been taken')
    else:
        user = User(username=username, email=email, password=hashed, user_type='basic')
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created.')

    return redirect('/')


@app.route('/login', methods=['POST'])
def process_login():
    """Validates and logs in to user account"""

    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if (user) and (hashpw(str(password), str(user.password)) == user.password):
        login_user(user)
        return redirect('/user_profile')
    else:
        flash('Username and/or password invalid')
        return redirect('/')


@app.route('/logout')
def logout():
    """Logout of account"""

    logout_user()
    return redirect('/')


@app.route('/user_profile')
@login_required
def show_user_profile():
    """Show user profile page"""

    user_id = session.get('user_id')

    # Retrieve user object and pass it into profile template
    user = db.session.query(User).get(user_id)
    # today = datetime.today().date()
    if user.professional:
        return render_template('pro_dashboard.html', pro=user)

    return render_template('basic_dashboard.html',
                           user_info={'user': user,
                                      'prescriptions': user.group_prescriptions_by_drug(),
                                      'daylog_info': user.get_daylog_info()
                                      }
                           )


##################################################################################
# MOOD LOG RELATED -- have to be logged in


@app.route('/log_day_mood', methods=['POST'])
@login_required
def process_day_mood_log():
    """ Add day log to database """

    date = datetime.strptime(request.form.get('today-date'), '%Y-%m-%d').date()
    user_id, overall_mood, min_mood, max_mood, notes = get_mood_rating()

    day = Day.query.filter_by(user_id=user_id, date=date).first()

    if day:
        day.overall_mood = overall_mood
        day.min_mood = min_mood
        day.max_mood = max_mood
        day.notes = notes
    else:
        day = Day(user_id=user_id,
                  date=date,
                  overall_mood=overall_mood,
                  max_mood=max_mood,
                  min_mood=min_mood,
                  notes=notes)
        db.session.add(day)

    db.session.commit()
    # day_datapoint = {'date': datetime.strftime(day.date, '%Y-%m-%d'),
    #                  'overall_mood': day.overall_mood}

    return redirect('/user_profile')


@app.route('/log_event_mood', methods=['POST'])
@login_required
def process_event_mood_log():
    """ Add event log to db"""

    # get user inputs
    event_name = request.form.get('event-name')
    event_date = datetime.strptime(request.form.get('today-event-date'), '%Y-%m-%d').date()
    # end_date = datetime.strptime(request.form.get('end-date'), '%Y-%m-%d').date()
    user_id, overall_mood, min_mood, max_mood, notes = get_mood_rating()

    # create event
    event = Event(event_name=event_name,
                  user_id=user_id,
                  overall_mood=overall_mood,
                  max_mood=max_mood,
                  min_mood=min_mood,
                  notes=notes)
    db.session.add(event)
    db.session.commit()

    # event.associate_days(start_date, end_date)
    if not event_date in [day.date for day in event.user.days]:
        event.create_dummy_day(event_date)
        flash('Event %s on today (%s) successfully created' % (event_name, event_date))

    return redirect('/user_profile')


@app.route('/search_log_results.json')
@login_required
def get_logs_for_time():
    start_date = datetime.strptime(request.args.get('startDate'), '%Y-%m-%d').date()
    day = Day.query.filter_by(user_id=session['user_id'], date=start_date).first()
    if day:
        return jsonify(day.get_info_dict())

    return jsonify(None)


##################################################################################
# MOOD CHART


@app.route('/user_day_moods')
@login_required
def display_day_mood_chart():
    user = User.query.get(session['user_id'])
    return render_template('mood_chart.html',
                           user_info={'user': user,
                                      'daylog_info': user.get_daylog_info()}
                           )


@app.route('/mood_chart.json')
@login_required
def get_mood_chart_data():
    """ Return relevant data to display on chart.js """

    user = User.query.get(session['user_id'])
    min_date = datetime.strptime(request.args.get('minDate'), '%Y-%m-%d').date()
    max_date = datetime.strptime(request.args.get('maxDate'), '%Y-%m-%d').date()

    # initialize master list of datasets
    datasets = []
    # create a dataset for each day's range
    for day in user.days:
        # only for days between requested time window that have an overall mood
        if (day.overall_mood) and (min_date <= day.date) and (day.date <= max_date):
            # format date into moment.js format to be plottable on chart.js
            date = datetime.strftime(day.date, '%Y-%m-%d')
            # initialize dataset with point(date, overall_mood)
            day_dataset = [{'x': date, 'y': day.overall_mood}]
            # if there is a mood range (check by or, in cases min or max is 0)
            if day.min_mood or day.max_mood:
                # extend the day's mood dataset with the range values
                day_dataset.extend([{'x': date, 'y': day.min_mood},
                                    {'x': date, 'y': day.max_mood}])
            # append day dataset to the master list of datasets
            datasets.append({'label': 'Day %s' % date,
                             'data': day_dataset})

            # also append events for logged (no dummy) days
            for event in day.events:
                if event.overall_mood:
                    event_dataset = [{'x': date, 'y': event.overall_mood}]
                    if event.min_mood or event.max_mood:
                        event_dataset.extend([{'x': date, 'y': event.min_mood},
                                              {'x': date, 'y': event.max_mood}])
                    datasets.append({'label': 'event',
                                     'backgroundColor': 'rgba(0,0,0,0)',
                                     'borderColor': 'rgba(0,0,0,0)',
                                     'data': event_dataset})

    return jsonify({'datasets': datasets})


###########################################################################################
# DRUG RELATED


@app.route('/drugs')
@login_required
def drug_list():
    """ Show a list of all drugs in database"""

    user_id = session.get('user_id')

    # Retrieve user object and pass it into profile template
    user = db.session.query(User).get(user_id)
    # today = datetime.today().date()
    if user.professional:
        # Get a list of all drug objects
        drugs = Drug.query.all()

        return render_template('drugs.html', drugs=drugs, pro=user)

    flash('Only healthcare professionals can access drug database')
    return redirect('/user_profile')


##################################################################################
# PRESCRIPTION RELATED -- have to be logged in


@app.route('/prescription_info/<prescription_id>')
def show_prescription_info(prescription_id):
    """ Show details for a prescription"""

    prescription = Prescription.query.get(prescription_id)

    # Will only show prescription info if logged in user 'owns' that prescription
    if prescription.user_id == session.get('user_id'):
        return render_template('prescription_info.html', prescription=prescription)
    else:
        flash('You do not have access to this user\'s prescription.')
        return redirect('/')


@app.route('/add_prescription')
def prescription_form():
    """ Show add prescription form """

    drug_id = request.args.get('drug', default=None)

    # Gets the prescription with the most recent end date (None end date takes precedence)
    last_prescription = Prescription.query.filter_by(drug_id=drug_id,
                                                     user_id=session['user_id']).order_by(Prescription.end_date.desc()).first()

    # If there was no previous prescription, or there is no active prescription
    if (not last_prescription) or (last_prescription.end_date):
        # Get drug object of interest
        drug = Drug.query.get(drug_id)
        # Show prescription form for that drug, last_prescription is an object or None
        return render_template('prescription_form.html', drug=drug, last_prescription=last_prescription)
    else:
        # Send user to active prescription so they can end it before creating a new one
        flash('You have an active prescription for this drug. End it before creating a new prescription with updated information.')
        return redirect('/prescription_info/%s' % last_prescription.prescription_id)


@app.route('/add_prescription', methods=['POST'])
def process_prescription():
    """ Add new prescription """

    pro_id = int(session['user_id'])
    client_id = int(request.form.get('client-id'))
    print request.form.get('drug-id')
    drug_id = int(request.form.get('drug-id'))
    instructions = request.form.get('prescription-instructions')
    start_date = datetime.strptime(request.form.get('prescription-start-date'), '%Y-%m-%d').date()
    notes = request.form.get('prescription-notes')

    # create new prescription from form inputs, add to db
    prescription = Prescription(client_id=client_id,
                                pro_id=pro_id,
                                drug_id=drug_id,
                                start_date=start_date,
                                instructions=instructions,
                                notes=notes)

    db.session.add(prescription)
    db.session.commit()

    flash('Prescription added')
    return redirect('/user_profile')


@app.route('/end_prescription', methods=['POST'])
def end_prescription():
    """ Ends an existing prescription """

    prescription_id = request.form.get('prescription-id')
    end_date = request.form.get('end-date')

    # update existing prescription's end_date
    old_prescription = Prescription.query.get(prescription_id)
    old_prescription.end_date = end_date
    flash('Prescription ended')
    db.session.commit()

    # if user chose to add new prescription after ending old one
    # send to add prescription for that drug
    if request.form.get('add-prescription'):
        return redirect('/add_prescription?drug=%s' % old_prescription.drug_id)
    else:
        return redirect('/user_profile')


###################################################################################
# HELPER FUNCTIONS


def get_mood_rating():
    """Gets ratings for a mood (day/event)"""

    user_id = session['user_id']
    overall_mood = request.form.get('overall-mood')
    notes = request.form.get('notes')
    # min and max mood are not req in html, will give empty str if not filled
    # changes empty str to None in Python before passing it into Day instance
    # prevents error when making record in db (min/max mood are integers)
    if not request.form.get('min-mood'):
        min_mood = None
        max_mood = None
    else:
        min_mood = request.form.get('min-mood')
        max_mood = request.form.get('max-mood')

    return [user_id, overall_mood, min_mood, max_mood, notes]


# def parse_date(form_input_name):
#     """Parses date input from web form into datetime object"""

#     return datetime.strptime(request.args.get(form_input_name), '%Y-%m-%d').date()


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app, 'projectdb')

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
