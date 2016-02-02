import sys
import time
import re
import urllib2

from syndication_app.modular_input import ModularInput, URLField, DurationField, BooleanField, Field
from syndication_app import feedparser

class SyndicationModularInput(ModularInput):
    """
    The syndication input facilitates import of feeds into Splunk.
    """
    
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
                DurationField("interval", "Interval", "The interval defining how often to import the feed; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False)
                ]
        
        ModularInput.__init__( self, scheme_args, args, logger_name='syndication_modular_input' )
        
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
    def get_realm_and_auth_type(cls, feed_url, username, password):
        
        # Perform request and get the realm and whether or not the view uses HTTP digest or basic authentication
        d = feedparser.parse(feed_url)
        
        # If the status isn't 401, then authentication isn't required
        if d.status != 401:
            return None, None
        
        auth_header = d.headers['www-authenticate']
        
        # Get the realm and whether it is using basic or digest authentication
        http_auth_re = re.compile("((Digest)|(Basic))( realm=[\"]?([^\"]*)[\"]?)?")
        match = http_auth_re.search(auth_header)
        
        auth_type = match.groups()[0]
        auth_realm = match.groups()[4]
        
        return auth_realm, auth_type
        
    @classmethod
    def get_auth_handler(cls, feed_url, username, password):
        
        realm, auth_type = cls.get_realm_and_auth_type(feed_url, username, password)
        
        # Make the associated auth handler
        if auth_type == None:
            return None
        elif auth_type.lower() == "basic":
            auth_handler = urllib2.HTTPBasicAuthHandler()
        else:
            auth_handler = urllib2.HTTPDigestAuthHandler()
        
        # Set the password
        auth_handler.add_password(realm=realm,
                                        uri=feed_url,
                                        user=username,
                                        passwd=password)

        return auth_handler
        
    @classmethod
    def get_feed(cls, feed_url, return_latest_date=False, include_later_than=None, logger=None, username=None, password=None):
        
        auth_handler = None
        
        # Get an authentication handler if needed
        if username is not None and password is not None:
            auth_handler = cls.get_auth_handler(feed_url, username, password)
            
        # Parse the feed
        if auth_handler is not None:
            opener = urllib2.build_opener(auth_handler) 
            feed = opener.open(feed_url)
            d = feedparser.parse(feed)
        else:
            d = feedparser.parse(feed_url)
        
        entries = []
        latest_date = None
        
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
                        logger.debug("Skipping entry with date=%r, since its not later than latest_date=%r, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), time.strftime('%Y-%m-%dT%H:%M:%SZ', include_later_than), entry.title)
                    
                    continue
                
                elif logger is not None and include_later_than is not None:
                    logger.debug("Including entry with date=%r, since its not later than latest_date=%r, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), time.strftime('%Y-%m-%dT%H:%M:%SZ', include_later_than), entry.title)
                
                elif logger is not None and include_later_than is None:
                    logger.debug("Including entry with date=%r, since its not later than latest_date=%r, title=\"%s\"", time.strftime('%Y-%m-%dT%H:%M:%SZ', entry_date), "none", entry.title)
                      
            entries.append(cls.flatten(entry))
        
        # Return the latest date if requested
        if return_latest_date:
            return entries, latest_date
        else:
            return entries
    
    @classmethod
    def flatten(cls, item, dictionary=None, name=None):
        
        if dictionary is None:
            dictionary = {}
        
        if name is None:
            name = ""
        
        iterative_name = name
            
        if len(iterative_name) > 0:
            iterative_name = name + "."
        
        # Handle dictionaries
        if isinstance(item, dict):
            for key in item:
                cls.flatten(item[key], dictionary,  iterative_name + key)
        
        # Handle arrays
        elif not isinstance(item, basestring) and isinstance(item, (list, tuple)):
            
            index = 0
            
            for a in item:
                cls.flatten(a, dictionary, iterative_name + str(index))
                
                index = index + 1
                
                
        # Handle plain values
        elif item in [True, False, None]:
            dictionary[name] = item
            
        # Handle date
        elif item.__class__.__name__ == "struct_time":
            dictionary[name] = time.strftime('%Y-%m-%dT%H:%M:%SZ', item)
            
        # Handle string values
        else:
            dictionary[name] = str(item)
            
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
        interval             = cleaned_params["interval"]
        feed_url             = cleaned_params["url"]
        include_only_changed = cleaned_params.get("include_only_changed", True)
        sourcetype           = cleaned_params.get("sourcetype", "syndication")
        username             = cleaned_params.get("username", None)
        password             = cleaned_params.get("password", None)
        host                 = cleaned_params.get("host", None)
        index                = cleaned_params.get("index", "default")
        source               = stanza
        
        if self.needs_another_run(input_config.checkpoint_dir, stanza, interval):
            
            # Get the date of the latest entry imported
            try:
                checkpoint_data = self.get_checkpoint_data(input_config.checkpoint_dir, stanza, throw_errors=True)
            except IOError:
                checkpoint_data = None
            except ValueError:
                self.logger.exception("Exception generated when attempting to load the check-point data")
                checkpoint_data = None
            
            if include_only_changed and checkpoint_data is not None and 'last_entry_date' in checkpoint_data:
                last_entry_date = time.localtime(checkpoint_data['last_entry_date'])
            else:
                last_entry_date = None
            
            # Get the feed information
            results, last_entry_date_retrieved = self.get_feed(feed_url.geturl(), return_latest_date=True, include_later_than=last_entry_date, logger=self.logger, username=username, password=password)
            self.logger.info("Successfully retrieved feed entries, count=%i, url=%s", len(results), feed_url.geturl())
            
            # Output the event
            for result in results:
                self.output_event(result, stanza, index=index, source=source, sourcetype=sourcetype, host=host, unbroken=True, close=True)
                
            # Get the time that the input last ran
            if checkpoint_data is not None and 'last_ran' in checkpoint_data:
                last_ran = checkpoint_data['last_ran']
            else:
                last_ran = None
            
            # Save the checkpoint so that we remember when we last
            if last_entry_date_retrieved is not None and last_entry_date_retrieved > last_entry_date:
                last_entry_date = last_entry_date_retrieved
            
            self.save_checkpoint(input_config.checkpoint_dir, stanza,  self.get_non_deviated_last_run(last_ran, interval, stanza), last_entry_date)
            
if __name__ == '__main__':
    try:
        syndication_input = SyndicationModularInput()
        syndication_input.execute()
        sys.exit(0)
    except Exception as e:
        
        # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
        if syndication_input is not None:
            syndication_input.logger.exception("Unhandled exception was caught, this may be due to a defect in the script")
        
        raise e