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
                sess['user_id'] = 1

    def tearDown(self):
        """ Do at end of every test. """

        db.session.close()
        db.drop_all()

    def test_index(self):
        """ Check homepage """

        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        # Check that there is login / register forms
        self.assertIn('Log Into Existing Account', result.data)
        self.assertIn('Register New Account', result.data)

    def testUserDashboard(self):
        """ Check user dashboard """

        result = self.client.get('/user_profile')
        self.assertEqual(result.status_code, 200)
        self.assertIn('<canvas', result.data)
        # self.assertIn('Log An Event For Today</button>', result.data)
        # self.assertIn('Log Today</button>', result.data)


if __name__ == '__main__':
    unittest.main()
