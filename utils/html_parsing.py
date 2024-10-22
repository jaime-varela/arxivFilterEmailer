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


def match_type_to_description(match_enum: MatchType) -> str:
    if match_enum == MatchType.AUTHOR:
        return 'author'
    elif match_enum == MatchType.TITLE:
        return 'title'
    elif match_enum == MatchType.SUMMARY:
        return 'summary'
    return ''

def description_to_match_type(desc: str) -> MatchType:
    if desc == 'author':
        return MatchType.AUTHOR
    elif desc == 'title':
        return MatchType.TITLE
    elif desc == 'summary':
        return MatchType.SUMMARY
    return MatchType.NONE



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
    TITLE = entry['title']
    result += TITLE + "\n \t"
    sep = ", "
    entryAuthors = entry['author'].split(sep)
    entryAuthors = [entry for entry in entryAuthors]
    result += sep.join(entryAuthors) + "\n \n"
    summary_text = entry['summary'][entry['summary'].find("Abstract:")+9:]
    result += summary_text + "\n \n"
    ## html entry
    html += """<div>"""
    html += """<p style="color:blue;font-size:1.17em;"><b><a href=\"""" + entry['link'] + """\">""" + wrapWordsInTags(TITLE, words,"""<span style="color:darkblue">""","""</span>""") + """</a></b></p>"""
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
    html += """<p>""" + htmlBoldWordsInText(summary_text, words)+ """</p>"""
    html += """<br><br></div>"""
    return html, result

def html_to_text(html_text):
    # Use BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    # Use regular expressions to remove newlines
    text = re.sub('\n', ' ', text)
    return text

def construct_similarity_entry(entry_title,entry_summary,entry_link, target_title,target_summary,target_link):

    #<a href=\"""" + entry['id'] + """\">""" + wrapWordsInTags(TITLE, words,"""<span style="color:darkblue">""","""</span>""") + """</a>
    html_template = '''
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 10px; border: 1px solid black;">
            <h2><a href="{link1}">{title1}</a></h2>
            <p>{abstract1}</p>
          </td>
          <td style="padding: 10px; border: 1px solid black; color: #888888;">
            <h2><a href="{link2}" style="color: #888888;">{title2}</a></h2>
            <p>{abstract2}</p>
          </td>
        </tr>
      </table>
    '''    
    text_res = entry_title + "\n" + entry_summary + "\n" + target_title + "\n" + target_summary
    html_code = html_template.format(title1=entry_title,
                                     abstract1=entry_summary,
                                     title2=target_title,
                                     abstract2=target_summary,
                                     link1=entry_link,
                                     link2=target_link)
    return html_code,text_res


def construct_email_from_saved_entry_list(entry_list,words,authors):

    result = ""
    html = """\
    <html>
      <head></head>
      <body>
    """
    for entry_value in entry_list:
        matchType = description_to_match_type(entry_value['match'])
        entry = entry_value['entry']
        html_entry, text_entry = construct_entry_text(entry,matchType,words=words,authors=authors)
        html += html_entry
        result += text_entry

    html += """</body>
    </html>"""

    return html, result