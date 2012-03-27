# Bangbot
Created By Alex Guerra

Bangbot is an easily extensible python script for finding and testing passwords on the internet. It is largely composed of four types of classes that you'll need to extend in order to make it do what you want: Bots, Searchers, Scrapers, and Testers. Each of these types of classes is detailed below.

## Bots

Bots are the glue of the script. Each AbstractBot subclass can be outfitted with multiple page finders, multiple searchers and a tester. The idea is to be able to quickly assemble a new bot from canned components and be able to easily extend it as new searchers and scrapers become available. Every bot **must** extend from AbstractBot class and must set a self.sitename if they persist data to the database using dbsync.

### AbstractBot

*	**run()**: Tests each combination found by each scraper on each page found by each searcher and add the working results to self.combinations
*	**dbsync()**: Persists all combinations found by 'run' to the database. The default database file is bangbot.db

*	searchers:
*	scrapers: 
*	tester:
*	connection:
*	combinations:
*	sitename: 

## Searchers

Searchers find and return webpages that they think are likely to have usernames and passwords. Searchers should be iterable; every time next is called you'll return the html contents of the next webpage you find. To reduce requests, webpages are cached using a static class variable 'cache' in AbstractSearcher. In order to make use of this cache, you **must** use the get_webpage function in order to grab the contents of a webpage.

### AbstractSearcher

## Scrapers

Scrapers take the html of webpages found by searchers and scrapes them for possible username/password combinations. Scrapers must return a set of tuples in the form (username, password). Tuples must be used instead of dicts because dicts are not hashable and sets can only take hashable items or something like that.

## Testers

Testers test username and password combinations for validity. The test method should take a username and password in the form of a tuple (username, password). For the most part, testers will have to be bespoke for the bot they're fitted to, though the BasicAuthTester class can cover many older sites still using http authentication quite easily.

Contact me at alex@heyimalex.com