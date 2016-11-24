import unittest
from server import app
from flask import session
from model import connect_to_db, db, example_data, Day


class NotLoggedInFlaskTests(unittest.TestCase):
    """Testing routes when there is no user logged in"""

    def setUp(self):
        """ Stuff to do before every test."""

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'abc'
        self.client = app.test_client()

        connect_to_db(app, 'testdb')
        db.create_all()
        example_data()

    def tearDown(self):
        """ Do at end of every test. """

        db.session.close()
        db.drop_all()

    def test_index(self):
        """ Test homepage """

        result = self.client.get('/',
                                 follow_redirects=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn('Log In', result.data)

    def test_user_registration(self):
        """ Test user registration form """

        result = self.client.post('/register',
                                  data={'new-username': 'test_user',
                                        'new-password': 'test_password',
                                        'email': 'test@email.com'},
                                  follow_redirects=True)

        self.assertIn('Log In', result.data)

    def test_user_login(self):
        """ Test user login form with user1"""

        result = self.client.post('/login',
                                  data={'username': 'user1',
                                        'password': 'password1'},
                                  follow_redirects=True)

        self.assertIn('<h3>Hi user1, How Are You Doing Today?</h3>', result.data)
        self.assertIn('Log Event', result.data)
        self.assertIn('Log Today', result.data)
        self.assertIn('<canvas id="moodChart"></canvas>', result.data)
        self.assertIn('<h3>Active Prescription', result.data)


class LoggedInFlaskTests(unittest.TestCase):
    """Testing routes when user1 is logged in"""

    def setUp(self):
        """ Stuff to do before every test."""

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'abc'
        self.client = app.test_client()

        connect_to_db(app, 'testdb')
        db.create_all()
        example_data()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

    def tearDown(self):
        """ Do at end of every test. """

        db.session.close()
        db.drop_all()

    def test_user_dashboard(self):
        """ Test user1 dashboard"""

        result = self.client.get('/user_dashboard',
                                 follow_redirects=True)

        self.assertIn('<h3>Hi user1, How Are You Doing Today?</h3>', result.data)
        self.assertIn('Log Event', result.data)
        self.assertIn('Log Today', result.data)
        self.assertIn('<canvas id="moodChart"></canvas>', result.data)
        self.assertIn('<h3>Active Prescription', result.data)

    def test_user_logs(self):
        """ Test user1 logs page"""

        result = self.client.get('/user_logs')

        self.assertIn('Select A Time Window', result.data)
        self.assertIn('Toggle Events', result.data)
        self.assertIn('Clear Search Results', result.data)
        self.assertIn('canvas id="dayChart">', result.data)

    def test_logout(self):
        """ Test user1 logged out"""

        with self.client as c:
            result = c.get('/logout',
                           follow_redirects=True)
            self.assertNotIn('user_id', session)
            self.assertIn('Log In', result.data)

    def test_log_day(self):
        """ Test user1 logging a day"""

        result = self.client.post('/log_day_mood',
                                  data={'today-date': '2016-11-01',
                                        'overall-mood': 0,
                                        'min-mood': -15,
                                        'max-mood': 15,
                                        'notes': 'Test log day'},
                                  follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Hi user1, How Are You Doing Today?</h3>', result.data)
        self.assertIn('Log Event', result.data)
        self.assertIn('Log Today', result.data)
        self.assertIn('<canvas id="moodChart"></canvas>', result.data)
        self.assertIn('<h3>Active Prescription', result.data)

        test_day = Day.query.filter_by(date='2016-11-01').first()
        assert test_day is not None, 'Day was not created'
        assert ({'date': '2016-11-01',
                 'overall_mood': 0,
                 'min_mood': -15,
                 'max_mood': 15,
                 'notes': 'Test log day',
                 'events': []}
                == test_day.get_info_dict()), 'Day did not have the right info'


if __name__ == '__main__':
    unittest.main()
