# coding=utf-8
import unittest
import sys
import os
import errno
import time
from datetime import datetime, timedelta

try:
    from urllib.request import HTTPBasicAuthHandler
except:
    from urllib2 import HTTPBasicAuthHandler

sys.path.append( os.path.join("..", "src", "bin") )

from syndication import SyndicationModularInput
from syndication_app import feedparser
from unit_test_web_server import UnitTestWithWebServer

class SyndicationAppTestCase(UnitTestWithWebServer):
    
    @classmethod
    def tearDownClass(cls):
        UnitTestWithWebServer.shutdownServer()

class TestSyndicationImport(SyndicationAppTestCase):
    
    def test_import_rss_public(self):
        results = SyndicationModularInput.get_feed("http://answers.splunk.com/feed/questions.rss")
        
        self.assertGreaterEqual(len(results), 10)
        
    def test_import_atom_public(self):
        
        results = SyndicationModularInput.get_feed("http://currentworldnews.blogspot.com/atom.xml")
        
        self.assertGreaterEqual(len(results), 10)
        
    def test_import_rss(self):
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/rss_example.xml")
        
        self.assertGreaterEqual(len(results), 2)
        
    def test_import_atom(self):
        
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/atom_example.xml")
        
        self.assertGreaterEqual(len(results), 1)
        
    def test_import_return_latest_date(self):
        results, latest_date = SyndicationModularInput.get_feed("http://127.0.0.1:8888/atom_example.xml", return_latest_date=True)
        
        self.assertGreaterEqual(len(results), 0)
        
        self.assertIsNotNone(latest_date)
    
    def test_import_filter_by_date(self):
        # First get the date of the last item
        results, latest_date = SyndicationModularInput.get_feed("http://127.0.0.1:8888/atom_example.xml", return_latest_date=True)
        
        # Back off the date by a second
        latest_datetime = datetime.fromtimestamp(time.mktime(latest_date))
        
        latest_date_minus_second = latest_datetime - timedelta(seconds=1)
        latest_date_minus_second_struct = latest_date_minus_second.timetuple()
        
        # Try it and see if we get one result
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/atom_example.xml", include_later_than=latest_date_minus_second_struct)
        
        self.assertGreaterEqual(len(results), 1)
        
    def test_import_filter_by_date_all(self):
        # First get the date of the last item
        results, latest_date = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", return_latest_date=True)
        
        # Try it and see if we get zero results
        results = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", include_later_than=latest_date)
        
        self.assertGreaterEqual(len(results), 0)
        
    def test_flatten_dict(self):
        
        d = {
                'list': {
                         'one' : 'uno',
                         'two' : 'dos'
                         }
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEquals(len(d), 2)
        self.assertEquals(d['list.one'], 'uno')
        
    def test_flatten_dict_sort(self):
        # https://lukemurphey.net/issues/2039
        d = {
                'list': {
                         '3' : 'tres',
                         '1' : 'uno',
                         '2' : 'dos',
                         '5' : 'cinco',
                         '4' : 'cuatro',
                         '6' : 'seis'
                         }
                }
        
        d = SyndicationModularInput.flatten(d, sort=True)
        
        self.assertEquals(len(d), 6)

        keys = list(d.keys())
        self.assertEquals(keys[0], 'list.1')
        self.assertEquals(keys[1], 'list.2')
        self.assertEquals(keys[2], 'list.3')
        self.assertEquals(keys[3], 'list.4')
        self.assertEquals(keys[4], 'list.5')
        self.assertEquals(keys[5], 'list.6')

    def test_flatten_list(self):
        
        d = {
                'list': [
                         'first',
                         'second'
                         ]
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEquals(len(d), 2)
        self.assertEquals(d['list.0'], 'first')
        self.assertEquals(d['list.1'], 'second')
        
    def test_flatten_none(self):
        
        d = {
                'none': None
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEquals(len(d), 1)
        self.assertEquals(d['none'], None)
        
    def test_flatten_int(self):
        
        d = {
                'int': 1
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEquals(len(d), 1)
        self.assertEquals(d['int'], 1)
        
    def test_flatten_boolean(self):
        
        d = {
                'TrueDat': True,
                'FalseDat': False
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 2)
        self.assertEquals(d['TrueDat'], True)
        self.assertEquals(d['FalseDat'], False)
        
    def test_flatten_time(self):
        
        t = time.strptime("9 Feb 15", "%d %b %y")
        
        d = {
            'time': t
        }
        
        d = SyndicationModularInput.flatten(d)
        self.assertEquals(d['time'], '2015-02-09T00:00:00Z')
    
    def test_get_auth_handler(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/auth/rss_example.xml", username="admin", password="changeme")   
        
        self.assertIsInstance(auth_handler, HTTPBasicAuthHandler)
        
    def test_get_auth_handler_none(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEquals(auth_handler, None)

    def test_get_realm_and_auth_type(self):
        auth_realm, auth_type = SyndicationModularInput.get_realm_and_auth_type("http://127.0.0.1:8888/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEquals(auth_realm, None)
        self.assertEquals(auth_type, None)

    def test_get_realm_and_auth_type_invalid(self):
        auth_realm, auth_type = SyndicationModularInput.get_realm_and_auth_type("http://127.0.0.1:8888/invalid_auth/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEquals(auth_realm, None)
        self.assertEquals(auth_type, None)
    
    def test_basic_auth_rss(self):
        
        username = 'admin'
        password = 'changeme'    
        
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/auth/rss_example.xml", username="admin", password="changeme")
        
        self.assertEqual(len(results), 2)

    def test_cleanup_html_rss(self):  
        # https://lukemurphey.net/issues/2038
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/rss_with_html.xml", clean_html=True)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[2]['content.0.value'][:120], "  1. **Introduction**\n\nIt seems that Google Chrome extensions have become quite the tool for banking\nmalware fraudsters.")
    
if __name__ == '__main__':
    report_path = os.path.join('..', os.environ.get('TEST_OUTPUT', 'tmp/test_report.html'))

    # Make the test directory
    try:
        os.makedirs(os.path.dirname(report_path))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    unittest.main()

    """
    with open(report_path, 'w') as report_file:
        test_runner = HTMLTestRunner.HTMLTestRunner(
            stream=report_file
        )
        unittest.main(testRunner=test_runner)
    """

