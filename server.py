from jinja2 import StrictUndefined

from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Drug, Prescription, Day


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

@app.route('/register')
def show_register_form():
    """Show form for creating new user account"""

    return render_template('register_form.html')


@app.route('/register', methods=['POST'])
def process_registration():
    """Creates new user account"""

    username = request.form.get('username')
    password = request.form.get('password')
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


@app.route('/login')
def show_login_form():
    """Show login to account form"""

    return render_template('login_form.html')


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

        # Create a dict that groups prescriptions of the same drug together
        prescription_dict = {}
        for prescription in user.prescriptions:
            prescription_dict.setdefault(prescription.drug.drug_name, []).append(prescription)

        return render_template('user_profile.html', user=user, prescriptions=prescription_dict)
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
# DAY LOG RELATED -- have to be logged in

@app.route('/log_day_mood')
def show_day_mood_form():
    """ Show add mood log for day form"""

    return render_template('day_mood_form.html')


@app.route('/log_day_mood', methods=['POST'])
def process_day_mood_log():
    """ Add day log to database """

    user_id = session['user_id']
    overall_mood = request.form.get('overall-mood')
    if not request.form.get('min-mood'):
        min_mood = None
        max_mood = None
    else:
        min_mood = request.form.get('min-mood')
        max_mood = request.form.get('max-mood')
    print type(min_mood), type(max_mood)
    notes = request.form.get('notes')
    date = request.form.get('date')

    day = Day(user_id=user_id,
              datetime=date,
              overall_mood=overall_mood,
              max_mood=max_mood,
              min_mood=min_mood,
              notes=notes)

    db.session.add(day)
    db.session.commit()

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
    start_date = datetime.strptime(request.form.get('start-date'), "%Y-%m-%d")

    # sets end_date as None if none entered
    # CODE COMMENTED OUT - prescription form does not take end_date for now
    # end_date = request.form.get('end-date')
    # if end_date:
    #     end_date = datetime.strptime(end_date, "%Y-%m-%d")
    # else:
    #     end_date = None

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


###################################################################################
# HELPER FUNCTIONS

# def is_loggedin():
#     """ Checks if there is a valid user logged in """

#     user_id = session.get('user_id')

#     if not user_id:
#         return 'You are not logged in.'
#     else:
#         user = User.query.get(user_id)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
