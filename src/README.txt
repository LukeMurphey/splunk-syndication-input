================================================
Overview
================================================

This app provides a mechanism for importing syndication feeds into Splunk (RSS, ATOM, RDF).



================================================
Configuring Splunk
================================================

This app exposes a new input type that can be configured in the Splunk Manager. To configure it, create a new input in the Manager under Data inputs � Syndication.



================================================
Getting Support
================================================

Go to the following website if you need support:

     http://splunk-base.splunk.com/apps/2630/answers/

You can access the source-code and get technical details about the app at:

     http://lukemurphey.net/projects/splunk-syndication-input/



================================================
Change History
================================================

+---------+------------------------------------------------------------------------------------------------------------------+
| Version |  Changes                                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------------+
| 0.5     | Initial release                                                                                                  |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.0     | Added ability to import feeds that require authentication                                                        |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.0.1   | Fixed issue where the source type cannot be selected correctly                                                   |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.0.2   | Hardened the input to recover from feeds that don't have an www-authenticate header and those with no entries    |
+---------+------------------------------------------------------------------------------------------------------------------+
