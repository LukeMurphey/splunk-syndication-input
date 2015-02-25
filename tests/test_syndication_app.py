# coding=utf-8
import unittest
import sys
import os
import time
from datetime import datetime, timedelta
import re
import splunk.auth
import threading
import urllib2

from test_web_server import get_server

sys.path.append( os.path.join("..", "src", "bin") )

from syndication import SyndicationModularInput
from syndication_app import feedparser

class SyndicationAppTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        
        attempts = 0
        cls.httpd = None
        
        sys.stdout.write("Waiting for web-server to start ...")
        sys.stdout.flush()
        
        while cls.httpd is None and attempts < 20:
            try:
                cls.httpd = get_server(8888)
                
                print " Done"
            except IOError:
                cls.httpd = None
                time.sleep(2)
                attempts = attempts + 1
                sys.stdout.write(".")
                sys.stdout.flush()
        
        def start_server(httpd):
            httpd.serve_forever()
        
        t = threading.Thread(target=start_server, args = (cls.httpd,))
        t.daemon = True
        t.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

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
        results, latest_date = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", return_latest_date=True)
        
        self.assertGreaterEqual(len(results), 10)
        
        self.assertIsNotNone(latest_date)
    
    def test_import_filter_by_date(self):
        # First get the date of the last item
        results, latest_date = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", return_latest_date=True)
        
        # Back off the date by a second
        latest_datetime = datetime.fromtimestamp(time.mktime(latest_date))
        
        latest_date_minus_second = latest_datetime - timedelta(seconds=1)
        latest_date_minus_second_struct = latest_date_minus_second.timetuple()
        
        # Try it and see if we get one result
        results = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", include_later_than=latest_date_minus_second_struct)
        
        self.assertGreaterEqual(len(results), 1)
        
    def test_import_filter_by_date_all(self):
        # First get the date of the last item
        results, latest_date = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", return_latest_date=True)
        
        # Try it and see if we get zero results
        results = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet", include_later_than=latest_date)
        
        self.assertGreaterEqual(len(results), 0)
        
    def test_flatten_dict(self):
        
        dict = {
                'list': {
                         'one' : 'uno',
                         'two' : 'dos'
                         }
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(len(d), 2)
        self.assertEquals(d['list.one'], 'uno')
        
    def test_flatten_list(self):
        
        dict = {
                'list': [
                         'first',
                         'second'
                         ]
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(len(d), 2)
        self.assertEquals(d['list.0'], 'first')
        self.assertEquals(d['list.1'], 'second')
        
    def test_flatten_none(self):
        
        dict = {
                'none': None
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(len(d), 1)
        self.assertEquals(d['none'], None)
        
    def test_flatten_int(self):
        
        dict = {
                'int': 1
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(len(d), 1)
        self.assertEquals(d['int'], 1)
        
    def test_flatten_boolean(self):
        
        dict = {
                'TrueDat': True,
                'FalseDat': False
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(len(d), 2)
        self.assertEquals(d['TrueDat'], True)
        self.assertEquals(d['FalseDat'], False)
        
    def test_flatten_time(self):
        
        t = time.strptime("9 Feb 15", "%d %b %y")
        
        dict = {
                'time': t
                }
        
        d = SyndicationModularInput.flatten(dict)
        
        self.assertEquals(d['time'], '2015-02-09T00:00:00Z')
    
    def test_get_auth_handler(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/auth/rss_example.xml", username="admin", password="changeme")   
        
        self.assertIsInstance(auth_handler, urllib2.HTTPBasicAuthHandler)
        
    def test_get_auth_handler_none(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEquals(auth_handler, None)
    
    def test_basic_auth_rss(self):
        
        username = 'admin'
        password = 'changeme'    
        
        results = SyndicationModularInput.get_feed("http://127.0.0.1:8888/auth/rss_example.xml", username="admin", password="changeme")
        
        self.assertGreaterEqual(len(results), 2)
        
    
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(TestSyndicationImport))
    
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))