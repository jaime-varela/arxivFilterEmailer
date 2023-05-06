import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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