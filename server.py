from jinja2 import StrictUndefined

from flask import Flask, jsonify, render_template, request, redirect, flash
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db


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

    flash('Created account for %s with email %s and secret password that is not %s' % (username, email, password))

    return redirect('/')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
