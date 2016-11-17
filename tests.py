import unittest
from server import app
from model import connect_to_db, db, example_data


class FlaskTests(unittest.TestCase):

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
                sess['user_id'] = 2

    def tearDown(self):
        """ Do at end of every test. """

        db.session.close()
        db.drop_all()

    def test_index(self):
        """ Test homepage """

        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        # Check that there is login / register forms
        self.assertIn('Log Into Existing Account', result.data)
        self.assertIn('Register New Account', result.data)

    def test_user_registration(self):
        """ Test user registration form """

        result = self.client.post('/register',
                                  data={'new-username': 'test_user',
                                        'new-password': 'test_password',
                                        'email': 'test@email.com'},
                                  follow_redirects=True)

        self.assertIn('Account successfully created.', result.data)

    def test_user_login(self):
        """ Test user login form """

        result = self.client.post('/login',
                                  data={'username': 'user1',
                                        'password': 'password'},
                                  follow_redirects=True)

        # assert session['user_id'] == 1
        self.assertIn('<h1>user1\'s Profile </h1>', result.data)
        # self.assertIn('<h1>user1 Dashboard</h1>', result.data)

    def testUserDashboard(self):
        """ Test user dashboard for preset user2"""

        result = self.client.get('/user_profile')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h1>user2\'s Profile </h1>', result.data)
        self.assertIn('<canvas', result.data)
        # self.assertIn('Log An Event For Today</button>', result.data)
        # self.assertIn('Log Today</button>', result.data)


if __name__ == '__main__':
    unittest.main()
