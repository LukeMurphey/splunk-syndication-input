================================================
Overview
================================================

This app provides a mechanism for importing syndication feeds into Splunk (RSS, ATOM, RDF).



================================================
Configuring Splunk
================================================

Install this app into Splunk by doing the following:

  1. Log in to Splunk Web and navigate to "Apps » Manage Apps" via the app dropdown at the top left of Splunk's user interface
  2. Click the "install app from file" button
  3. Upload the file by clicking "Choose file" and selecting the app
  4. Click upload
  5. Restart Splunk if a dialog asks you to

Once the app is installed, you can use the app by configuring a new input:
  1. Navigate to "Settings » Data Inputs" at the menu at the top of Splunk's user interface.
  2. Click "Syndication"
  3. Click "New" to make a new instance of an input



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
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.0.3   | Improved handling of time fields by adding updated_epoch and published_epoch fields                              |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.1     | Added search command for retrieving syndication feeds from SPL (called "feedstail")                              |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2     | Licensed has been changed to the GNU GPL due to the inclusion of html2text                                       |
|         | Adding ability to convert HTML to readable text (Markdown)                                                       |
|         | Fixed issue where the output could break incorrectly when the content contains HTML                              |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.1   | Fixed crash that occurred when an invalid HTTP header was received                                               |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.2   | Adding support for Python 2 and 3                                                                                |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.3   | Updating the mod input library to 2.1.13                                                                         |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.4   | Making the library recover better from errors                                                                    |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.5   | Updating the mod input library to 2.1.14                                                                         |
|         | Improving appinspect issues                                                                                      |
|         | Improving handling of cases in which the latest entry date could not be found                                    |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.6   | Fixing issue that prevented a proxy server from working                                                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.2.7   | App now recognizes the dates of the feed entries better                                                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.3.0   | Improved cloud support                                                                                           |
|---------|------------------------------------------------------------------------------------------------------------------|
| 1.3.1   | Fixed issue with Splunk 9.3 by updating the feedparser library to 6.0.11                                         |
+---------+------------------------------------------------------------------------------------------------------------------+
