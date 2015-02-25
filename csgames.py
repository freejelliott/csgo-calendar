import gflags
import re
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from bs4 import BeautifulSoup as bs
from urllib2 import urlopen
from datetime import date, timedelta


calendarId = 'uhde8ddsban9np68ormfio1lhk@group.calendar.google.com'
date_convers = {
    'February' : '02',
    'March' : '03',
    'April' : '04'
}

def initialiseCalendar():
    FLAGS = gflags.FLAGS

    # Set up a Flow object to be used if we need to authenticate. This
    # sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
    # the information it needs to authenticate. Note that it is called
    # the Web Server Flow, but it can also handle the flow for native
    # applications
    # The client_id and client_secret can be found in Google Developers Console
    FLOW = OAuth2WebServerFlow(
        client_id='459471911785-ocjil131jv3f48auh1uvkh1khumr7blt.apps.googleusercontent.com',
        client_secret='VAomZjfI0NKFJR7j0tpL8oX4',
        scope='https://www.googleapis.com/auth/calendar',
        user_agent='YOUR_APPLICATION_NAME/YOUR_APPLICATION_VERSION')

    # To disable the local server feature, uncomment the following line:
    # FLAGS.auth_local_webserver = False

    # If the Credentials don't exist or are invalid, run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('calendar.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Build a service object for interacting with the API. Visit
    # the Google Developers Console
    # to get a developerKey for your own application.
    return build(serviceName='calendar', version='v3', http=http,
           developerKey='AIzaSyAICooyJLruGo-JTS_lN92hGDUztc7z5IU')

def addFaceItInfo(service):
    f = open('faceitinfo', 'r')

    month = 'unknown'
    date = 'unknown'
    for line in f:
        if line == '\n':
            continue
        m = re.match(r'^(\w+) (\d+)', line)
        if m:
            month = m.group(1)
            print month
            date = m.group(2)
            print date
            continue
        details = re.split('-', line)
        m = re.match(r'^(\d\d)', details[0])
        time = m.group(1)
        match_name = details[-2]
        match_map = details[-1]
       
        event = {
                'summary' : match_name,
                'description' : match_map + '. FACEIT League 2015',
                'start' : {
                    'dateTime' : '2015-'+date_convers[month]+'-'+date+'T'+time+':00:00.000+01:00'
                },
                'end' : {
                    'dateTime' : '2015-'+date_convers[month]+'-'+date+'T'+str(int(time)+1)+':00:00.000+01:00'
                }
        }

        created_event = service.events().insert(calendarId=calendarId, body=event).execute()

def updateCEVOInfo(service):
    return None

def updateESEAInfo(service):
    time = 'unknown'
    for i in xrange(7):
        the_date = date.today()+timedelta(days=i)
        url = 'http://play.esea.net/index.php?s=league&date='+str(the_date)+'&region_id=all&division_level=invite'
        soup = bs(urlopen(url))
        for match in soup.find_all(class_='match-container'):
            m = re.search(r'Completed|Live|Schedule Pending', match.find('img').string)
            if not m:
                m = re.search('(\d:\d\d)(\w)m$', match.find('img').string)
                if m.group(2) == 'a':
                    time = '0'+m.group(1)
                else:
                    # potential bug here dealing with if a match is at midnight
                    # ceebs dealing with unless it's a problem later
                    time = str(int(m.group(1)[0])+12)+m.group(1)[1:]

                anchor_tags = match.find_all('a')
                match_name = anchor_tags[1].string + ' vs ' + anchor_tags[3].string
                match_desc = 'ESEA ' + match.find(class_='match-footer').string
                start_time = str(the_date) + 'T' + time + ':00.000+11:00'
                end_time = str(the_date) + 'T' + time[0] + str(int(time[1]) + 1) + time[2:] + ':00.000+11:00'
                existing_events = service.events().list(calendarId=calendarId, timeMin=start_time, timeMax = end_time).execute()
                # check if the event already exists
                eventExists = False
                for event in existing_events['items']:
                    if event['summary'] == match_name:
                        eventExists = True
                        break
                if eventExists == False:
                    event = {
                        'summary' : match_name,
                        'description' : match_desc,
                        'start' : {
                            'dateTime' : start_time
                        },
                        'end' : {
                            'dateTime' : end_time
                        }
                    }
                    created_event = service.events().insert(calendarId=calendarId, body=event).execute()

            





def updateStarLadderInfo(service):
    return None

def updateGameShowInfo(service):
    return None




def main():
    service = initialiseCalendar()
    #addFaceItInfo(service)
    #updateCEVOInfo(service)
    updateESEAInfo(service)
    #updateStarLadderInfo(service)


if __name__ == "__main__":
    main()
#faceit_link = 'http://www.gosugamers.net/counterstrike/news/29966-faceit-releases-full-schedule-for-all-divisions-in-2015'
#soup = bs(urlopen(faceit_link))
