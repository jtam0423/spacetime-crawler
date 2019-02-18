import logging
from datamodel.search.JasonhtTychua_datamodel import JasonhtTychuaLink, OneJasonhtTychuaUnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time
from uuid import uuid4
import urllib2

import sys

from urlparse import urlparse, parse_qs
from uuid import uuid4

logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"

SUBDOMAINS = {}
MAX_COUNT = 0
MAX_URL = ""
COUNT = 0

@Producer(JasonhtTychuaLink)
@GetterSetter(OneJasonhtTychuaUnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "JasonhtTychua"

    def __init__(self, frame):
        self.app_id = "JasonhtTychua"
        self.frame = frame

    def initialize(self):
        self.count = 0
        links = self.frame.get_new(OneJasonhtTychuaUnProcessedLink)
        if len(links) > 0:
            print "Resuming from the previous state."
            self.download_links(links)
        else:
            l = JasonhtTychuaLink("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneJasonhtTychuaUnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            increaseCount()
            links = extract_next_links(downloaded)
            for l in links:
                if is_valid(l):
                    self.frame.add(JasonhtTychuaLink(l))

    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")

def increaseCount():
    global COUNT
    COUNT = COUNT + 1
    print COUNT
    
def extract_next_links(rawDataObj):
    global SUBDOMAINS
    global MAX_COUNT
    global MAX_URL
    
    outputLinks = []
    '''
    rawDataObj is an object of type UrlResponse declared at L20-30
    datamodel/search/server_datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.
    
    Suggested library: lxml    
    '''
    
    try:
        content = rawDataObj.content
        element = html.fromstring(content)
        out = html.fromstring(html.tostring(element))

        l_count = 0
        for l in out.iterlinks():
            parsed = urlparse(l[2])
            if parsed.scheme == 'http' and 'ics.uci.edu' in parsed.netloc:
                if parsed.netloc not in SUBDOMAINS:
                    SUBDOMAINS[parsed.netloc] = 1
                else:
                    SUBDOMAINS[parsed.netloc] = SUBDOMAINS[parsed.netloc] + 1
            outputLinks.append(l[2])
            l_count = l_count + 1
            write_outfile()
        
        if (l_count > MAX_COUNT):
            MAX_COUNT = l_count
            MAX_URL = rawDataObj.url
            
    except:
        pass

    return outputLinks
    
#    try:
#        page = urllib2.urlopen(rawDataObj.url.encode('utf-8')).read()
#    except urllib2.URLError:
#        print "Invalid URL"
#    else:
#        if int(rawDataObj.http_code) < 400:
#            content = html.fromstring(page)
#            content.make_links_absolute(rawDataObj.url)
#
#            for l in content.iterlinks():
#                parsed = urlparse(l[2])
#                outputLinks.append(l[2])
#
#
##                if parsed.scheme == 'http' and 'ics.uci.edu' in parsed.netloc:
##                    if parsed.netloc not in SUBDOMAINS:
##                        SUBDOMAINS[parsed.netloc] = 1
##                    else:
##                        SUBDOMAINS[parsed.netloc] = SUBDOMAINS[parsed.netloc] + 1
##                    outputLinks.append(l[2])
#
#    return outputLinks


def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        return False
    
    #calendar killer
    if "calendar" in url.lower():
        print ("calendar")
        return False
    
    #if exceeds 350 in length
    if len(url) > 350:
        print ("length")
        return False
    
    #check if absolute
    if not is_absolute(url):
        print (url, ": Absolute URL Error")
        return False
    
    if "events" in url:
        print("events")
        return False
    
#    #syntax
#    if "?" in url and "=" in url:
#        print (url, ": Query Parameter Error")
#        return False
    
#    #handle multiple paths
#    paths = parsed.path
#    
#    paths_list = paths.split("/")
#    
#    if len(paths_list) > 10:
#        print(url, ": Multiple Paths Error")

    list_paths = parsed.path.split('/')
    for item in list_paths:
        if item != '' and list_paths.count(item) > 1:
            print ("Multiple Path Error")
            return False

    
    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        return False

def is_absolute(url):
    return bool(urlparse(url).netloc)

def write_outfile():
    outfile = open("analysis.txt", 'w')
    outfile.write('Subdomains: ' + str(SUBDOMAINS))
    outfile.write("\nMax Outlink Count: " + str(MAX_COUNT))
    outfile.write("\nMax Outlink URL: " + MAX_URL)