from jinja2 import StrictUndefined

from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, logout_user, login_required

from model import connect_to_db, db, User, Drug, Prescription, Day, Event
from mood_analysis import get_rolling_mean

from bcrypt import hashpw, gensalt

# import json
# import requests
app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Deals with undefined variables passed to jinja
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

##########################################################################
###########################   LOGIN MANAGER   ############################
##########################################################################

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'


@login_manager.user_loader
def user_loader(user_id):
    """ User loader callback to load user object from id stored in session """
    return User.query.get(user_id)


##########################################################################
############################  GENERAL ROUTES  ############################
##########################################################################


@app.route('/')
def index():
    """Homepage."""

    if 'user_id' in session:
        return redirect('/user_dashboard')

    return render_template('index.html')


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

    if not (user) or (hashpw(str(password), str(user.password)) != user.password):
        flash('Username and/or password invalid')
        return redirect('/')
    else:
        login_user(user)
        return redirect('/user_dashboard')


@app.route('/logout')
def logout():
    """Logout of account"""

    logout_user()
    return redirect('/')


@app.route('/user_dashboard')
@login_required
def show_user_dashboard():
    """Show user profile page"""

    user_id = session['user_id']

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


##########################################################################
########################### PRO USER ROUTES  #############################
##########################################################################
@app.route('/client_prescriptions.json')
@login_required
def get_client_prescriptions():
    """Returns prescriptions for a specific client"""

    pro = db.session.query(User).get(session['user_id'])
    client_id = request.args.get('client_id')
    client = db.session.query(User).get(client_id)
    if pro.professional:
        return jsonify({'username': client.username,
                        'prescriptions': client.group_prescriptions_by_drug()})


##########################################################################
###########################  MOOD LOG  ROUTES  ###########################
##########################################################################


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

    return redirect('/user_dashboard')


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

    event.associate_day(event_date)
    flash('Event %s on today (%s) successfully created' % (event_name, event_date))

    return redirect('/user_dashboard')


@app.route('/logs_html.json')
@login_required
def get_logs_for_day():
    """ Returns info of logs formatted in html to display as search results"""

    requested_date = datetime.strptime(request.args.get('searchDate'), '%Y-%m-%d').date()
    day = Day.query.filter_by(user_id=session['user_id'], date=requested_date).first()
    if day:
        day_info = day.get_info_dict()
        day_html = '<h3>On {}, you rated your moods: </h3><ul>'.format(day_info['date'])

        if day_info.get('max_mood'):
            day_html += '<li>Highest at {}</li>'.format(day_info['max_mood'])

        day_html += '<li> Overall at {}</li>'.format(day_info['overall_mood'])

        if day_info.get('min_mood'):
            day_html += '<li>Lowest at {}</li>'.format(day_info['min_mood'])

        if day_info['notes']:
            day_html += '<li>Notes: {}</li>'.format(day_info['notes'])
        day_html += '</ul>'

        event_html = ''
        for event in day.events:
            event_html += '<li>{} rated {}'.format(event.event_name, event.overall_mood)
            if event.notes:
                event_html += '<p>&nbsp;&nbsp;&nbsp;&nbsp;{}</p>'.format(event.notes)
            event_html += '</li>'

        if event_html:
            event_html = '<h3>You also logged event(s):</h3><ul>' + event_html + '</ul>'

        return jsonify({'day_html': day_html, 'event_html': event_html})

    return jsonify(None)


##########################################################################
##########################  MOOD CHART ROUTES  ###########################
##########################################################################

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
                    # if event.min_mood or event.max_mood:
                    #     event_dataset.extend([{'x': date, 'y': event.min_mood},
                    #                           {'x': date, 'y': event.max_mood}])
                    datasets.append({'label': 'event',
                                     'backgroundColor': 'rgba(0,0,0,0)',
                                     'borderColor': 'rgba(0,0,0,0)',
                                     'data': event_dataset})

    return jsonify({'datasets': datasets})


@app.route('/smooth_mood_data.json')
@login_required
def get_smooth_mood_data():
    """ Return 'smoothened' moods for a user"""

    client_id = request.args.get('clientId')
    smooth = get_rolling_mean(client_id)
    min_date = datetime.strptime(request.args.get('minDate'), '%Y-%m-%d').date()
    max_date = datetime.strptime(request.args.get('maxDate'), '%Y-%m-%d').date()

    # initialize master list of datasets
    dataset = []
    # create a dataset for each day's range
    for i, date in enumerate(smooth.index):
        # only for days between requested time window that have an overall mood
        if (smooth[i] is not None) and (min_date <= date) and (date <= max_date):
            # format date into moment.js format to be plottable on chart.js
            date = datetime.strftime(date, '%Y-%m-%d')
            # initialize dataset with point(date, overall_mood)
            dataset.append({'x': date, 'y': smooth[i]})

    return jsonify({'datasets': [{'data': dataset}]})


@app.route('/day_chart.json')
# @login_required
def get_day_logs():
    """ Get's all logs (events and day) for a specific day"""

    date_str = request.args.get('day')
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    day = Day.query.filter_by(user_id=session['user_id'], date=date).first()
    datasets = []

    print day

    if day:
        print day.events
        for event in day.events:
            # event_dataset.append({'x': date_str, 'y': event.overall_mood})
            datasets.append({'label': '%s' % event.event_name,
                             'backgroundColor': 'rgba(255,153,0,1)',
                             'borderColor': 'rgba(0,0,0,0)',
                             'data': [{'x': date_str, 'y': event.overall_mood}]})

        if day.overall_mood:
            # initialize dataset with point(date, overall_mood)
            day_dataset = [{'x': date_str, 'y': day.overall_mood}]
            # if there is a mood range (check by or, in cases min or max is 0)
            if day.min_mood or day.max_mood:
                # extend the day's mood dataset with the range values
                day_dataset.extend([{'x': date_str, 'y': day.min_mood},
                                    {'x': date_str, 'y': day.max_mood}])
            # append day dataset to the master list of datasets
            datasets.append({'label': 'Day %s' % date_str,
                             'data': day_dataset})
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
    return redirect('/user_dashboard')


##################################################################################
# PRESCRIPTION RELATED -- have to be logged in


@app.route('/end_prescription.json', methods=['POST'])
def end_prescription():
    """ Ends Prescription """

    prescription_id = int(request.form.get('prescriptionId'))
    end_date = datetime.strptime(request.form.get('currentDate'), '%Y-%m-%d').date()

    prescription = Prescription.query.get(prescription_id)
    prescription.end_date = end_date
    db.session.commit()

    return jsonify(prescription.make_dict())


@app.route('/add_prescription.json', methods=['POST'])
def process_prescription():
    """ Add new prescription """

    pro_id = int(session['user_id'])
    client_id = int(request.form.get('clientId'))
    drug_id = int(request.form.get('drugId'))
    instructions = request.form.get('instructions')
    start_date = datetime.strptime(request.form.get('startDate'), '%Y-%m-%d').date()
    notes = request.form.get('notes')
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

    return jsonify(prescription.make_dict())


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

    connect_to_db(app, 'asgard_db')

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
