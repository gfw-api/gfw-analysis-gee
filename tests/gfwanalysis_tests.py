import os
import tempfile
import unittest

import gfwanalysis


class GFWAnalysisTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, gfwanalysis.app.config['DATABASE'] = tempfile.mkstemp()
        gfwanalysis.app.testing = True
        self.app = gfwanalysis.app.test_client()

    def test_empty_db(self):
        rv = self.app.get('/ping')
        assert b'pong' in rv.data

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(gfwanalysis.app.config['DATABASE'])


if __name__ == '__main__':
    unittest.main()
