from jinja2 import StrictUndefined

from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Drug, Prescription, Day, Event, EventDay

import json
import requests

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True


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
    email = request.form.get('email')

    # if there doesn't exist a record in the database with that email or username
    if db.session.query(User).filter(User.email == email).first():
        flash('An account with that email already exists')
    elif db.session.query(User).filter(User.username == username).first():
        flash('That username has already been taken')
    else:
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created.')

    return redirect('/')


@app.route('/login', methods=['POST'])
def process_login():
    """Validates and logs in to user account"""

    username = request.form.get('username')
    password = request.form.get('password')

    # Get user object for that username and password (none if non-existent)
    user = db.session.query(User).filter(User.username == username,
                                         User.password == password).first()

    # If user exists:
    # store id in sesion to keep them logged in
    # send to user profile
    if user:
        session['user_id'] = user.user_id
        return redirect('/user_profile')
    # Else user does not exist:
    # send back to homepage
    else:
        flash('Username and/or password invalid')
        return redirect('/')


@app.route('/logout')
def logout():
    """Logout of account"""

    # Logout route should only be available if user is logged in
    # Checking user_id exists in session to be safe
    if session.get('user_id'):
        # Remove user_id
        session.pop('user_id')
        flash('Logged out successfully')
    else:
        flash('You are not logged in.')

    return redirect('/')


@app.route('/user_profile')
def show_user_profile():
    """Show user profile page"""

    user_id = session.get('user_id')

    # Profile only available to logged in user
    if user_id:
        # Retrieve user object and pass it into profile template
        user = db.session.query(User).get(user_id)
        # today = datetime.today().date()

        # Is most recent logged day of user today
        if user.days:
            latest_day_date = user.days[0].date
            latest_day_overall = user.days[0].overall_mood
        else:
            latest_day_date = None
            latest_day_overall = None

        # today_logged = (latest_day.date == today) and (not latest_day.date is None)

    # 'logged_days': [datetime.strftime(day.date, '%Y-%m-%d') for day in user.days]
        return render_template('user_profile.html',
                               user_info={'user': user,
                                          'prescriptions': user.group_prescriptions_by_drug(),
                                          'day_log_range': user.get_day_log_range(),
                                          'latest_day_date': latest_day_date,
                                          'latest_day_overall': latest_day_overall
                                          }
                               )
    else:

        flash('You are not logged in.')
        return redirect('/')


###########################################################################################
# DRUG RELATED

@app.route('/drugs')
def drug_list():
    """ Show a list of all drugs in database"""

    # Get a list of all drug objects
    drugs = Drug.query.all()

    return render_template('drugs.html', drugs=drugs)


@app.route('/drugs/<drug_id>')
def show_drug_info(drug_id):
    """ Show details for a drug"""

    # Get specific drug object
    drug = Drug.query.get(drug_id)

    return render_template('drug_info.html', drug=drug)


##################################################################################
# MOOD LOG RELATED -- have to be logged in


@app.route('/log_day_mood', methods=['POST'])
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

    user_id = session['user_id']
    physician = request.form.get('physician')
    drug_id = request.form.get('drug-id')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    start_date = request.form.get('start-date')

    # create new prescription from form inputs, add to db
    prescription = Prescription(user_id=user_id,
                                drug_id=drug_id,
                                start_date=start_date,
                                physician=physician,
                                dosage=dosage,
                                frequency=frequency)

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


########### CHART.JS PRACTICE ###################
@app.route('/user_day_moods')
def display_day_mmood_chart():

    days = User.query.get(session['user_id']).days
    latest = datetime.strftime(days[0].date, '%Y-%m-%d')
    earliest = datetime.strftime(days[-1].date, '%Y-%m-%d')
    return render_template("chart_practice.html", latest=latest, earliest=earliest)


# @app.route('/event_mood.json')
# def event_mood_data():
#     """Return graphable event data"""
#     user = User.query.get(session['user_id'])
#     datasets = []
#     for event in user.events:
#         event_datasets = {'overall': []}
#         for day in event.days:
#             date = datetime.strftime(day.date, '%Y-%m-%d')
#             event_datasets['overall'].append({'x': date, 'y': event.overall_mood})ag
#             if event.min_mood or event.max_mood:
#                 event_datasets.setdefault('min', []).append({'x': date, 'y': event.min_mood})
#                 event_datasets.setdefault('max', []).append({'x': date, 'y': event.max_mood})

#         for mood, dataset in event_datasets.iteritems():
#             datasets.append({'label': event.event_name + mood,
#                              'backgroundColor': 'rgba(0,0,0,0)',
#                              'borderColor': 'rgba(255, 153, 0, 0.4)',
#                              'pointBackgroundColor': 'rgba(255, 153, 0, 0.4)',
#                              'data': dataset})

#     return jsonify(datasets)


@app.route('/day_mood_chart.json')
def day_mood_chart_data():
    """ Return some data to chart"""

    user = User.query.get(session['user_id'])

    # initialize list of datasets
    datasets = []
    # create a dataset for each day's range
    for day in user.days:
        if day.overall_mood:
            # format date into a moment.js format so chart.js can plot on a time scale
            date = datetime.strftime(day.date, '%Y-%m-%d')
            # initialize a dataset with that day's overall mood
            dataset = [{'x': date, 'y': day.overall_mood}]
            # if there is a mood range assocaited as well
            if day.min_mood or day.max_mood:
                # extend the day's mood dataset with the range values
                dataset.extend([{'x': date, 'y': day.min_mood},
                                {'x': date, 'y': day.max_mood}])
            # append the day dataset to the master list of datasets
            datasets.append({'label': 'day %s' % date,
                             'data': dataset})

    for event in user.events:
        event_datasets = {'overall': []}
        for day in event.days:
            date = datetime.strftime(day.date, '%Y-%m-%d')
            event_datasets['overall'].append({'x': date, 'y': event.overall_mood})
            if event.min_mood or event.max_mood:
                event_datasets.setdefault('min', []).append({'x': date, 'y': event.min_mood})
                event_datasets.setdefault('max', []).append({'x': date, 'y': event.max_mood})

        for mood, dataset in event_datasets.iteritems():
            datasets.append({'label': 'event',
                             'backgroundColor': 'rgba(0,0,0,0)',
                             'borderColor': 'rgba(0,0,0,0)',
                             # 'pointBackgroundColor': 'rgba(0,0,0,0)',
                             'data': dataset})

    return jsonify({'datasets': datasets})

################### OPENFDA API PRACTICE ######################


@app.route('/drug_search')
def show_drug_search_form():
    """Show drug search form"""

    return render_template('drug_search.html')


@app.route('/search_openfda.json', methods=['POST'])
def search_openfda():

    user_input = request.form.get('drug_keyword')
    print user_input
    r = requests.get("https://api.fda.gov/drug/label.json?limit=10&search=brand_name:%s" % user_input)

    drug_results = r.json()['results']
    # print drug_results

    return jsonify(drug_results)


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


def day_mood_data():
    """ Return some data to chart"""

    user = User.query.get(session['user_id'])

    data_dict = {
        'labels': [datetime.strftime(day.date, '%Y-%m-%d') for day in user.days],
        'datasets': [{
            'label': 'Overall Mood',
            'data': [day.overall_mood for day in user.days]
            }]
        }

    return data_dict


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app, 'projectdb')

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
