"""
This module provides a search command for retrieving information from RSS feeds.
"""

import sys

from splunk.util import normalizeBoolean

from syndication_app.search_command import SearchCommand
from syndication import SyndicationModularInput

class FeedsTail(SearchCommand):
    """
    This class is the command that retrieves the feed information.
    """
    def __init__(self, url, username=None, password=None, clean_html=False):

        # Save the parameters
        self.url = url
        self.username = username
        self.password = password
        self.clean_html = normalizeBoolean(clean_html)

         # Initialize the class
        SearchCommand.__init__(self, run_in_preview=True, logger_name='feeds_tail_search_command')

    def handle_results(self, results, session_key, in_preview):

        results = SyndicationModularInput.get_feed(self.url, self.username, self.password, clean_html=self.clean_html, logger=self.logger)
        self.output_results(results)

if __name__ == '__main__':
    try:
        FeedsTail.execute()
        sys.exit(0)
    except Exception as exception:
        print(exception)
