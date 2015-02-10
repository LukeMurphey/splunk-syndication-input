[syndication://default]
* Configure an input for importing syndication feeds (RSS, ATOM, RDF)

url = <value>
* The url of the feed

interval = <value>
* Indicates how often to perform the import

include_only_changed = <value>
* If true, then items will not be obtained if the are older than the last entry seen before
* This prevents re=indexing the same items repeatedly