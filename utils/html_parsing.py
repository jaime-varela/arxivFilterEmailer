import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import re
# Set of utilities for Arxiv filter and emailer

## very specialized html stripper (DO NOT USE ANYWHERE ELSE)
def strip_html(verboseAuthor):
    begind = verboseAuthor.find("\">")
    endind = verboseAuthor.find("</a>")
    return verboseAuthor[begind+2:endind]

def wrapWordsInTags(text,words,startTag,endTag):
    loweredWords = map(lambda word : word.lower(),words)
    newText = text
    for word in loweredWords:
        newText = newText.replace(word,startTag + word + endTag )
        newText = newText.replace(word.capitalize(),startTag + word.capitalize() + endTag )
        newText = newText.replace(word.capitalize(),startTag + word.title() + endTag )

    return newText


def htmlBoldWordsInText(text,words):
    ''' adds html bold tags around the words in text which are in the words set'''
    return wrapWordsInTags(text,words,"""<b>""","""</b>""")



def sendHtmlEmailFromGoogleAccount(toEmail, fromEmail, subject, plainText,htmlText, username,password):
    me = fromEmail
    you = toEmail

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = you

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plainText, 'plain')
    part2 = MIMEText(htmlText, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    username = username
    password = password

    mail.login(username,password)
    mail.sendmail(me, you, msg.as_string())
    mail.quit()


from enum import Enum
class MatchType(Enum):
    AUTHOR=1
    TITLE=2
    SUMMARY=3
    NONE=4

## filters
def EntryMatch(entry,words,authors):
    # author has the highest priority
    if(any(entry['author'].find(author) > 0 for author in authors)): return MatchType.AUTHOR
    if(any(entry['title'].lower().find(word.lower()) > 0 for word in words)): return MatchType.TITLE
    if(any(entry['summary'].lower().find(word.lower()) > 0 for word in words)): return MatchType.SUMMARY
    return MatchType.NONE


def construct_entry_text(entry,matchType, words,authors):
    result = ""
    html = ""
    TITLE = entry['title'][0:entry['title'].find("(arXiv:")]
    result += TITLE + "\n \t"
    sep = ", "
    entryAuthors = entry['author'].split(sep)
    entryAuthors = [strip_html(entry) for entry in entryAuthors]
    result += sep.join(entryAuthors) + "\n \n"
    result += entry['summary'][3:-4] + "\n \n"
    ## html entry
    html += """<div>"""
    html += """<p style="color:blue;font-size:1.17em;"><b><a href=\"""" + entry['id'] + """\">""" + wrapWordsInTags(TITLE, words,"""<span style="color:darkblue">""","""</span>""") + """</a></b></p>"""
    if(matchType != MatchType.AUTHOR):
        html += """<p><i>""" + sep.join(entryAuthors) + """<i></p><br>"""
    else:
        html += """<p><i>"""
        for authName in entryAuthors:
            if any(authName.find(author) >= 0 for author in authors):
                html += """<b>""" + authName + """</b>""" + " , "
            else:
                html += authName + " , "
        html = html[:len(html)-2]
        html +=  """<i></p><br>"""
    html += """<p>""" + htmlBoldWordsInText(entry['summary'][3:-4], words)+ """</p>"""
    html += """<br><br></div>"""
    return html, result

def html_to_text(html_text):
    # Use BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    # Use regular expressions to remove newlines
    text = re.sub('\n', ' ', text)
    return text