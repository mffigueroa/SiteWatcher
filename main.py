__author__ = 'mikfig'

import hashlib
import os
import re
from base64 import b64encode
from utils import *

# the list of the sites to be checked
# each tuple consists of the sitename, the site hostname, and the URL to start from
sites = [('TreeHacks', 'treehacks', 'https://www.treehacks.com'),
         ('HackPrinceton', 'hackprinceton', 'http://hackprinceton.com')]
		 
# --- NOTE ---
# these values all need to be set
# a tuple giving the email addresses to notify on a change
emailRecipients = ('notifyme1@gmail.com', 'notifyme2@gmail.com')
# the login info for the email we'll send it from
emailLogin = ('someemail', 'somepassword')
# the email address to be sent from
emailFrom = 'someemail@somedomain.com'
# the smtp server connection information
smtpServer = ('smtp.somedomain.com', 587)

def getURLHashFilename(url):
    m = hashlib.md5()
    m.update(url)
    return "url-" + b64encode(m.digest(), "!#") + ".bin"

def checkHTMLAgainstStoredHash(url, html):
    filename = getURLHashFilename(url)

    m = hashlib.md5()
    m.update(html)

    if os.path.isfile(filename):
        fp = open(filename, "rb")
        oldHash = fp.read()

        if oldHash != m.digest():
            print "URL has changed: " + url

            fp.close()
            fp = open(filename, "wb")
            fp.write(m.digest())

            return True
        else:
            return False
    else:
        print "New URL: " + url
        fp = open(filename, "wb")
        fp.write(m.digest())

        return True



for site in sites:
    currDomain = site[1]
    urlsToCheck = [parseURL(site[2])]
    urlsAlreadyChecked = []
    changedUrls = []

    while len(urlsToCheck) > 0:
        url = urlsToCheck.pop()
        
        if url[0] in urlsAlreadyChecked:
            continue
        
        print 'Checking URL: ' + url[0]
        response = getHTTPResponse(url[0])
        urlsAlreadyChecked.append(url[0])

        urlParts = parseURL(response[1], url[1], url[2], url[3])

        # If we get some weird redirect outside the domain, ignore it
        if parseHostname(urlParts[2])[1] != currDomain:
            continue

        if checkHTMLAgainstStoredHash(url[0], response[0]):
            changedUrls.append(url[0])

        links = getParsedLinksInHTML(response[0], url[1], url[2], url[3])

        currDirectory = re.search('[^?]*/', urlParts[3]).group(0)

        for link in links:
            if link[2][2] == currDomain:
                urlsToCheck.append((link[0], link[1], link[2][0], currDirectory))

    if len(changedUrls) > 0:
        text = site[0] + ' has changed:'
        html = """\
        <html>
        <body>
        <h1>""" + site[0] + " has changed...</h1><br />"

        for i in range(0, len(changedUrls)):
            try:
                filename = changedUrls[i][ changedUrls[i].rfind('/'): ]
            except ValueError:
                filename = changedUrls[i]

            text += '\n' + filename
            html += '<a href="' + changedUrls[i] + '">' + filename + '</a><br />'

        html += """\
        </body>
        </html>
        """
        
        for emailRecipient in emailRecipients:
            sendEmail(emailRecipient, emailFrom, site[0] + ' has changed', text, html, smtpServer, emailLogin)