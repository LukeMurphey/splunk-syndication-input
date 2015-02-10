# coding=utf-8
import unittest
import sys
import os
import time
from datetime import datetime, timedelta
import re
import splunk.auth

sys.path.append( os.path.join("..", "src", "bin") )

from syndication import SyndicationModularInput

class TestSyndicationImport(unittest.TestCase):
    
    def test_import_rss(self):
        results = SyndicationModularInput.get_feed("http://feeds.feedburner.com/456bereastreet")
        #print results[0]
        self.assertGreaterEqual(len(results), 10)
        
    def test_import_atom(self):
        
        results = SyndicationModularInput.get_feed("http://currentworldnews.blogspot.com/atom.xml")
        
        self.assertGreaterEqual(len(results), 10)
        
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
    
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(TestSyndicationImport))
    
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))