# Bangbot
Created By Alex Guerra

Bangbot is an easily extensible python script for finding and testing passwords on the internet. It is largely composed of four types of classes that you'll need to extend in order to make it do what you want: Bots, Searchers, Scrapers, and Testers. Each of these types of classes is detailed below. A simple outline goes a bit like this: a searcher is an iterator that finds webpages that it thinks are likely to have passwords, a scraper takes those pages found by the searcher and searchers them for passwords, a tester takes all of the passwords found by the scraper and checks them for validity, and a bot encapsulates all of this logic (along with an easy way to store it after it's collected) in a couple of easy to use functions.

## Bots

Bots are the glue of the script. Each AbstractBot subclass can be outfitted with multiple page finders, multiple searchers and a tester. The idea is to be able to quickly assemble a new bot from canned components and be able to easily extend it as new searchers and scrapers become available. Every bot **must** extend from AbstractBot class and must set a self.sitename if they persist data to the database using dbsync.

### AbstractBot

#### Methods

*  **run()** - Tests each combination found by each scraper on each page found by each searcher and adds the working results to self.combinations
*	**dbsync()** - Persists all combinations found by 'run' to the database. The default database file is bangbot.db

#### Attributes

*	*searchers* - List of searcher objects used by run
*	*scrapers* - List of scraper objects used by run
*	*tester* - Tester object used by run
*	*connection* - Static variable that is a sqlite database connection. The default is bangbot.db
*	*combinations* - Set of username/password combinations in the form (username,password)
*	*sitename* - Name of the site that the bot is working on. Used as a column in the database to identify the site the combinations belong to.

## Searchers

Searchers find and return webpages that they think are likely to have usernames and passwords. Searchers should be iterable; every time next is called you'll return the html contents of the next webpage you find. To reduce requests, webpages are cached using a static class variable 'cache' in AbstractSearcher. In order to make use of this cache, you **must** use the get_webpage function in order to grab the contents of a webpage.

### AbstractSearcher

## Scrapers

Scrapers take the html of webpages found by searchers and scrapes them for possible username/password combinations. Scrapers must return a set of tuples in the form (username, password). Tuples must be used instead of dicts because dicts are not hashable and sets can only take hashable items or something like that.

## Testers

Testers test username and password combinations for validity. The test method should take a username and password in the form of a tuple (username, password). For the most part, testers will have to be bespoke for the bot they're fitted to, though the BasicAuthTester class can cover many older sites still using http authentication quite easily.

## Database Schema

The database is an sqlite3 database file. It has five columns

*	id INT PRIMARY AUTO-INCREMENT - The combination id
*	username VARCHAR(50) - The username
*	passwords VARCHAR(50) - The password
*	site VARCHAR(50) - The sitename provided by the bot
*	last_checked DATE_TIME DEFAULT CURRENT_TIMESTAMP - The last time this combination was tested

Contact me at alex@heyimalex.com