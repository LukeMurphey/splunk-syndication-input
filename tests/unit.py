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

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse

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
        results = SyndicationModularInput.get_feed("https://www.str.org/article-feed/-/journal/rss/20123/264695")
        
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

    def test_get_auth_handler(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/auth/rss_example.xml", username="admin", password="changeme")   
        
        self.assertIsInstance(auth_handler, HTTPBasicAuthHandler)
        
    def test_get_auth_handler_none(self):
        auth_handler = SyndicationModularInput.get_auth_handler("http://127.0.0.1:8888/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEqual(auth_handler, None)

    def test_get_realm_and_auth_type(self):
        auth_realm, auth_type = SyndicationModularInput.get_realm_and_auth_type("http://127.0.0.1:8888/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEqual(auth_realm, None)
        self.assertEqual(auth_type, None)

    def test_get_realm_and_auth_type_invalid(self):
        auth_realm, auth_type = SyndicationModularInput.get_realm_and_auth_type("http://127.0.0.1:8888/invalid_auth/rss_example.xml", username="admin", password="changeme")   
        
        self.assertEqual(auth_realm, None)
        self.assertEqual(auth_type, None)

class TestSyndicationOffline(unittest.TestCase):
    def test_flatten_dict(self):
        
        d = {
                'list': {
                         'one' : 'uno',
                         'two' : 'dos'
                         }
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 2)
        self.assertEqual(d['list.one'], 'uno')
        
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
        
        self.assertEqual(len(d), 6)

        keys = list(d.keys())
        self.assertEqual(keys[0], 'list.1')
        self.assertEqual(keys[1], 'list.2')
        self.assertEqual(keys[2], 'list.3')
        self.assertEqual(keys[3], 'list.4')
        self.assertEqual(keys[4], 'list.5')
        self.assertEqual(keys[5], 'list.6')

    def test_flatten_list(self):
        
        d = {
                'list': [
                         'first',
                         'second'
                         ]
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 2)
        self.assertEqual(d['list.0'], 'first')
        self.assertEqual(d['list.1'], 'second')
        
    def test_flatten_none(self):
        
        d = {
                'none': None
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 1)
        self.assertEqual(d['none'], None)
        
    def test_flatten_int(self):
        
        d = {
                'int': 1
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 1)
        self.assertEqual(d['int'], 1)
        
    def test_flatten_boolean(self):
        
        d = {
                'TrueDat': True,
                'FalseDat': False
                }
        
        d = SyndicationModularInput.flatten(d)
        
        self.assertEqual(len(d), 2)
        self.assertEqual(d['TrueDat'], True)
        self.assertEqual(d['FalseDat'], False)
        
    def test_flatten_time(self):
        
        t = time.strptime("9 Feb 15", "%d %b %y")
        
        d = {
            'time': t
        }
        
        d = SyndicationModularInput.flatten(d)
        self.assertEqual(d['time'], '2015-02-09T00:00:00Z')

    def test_get_proxy_handler_none(self):
        self.assertIsNone(SyndicationModularInput.get_proxy_handler(None))

    def test_get_proxy_handler(self):
        url = urlparse("http://127.0.0.1:8080")
        self.assertIsNotNone(SyndicationModularInput.get_proxy_handler(url))

    def test_get_timestamp_updated(self):
        event = {
            'updated_parsed': '2022-03-10T10:45:00Z'
        }

        self.assertEqual(SyndicationModularInput.get_timestamp(event), datetime(2022, 3, 10, 10, 45))
    
    def test_get_timestamp_published(self):
        event = {
            'published_parsed': '2022-03-10T10:46:00Z'
        }

        self.assertEqual(SyndicationModularInput.get_timestamp(event), datetime(2022, 3, 10, 10, 46))
    
    def test_get_timestamp_default(self):
        event = {
            'noasdasd': 'Not a date!'
        }

        self.assertIsNotNone(SyndicationModularInput.get_timestamp(event))

    def test_get_timestamp_bad_time(self):
        event = {
            'published_parsed': 'Not a date!'
        }

        self.assertIsNotNone(SyndicationModularInput.get_timestamp(event))

if __name__ == '__main__':
    unittest.main()
