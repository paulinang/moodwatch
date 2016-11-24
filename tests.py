import unittest
from server import app
from flask import session
from model import connect_to_db, db, example_data, Day, Event
from datetime import datetime
import json


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

        # Make sure redirected page is user dashboard
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Hi user1, How Are You Doing Today?</h3>', result.data)
        self.assertIn('Log Event', result.data)
        self.assertIn('Log Today', result.data)
        self.assertIn('<canvas id="moodChart"></canvas>', result.data)
        self.assertIn('<h3>Active Prescription', result.data)

        # Make sure day is created and has right info
        test_day = Day.query.filter_by(date='2016-11-01').first()
        assert test_day is not None, 'Day was not created'
        assert (test_day.user_id == 1), 'User_id for day not user1'
        assert ({'date': '2016-11-01',
                 'overall_mood': 0,
                 'min_mood': -15,
                 'max_mood': 15,
                 'notes': 'Test log day',
                 'events': []}
                == test_day.get_info_dict()), 'Day did not have the right info'

    def test_log_event(self):
        """ Test user1 logging a event"""

        result = self.client.post('/log_event_mood',
                                  data={'event-name': 'Test event',
                                        'today-event-date': '2016-11-01',
                                        'overall-mood': 0,
                                        'notes': 'Test log event'},
                                  follow_redirects=True)

        # Make sure redirected page is user dashboard
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Hi user1, How Are You Doing Today?</h3>', result.data)
        self.assertIn('Log Event', result.data)
        self.assertIn('Log Today', result.data)
        self.assertIn('<canvas id="moodChart"></canvas>', result.data)
        self.assertIn('<h3>Active Prescription', result.data)

        # Make sure event is created and has right info
        test_event = Event.query.filter_by(event_name='Test event').first()
        assert test_event is not None, 'Event was not created'
        test_event_info = [test_event.event_name, test_event.overall_mood, test_event.notes, test_event.user_id]
        assert (['Test event', 0, 'Test log event', 1]
                == test_event_info), 'Event did not have the right info'

        # Make sure there was a dummy day created and had right info
        assert (len(test_event.days) == 1), 'Event did not have only 1 day associated with it'
        dummy_day = test_event.days[0]
        dummy_day_info = [datetime.strftime(dummy_day.date, '%Y-%m-%d'), dummy_day.user_id, dummy_day.overall_mood]
        assert (['2016-11-01', 1, None]
                == dummy_day_info), 'Dummy day did not have right info'

    def test_log_html_json(self):
        """ Test getting user1's logs as html """

        result = self.client.get('/logs_html.json',
                                 query_string={'searchDate': '2016-08-09'})

        logs_html = json.loads(result.data)
        assert '<h3>On 2016-08-09, you rated' in logs_html['day_html']
        assert '<li>Overall at 10' in logs_html['day_html']
        assert 'Notes' not in logs_html['day_html']
        assert 'You also logged event(s):' in logs_html['event_html']
        assert 'Test event 1 rated 15' in logs_html['event_html']

    def test_day_chart_json(self):
        """ Test getting user1's logs as json for day chart """

        result = self.client.get('/day_chart.json',
                                 query_string={'day': '2016-08-09'})

        datasets = json.loads(result.data)
        assert {'label': 'Test event 1',
                'backgroundColor': 'rgba(255,153,0,1)',
                'borderColor': 'rgba(0,0,0,0)',
                'data': [{'x': '2016-08-09', 'y': 15}]} in datasets['datasets']
        assert {'label': 'Day 2016-08-09',
                'data': [{'x': '2016-08-09', 'y': 10}]} in datasets['datasets']


if __name__ == '__main__':
    unittest.main()
