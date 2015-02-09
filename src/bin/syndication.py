import sys
import json
import time

from syndication_app.modular_input import ModularInput, URLField, DurationField
from syndication_app import feedparser

class SyndicationModularInput(ModularInput):
    """
    The syndication input facilitates import of feeds into Splunk.
    """
    
    def __init__(self):

        scheme_args = {'title': "Syndication Feed (RSS, ATOM, RDF)",
                       'description': "Allows you to import feeds (RSS, ATOM, RDF) into Splunk",
                       'use_external_validation': "true",
                       'streaming_mode': "xml",
                       'use_single_instance': "true"}
        
        args = [
                URLField("url", "Feed URL", "The URL of the feed to input", empty_allowed=False),
                DurationField("interval", "Interval", "The interval defining how often to import the feed; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False)
                ]
        
        ModularInput.__init__( self, scheme_args, args, logger_name='syndication_modular_input' )
        
    @classmethod
    def get_feed(cls, feed_url):
        d = feedparser.parse(feed_url)
        
        entries = []
        
        for entry in d.entries:
            entries.append(cls.flatten(entry))
        
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
            
        
    def run(self, stanza, cleaned_params, input_config):
        
        # Make the parameters
        interval        = cleaned_params["interval"]
        feed_url        = cleaned_params["url"]
        sourcetype      = cleaned_params.get("sourcetype", "syndication")
        host            = cleaned_params.get("host", None)
        index           = cleaned_params.get("index", "default")
        source          = stanza
        
        if self.needs_another_run(input_config.checkpoint_dir, stanza, interval):
            
            # Get the feed information
            results = self.get_feed(feed_url.geturl())
            self.logger.info("Got results, count=%i, url=%s", len(results), feed_url.geturl())
            
            # Output the event
            for result in results:
                self.output_event(result, stanza, index=index, source=source, sourcetype=sourcetype, host=host, unbroken=True, close=True)
                
            # Get the time that the input last ran
            last_ran = self.last_ran(input_config.checkpoint_dir, stanza)
            
            # Save the checkpoint so that we remember when we last
            self.save_checkpoint_data(input_config.checkpoint_dir, stanza, {"last_run" : self.get_non_deviated_last_run(last_ran, interval, stanza) })
        
            
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