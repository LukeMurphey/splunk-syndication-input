"""
This module provides the Python code for a modular input that retrieves syndication feed info so
that Splunk can index it.
"""

import sys
import time
import re
import os
import logging
try:
    from urllib.request import HTTPBasicAuthHandler, HTTPDigestAuthHandler, build_opener, ProxyHandler
except:
    from urllib2 import HTTPBasicAuthHandler, HTTPDigestAuthHandler, build_opener, ProxyHandler
from collections import OrderedDict

path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_input.zip')
sys.path.insert(0, path_to_mod_input_lib)
from modular_input import ModularInput, URLField, DurationField, BooleanField, Field
from syndication_app.event_writer import StashNewWriter

path_to_app_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'syndication_app')
sys.path.insert(0, path_to_app_lib)
import feedparser
import html2text

class SyndicationModularInput(ModularInput):
    """
    The syndication input facilitates import of feeds into Splunk.
    """

    OUTPUT_USING_STASH = True

    def __init__(self):

        scheme_args = {'title': "Syndication Feed (RSS, ATOM, RDF)",
                       'description': "Import syndication feeds (RSS, ATOM, RDF)",
                       'use_external_validation': "true",
                       'streaming_mode': "xml",
                       'use_single_instance': "true"}

        args = [
                URLField("url", "Feed URL", "The URL of the feed to input", empty_allowed=False),
                BooleanField("include_only_changed", "Include only new or changed entries", "Only include entries that has not been indexed yet (won't get items that were already observed)", empty_allowed=False),
                Field("username", "Username", "The username to use for authenticating (only HTTP authentication supported)", none_allowed=True, empty_allowed=True, required_on_create=False, required_on_edit=False),
                Field("password", "Password", "The password to use for authenticating (only HTTP authentication supported)", none_allowed=True, empty_allowed=True, required_on_create=False, required_on_edit=False),
                DurationField("interval", "Interval", "The interval defining how often to import the feed; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False),
                BooleanField("clean_html", "Convert HTML to Text", "Convert HTML to human readable text", empty_allowed=False),
                URLField("proxy", "Proxy URL", "URL for proxy", empty_allowed=True, none_allowed=True, required_on_create=False, required_on_edit=False)
                ]

        ModularInput.__init__(self, scheme_args, args, logger_name='syndication_modular_input', logger_level=logging.INFO)

    @classmethod
    def get_updated_date(cls, entry):

        if 'updated_parsed' in entry:
            #cls.logger.debug("Using date updated_parsed=%s", entry.updated_parsed)
            return entry.updated_parsed

        if 'published_parsed' in entry:
            #cls.logger.debug("Using date published_parsed=%s", entry.published_parsed)
            return entry.published_parsed

        #cls.logger.debug("No date found")
        return None

    @classmethod
    def get_realm_and_auth_type(cls, feed_url, username, password, logger=None):
        """
        Get the realm and authentication type for the given feed.

        Arguments:
        feed_url -- The URL of the feed to retrieve (as a string)
        username -- The username to use when authenticating
        password -- The password to use when authenticating
        logger -- A logger to log failure to parse the header messages
        """

        # Perform request and get the realm and whether or not the view uses HTTP digest or basic authentication
        d = feedparser.parse(feed_url)

        # Make sure we got a result
        if d is None or not hasattr(d, 'status'):
            return None, None

        # If the status isn't 401, then authentication isn't required
        if d.status != 401:
            return None, None

        # Make sure that an auth header exists
        if 'www-authenticate' not in d.headers:
            return None, None

        auth_header = d.headers['www-authenticate']

        # Get the realm and whether it is using basic or digest authentication
        http_auth_re = re.compile("((Digest)|(Basic))( realm=[\"]?([^\"]*)[\"]?)?", re.IGNORECASE)
        match = http_auth_re.search(auth_header)

        # Stop if we couldn't parse the header
        if match is None or len(match.groups()) < 5:
            if logger is not None:
                logger.warn("Unable to parse the HTTP authentication header, header=\"%s\"", auth_header)

            return None, None
        else:
            auth_type = match.groups()[0]
            auth_realm = match.groups()[4]

        return auth_realm, auth_type

    @classmethod
    def get_auth_handler(cls, feed_url, username, password, logger=None):
        """
        Create a URL that will perform authentication for the given feed.

        Arguments:
        feed_url -- The URL of the feed to retrieve (as a string)
        username -- The username to use when authenticating
        password -- The password to use when authenticating
        """

        realm, auth_type = cls.get_realm_and_auth_type(feed_url, username, password, logger)

        # Make the associated auth handler
        if auth_type == None:
            return None
        elif auth_type.lower() == "basic":
            auth_handler = HTTPBasicAuthHandler()
        else:
            auth_handler = HTTPDigestAuthHandler()

        # Set the password
        auth_handler.add_password(realm=realm,
                                  uri=feed_url,
                                  user=username,
                                  passwd=password)

        return auth_handler

    @classmethod
    def get_proxy_handler(cls, proxy, logger=None):
        """
        Create a ProxyHandler object used by urllib.

        Arguments:
        proxy -- Proxy URL
        """

        proxy_handler = None
        mapping = None

        # Make the associated proxy handler
        if proxy == None:
            return None
        else:
            if proxy.scheme is not None and proxy.hostname is not None:
                mapping = {}
                if proxy.scheme == 'http' or proxy.scheme == 'https':
                    mapping["http"] = proxy.netloc
                    mapping["https"] = proxy.netloc
                else:
                    mapping[proxy.scheme] = proxy.netloc

                proxy_handler = ProxyHandler(mapping)

        return proxy_handler

    @classmethod
    def get_feed(cls, feed_url, return_latest_date=False, include_later_than=None, logger=None, username=None, password=None, clean_html=True, proxy=None):
        """
        Get the feed results as a dictionary.

        Arguments:
        feed_url -- The URL of the feed to retrieve (as a string)
        return_latest_date -- Return the date of the latest feed entry as the second item in a tuple
        include_later_than -- Only return the feeds that are after this date
        logger -- The logger to log the data to
        username -- The username to use when authenticating
        password -- The password to use when authenticating
        clean_html -- If true, HTML will be convrted to something human readable
        """

        auth_handler = None
        proxy_handler = None

        # Get an authentication handler if needed
        if username is not None and password is not None:
            auth_handler = cls.get_auth_handler(feed_url, username, password, logger)

        # Get a proxy handler if needed
        if proxy is not None:
            proxy_handler = cls.get_proxy_handler(proxy, logger)

        # Parse the feed
        if auth_handler is not None:
            opener = build_opener(auth_handler)
            feed = opener.open(feed_url)
            d = feedparser.parse(feed)
        elif proxy_handler is not None:
            opener = build_opener(proxy_handler)
            feed = opener.open(feed_url)
            d = feedparser.parse(feed)
        else:
            d = feedparser.parse(feed_url)

        entries = []
        latest_date = None

        # Stop if we didn't get a result
        if d is None or not hasattr(d, 'entries'):
            logger.warn("No entries returned from the feed, url=\"%s\"", feed_url)
        else:
            for entry in d.entries:

                # Get the updated or published date
                entry_date = cls.get_updated_date(entry)

                # Perform the operations that are based on the date
                if entry_date is not None:

                    # If this is the latest one, then save it
                    if latest_date is None or entry_date > latest_date:
                        latest_date = entry_date

                    # If the item is earlier than the date we are to include, then skip it
                    if include_later_than is not None and entry_date <= include_later_than:

                        if logger is not None:
                            logger.debug("Skipping entry with date=%r, since it's not later than latest_date=%r, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), time.strftime('%Y-%m-%dT%H:%M:%SZ', include_later_than), entry.title)

                        continue

                    elif logger is not None and include_later_than is not None:
                        logger.debug("Including entry with date=%r, since it's later than latest_date=%r, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), time.strftime('%Y-%m-%dT%H:%M:%SZ', include_later_than), entry.title)

                    elif logger is not None and include_later_than is None:
                        logger.debug("Including entry with date=%r, since there is no checkpoint date, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), entry.title)

                # Clean up the HTML if requested
                if clean_html:

                    # Clean up the content
                    try:
                        if entry.get('content', None) and entry['content'][0].get('type', 'text/html') == 'text/html' and entry['content'][0].get('value', None):
                            entry['content'][0]['value'] = html2text.html2text(entry['content'][0]['value'])
                    except:
                        logger.warn("Unable to convert the HTML content, field=%s", "value")

                    # Clean up the summary
                    try:
                        if entry.get('summary', None):
                            entry['summary'] = html2text.html2text(entry['summary'])
                    except:
                        logger.warn("Unable to convert the HTML content, field=%s", "summary")

                    # Clean up the summary_detail
                    try:
                        if entry.get('summary_detail', None) and entry['summary_detail'].get('type', 'text/html') == 'text/html' and entry['summary_detail'].get('value', None):
                            entry['summary_detail']['value'] = html2text.html2text(entry['summary_detail']['value'])
                    except:
                        logger.warn("Unable to convert the HTML content, field=%s", "summary_detail")

                entries.append(cls.flatten(entry, sort=True))

        # Return the latest date if requested
        if return_latest_date:
            return entries, latest_date
        else:
            return entries

    @classmethod
    def flatten(cls, item, dictionary=None, name=None, sort=False):
        """
        Take a Python object and flatten it into a list.

        Arguments:
        item -- The Python item to flatten
        dictionary -- The dictionary to populate if you want to start with an existing dictionary
        name -- The name that should be used for appended to the name of the items created
        sort -- If true, the dictionary will be sorted
        """

        if dictionary is None:
            dictionary = {}

        if name is None:
            name = ""

        iterative_name = name

        if len(iterative_name) > 0:
            iterative_name = name + "."

        # Python 2+3 basestring
        try:
            basestring
        except NameError:
            basestring = str

        # Handle dictionaries
        if isinstance(item, dict):
            for key in item:
                cls.flatten(item[key], dictionary, iterative_name + key)

        # Handle date
        elif item.__class__.__name__ == "struct_time":
            dictionary[name] = time.strftime('%Y-%m-%dT%H:%M:%SZ', item)

        # Handle arrays
        elif not isinstance(item, basestring) and isinstance(item, (list, tuple)):
            index = 0

            for entry in item:
                cls.flatten(entry, dictionary, iterative_name + str(index))

                index = index + 1

        # Handle plain values
        elif item in [True, False, None]:
            dictionary[name] = item

        # Handle string values
        else:
            dictionary[name] = str(item)

        # Sort the dictionary
        if sort:
            dictionary = OrderedDict(sorted(dictionary.items(), key=lambda x: x[0]))

        return dictionary

    def save_checkpoint(self, checkpoint_dir, stanza, last_run, last_entry_date):
        """
        Save the checkpoint state.

        Arguments:
        checkpoint_dir -- The directory where checkpoints ought to be saved
        stanza -- The stanza of the input being used
        last_run -- The time when the analysis was last performed
        last_entry_date -- The date of the last entry that was imported
        """

        if last_entry_date is not None:
            self.save_checkpoint_data(checkpoint_dir, stanza, { 'last_run' : last_run,
                                                                'last_entry_date' : time.mktime(last_entry_date)
                                                               })
        else:
            self.save_checkpoint_data(checkpoint_dir, stanza, { 'last_run' : last_run })

    def run(self, stanza, cleaned_params, input_config):

        # Make the parameters
        interval = cleaned_params["interval"]
        feed_url = cleaned_params["url"]
        include_only_changed = cleaned_params.get("include_only_changed", True)
        sourcetype = cleaned_params.get("sourcetype", "syndication")
        username = cleaned_params.get("username", None)
        password = cleaned_params.get("password", None)
        host = cleaned_params.get("host", None)
        index = cleaned_params.get("index", "default")
        clean_html = cleaned_params.get("clean_html", False)
        proxy = cleaned_params.get("proxy", None)
        source = stanza

        if self.needs_another_run(input_config.checkpoint_dir, stanza, interval):

            # Get the date of the latest entry imported
            try:
                checkpoint_data = self.get_checkpoint_data(input_config.checkpoint_dir, stanza, throw_errors=True)
            except IOError:
                checkpoint_data = None
            except ValueError:
                self.logger.exception("Exception generated when attempting to load the check-point data")
                checkpoint_data = None

            # Try to load the last entry date from the checkpoint data
            if include_only_changed and checkpoint_data is not None and 'last_entry_date' in checkpoint_data:
                last_entry_date = time.localtime(checkpoint_data['last_entry_date'])
                self.logger.debug("Loaded latest entry date from checkpoint, last_entry_date=%s", time.strftime('%Y-%m-%dT%H:%M:%SZ', last_entry_date))
            else:
                last_entry_date = None

            # Get the feed information
            results = None
            last_entry_date_retrieved = None

            try:
                results, last_entry_date_retrieved = self.get_feed(feed_url.geturl(), return_latest_date=True, include_later_than=last_entry_date, logger=self.logger, username=username, password=password, clean_html=clean_html, proxy=proxy)
            except:
                self.logger.exception("Unable to get the feed, url=%s", feed_url.geturl())
                result = None

            if last_entry_date_retrieved is not None:
                self.logger.debug("Latest date from feed retrieved, last_entry_date_retrieved=%i", time.mktime(last_entry_date_retrieved))
            else:
                self.logger.debug("Latest date from feed was not retrieved")

            # Process the results
            if results is not None:
                self.logger.info("Successfully retrieved feed entries, count=%i, url=%s", len(results), feed_url.geturl())

                # Output the event
                for result in results:
                    # Send the event
                    if self.OUTPUT_USING_STASH:

                        # Write the event as a stash new file
                        writer = StashNewWriter(index=index, source_name=source, file_extension=".stash_syndication_input", sourcetype=sourcetype, host=host)
                        self.logger.debug("Wrote stash file=%s", writer.write_event(result))

                    else:
                        #self.logger.debug("Generating event, count=%i, url=%s", len(results), feed_url.geturl())
                        self.output_event(result, stanza, index=index, source=source, sourcetype=sourcetype, host=host, unbroken=True, close=True)

                # Get the time that the input last ran
                if checkpoint_data is not None and 'last_ran' in checkpoint_data:
                    last_ran = checkpoint_data['last_ran']
                else:
                    last_ran = None

                # Show a warning if no results were loaded but the last entry date is being updated (that shouldn't happen)
                if len(results) == 0 and last_entry_date_retrieved is not None and last_entry_date is not None and last_entry_date_retrieved > last_entry_date:
                    self.logger.warn("Latest entry date changed even though no entries were loaded, last_entry_date=$s, last_entry_date_retrieved=%s", last_entry_date, last_entry_date_retrieved)

                # Handle the case where no last_entry_date could be loaded
                if last_entry_date is None:
                    if results == None:
                        self.logger.warn("Latest entry date was not found, no results found")
                    else:
                        result_count = len(results)
                        last_entry_date = time.localtime()
                    
                        self.logger.warn("Latest entry date was not found, result_count=$i", result_count)

                # Set the last last_entry_date to the lastest entry retrieved
                elif last_entry_date_retrieved is not None and last_entry_date_retrieved > last_entry_date:
                    last_entry_date = last_entry_date_retrieved

                # Save the checkpoint so that we remember when we last
                self.save_checkpoint(input_config.checkpoint_dir, stanza, self.get_non_deviated_last_run(last_ran, interval, stanza), last_entry_date)

if __name__ == '__main__':
    try:
        syndication_input = SyndicationModularInput()
        syndication_input.execute()
        sys.exit(0)
    except Exception as exception:

        # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
        if syndication_input is not None:
            syndication_input.logger.exception("Unhandled exception was caught, this may be due to a defect in the script")

        raise exception
