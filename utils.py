__author__ = 'mikfig'

import httplib
from HTMLParser import HTMLParser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def parseURL(url, defaultPrefix = '', defaultHostname = '', defaultDirectory = ''):
    prefixSeperator = "://"

    try:
        prefix = url[:url.index(prefixSeperator)]
    except ValueError:
        prefix = defaultPrefix

        if url[0] != '/':
            url = defaultDirectory + url
        if url[:2] != '//':
            url = prefix + prefixSeperator + defaultHostname + url
        else:
            url = prefix + ':' + url

    hostname = url[url.index(prefixSeperator) + len(prefixSeperator):]

    try:
        requestSeparator = hostname.index('/')
        request = hostname[requestSeparator:]
        hostname = hostname[:requestSeparator]
    except ValueError:
        request = "/"

    return [url, prefix, hostname, request]

def parseHostname(hostname):
    try:
        lastDot = hostname.rindex('.')
    except ValueError:
        return hostname

    tld = hostname[lastDot + 1:]
    domain = hostname[:lastDot]

    try:
        subdomainSeparator = domain.rindex('.')
    except ValueError:
        return ['', domain, tld]

    subdomain = domain[:subdomainSeparator]
    domain = domain[subdomainSeparator + 1:]

    return [subdomain, domain, tld]

def getParsedLinksInHTML(html, defaultPrefix, defaultHostname, defaultDirectory):
    linkList = []
    parser = LinkExtractor(linkList)
    parser.feed(html)
    parsedLinks = map(lambda url: parseURL(url, defaultPrefix, defaultHostname, defaultDirectory), linkList)
    parsedLinks = map(lambda link: [link[0], link[1], [link[2]] + parseHostname(link[2]), link[3]], parsedLinks)
    return parsedLinks

def getHTTPResponse(url):
    parsedURL = parseURL(url)

    if parsedURL[1] == "https":
        conn = httplib.HTTPSConnection(parsedURL[2])
    elif parsedURL[1] == "http":
        conn = httplib.HTTPConnection(parsedURL[2])
    else:
        return ("", url)

    conn.request("GET", parsedURL[3])
    r1 = conn.getresponse()

    redirectStatusCodes = (301, 302, 307, 308)

    if r1.status == 200:
        return (r1.read(), url)
    elif r1.status in redirectStatusCodes:
        headers = r1.getheaders()
        locationHeader = "location"
        for i in range(0, len(headers)):
            if str.lower(headers[i][0]) == locationHeader:
                return getHTTPResponse(headers[i][1])
        return ("", url)
    else:
        return ("", url)

class LinkExtractor(HTMLParser):
    def __init__(self, linkList):
        HTMLParser.__init__(self)
        self.linkList = linkList
    def handle_starttag(self, tag, attrs):
        linkAttrs = ["src", "href"]
        for attr in attrs:
            if attr[0] in linkAttrs:
                self.linkList.append(attr[1])
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        pass
		
def sendEmail(strTo, strFrom, strSubject, strTxtBody, strHtmlBody, smtpServer, emailLogin):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = strSubject
    msg['From'] = strFrom
    msg['To'] = strTo
    msg.attach(MIMEText(strTxtBody, 'plain'))
    msg.attach(MIMEText(strHtmlBody, 'html'))

    mailServer = smtplib.SMTP(smtpServer[0], smtpServer[1])
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(emailLogin[0], emailLogin[1])
    mailServer.sendmail(strFrom, [strTo], msg.as_string())