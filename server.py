from jinja2 import StrictUndefined

from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Drug, Prescription


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


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

    user = db.session.query(User).filter(User.username == username,
                                         User.password == password).first()

    if user:
        session['user_id'] = user.user_id
        return redirect('/user_profile')
    else:
        flash('Username and/or password invalid')
        return redirect('/')


@app.route('/logout')
def logout():
    """Logout of account"""

    if session.get('user_id'):
        session.pop('user_id')
        flash('Logged out successfully')
    else:
        flash('You are not logged in.')

    return redirect('/')


@app.route('/user_profile')
def show_user_profile():
    """Show user profile page"""

    user_id = session.get('user_id')

    # only shows profile page if user logged in
    if user_id:
        user = db.session.query(User).get(user_id)
        return render_template('user_profile.html', user=user)
    else:
        flash('You are not logged in.')
        return redirect('/')


###########################################################################################
# DRUG RELATED

@app.route('/drugs')
def drug_list():
    """ Show a list of all drugs in database"""

    drugs = Drug.query.all()

    return render_template('drugs.html', drugs=drugs)


@app.route('/drugs/<drug_id>')
def show_drug_info(drug_id):
    """ Show details for a drug"""

    drug = Drug.query.get(drug_id)

    return render_template('drug_info.html', drug=drug)


@app.route('/add_prescription')
def prescription_form():
    """ Show add prescription form """

    drug_id = request.args.get('drug', default=None)

    drug = Drug.query.get(drug_id)

    return render_template('prescription_form.html', drug=drug)


@app.route('/add_prescription', methods=['POST'])
def process_prescription():
    """ Add new prescription """

    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    start_date = datetime.strptime(request.form.get('start-date'), "%Y-%m-%d")

    end_date = request.form.get('end-date')
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = None
    physician = request.form.get('physician')
    drug_id = request.form.get('drug-id')
    user_id = session['user_id']

    prescription = Prescription(user_id=user_id,
                                drug_id=drug_id,
                                start_date=start_date,
                                end_date=end_date,
                                physician=physician,
                                dosage=dosage,
                                frequency=frequency)

    db.session.add(prescription)
    db.session.commit()

    flash('Prescription added')
    return redirect('/user_profile')




if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
