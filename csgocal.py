import os
import re
import httplib2
import feed.date.rfc3339

from apiclient.discovery import build
from bs4 import BeautifulSoup as bs
from urllib2 import urlopen, Request
from datetime import date, timedelta, datetime
from oauth2client.client import SignedJwtAssertionCredentials

dir = os.path.dirname(__file__)

class CSGOCalendar:
    'Provides access to a Google Calendar through the Google Calendar API'
    def __init__(self):
        client_email = '459471911785-ruid59gu06t6jr7djbo6t4882qrr0u19@developer.gserviceaccount.com'
        filename = os.path.join(dir, 'My Project-e6813da287b5.p12')
        with open(filename) as f:
            private_key = f.read()

        credentials = SignedJwtAssertionCredentials(client_email, private_key, 
                'https://www.googleapis.com/auth/calendar', sub='joshualjelliott@gmail.com')

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service = build(serviceName='calendar', version='v3', http=http,
               developerKey='AIzaSyAICooyJLruGo-JTS_lN92hGDUztc7z5IU')

        self.calendarId = 'k3nafbeprkllv2q45bvpvhodig@group.calendar.google.com'

        self.date_convers = {
            'January' : '01',
            'Jan' : '01',
            'February' : '02',
            'Feb' : '02',
            'March' : '03',
            'Mar' : '03',
            'April' : '04',
            'Apr' : '04',
            'May' : '05',
            'June' : '06',
            'Jun' : '06',
            'July' : '07',
            'Jul' : '07',
            'August' : '08',
            'Aug' : '08',
            'September' : '09',
            'Sep' : '09',
            'October' : '10',
            'Oct' : '10',
            'November' : '11',
            'Nov' : '11',
            'December' : '12',
            'Dec' : '12'
        }
    
    def update(self):
        url = 'http://www.gosugamers.net/counterstrike/gosubet?u-page=1'
        request = Request(url, headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'})
        soup = bs(urlopen(request))
        # absolutely unreadable shit. sorry kinda not sorry
        num_pages = int(soup.find_all(class_='box')[1].find_all('a')[-1]['href'][-1])
        for soup_url in ['http://www.gosugamers.net/counterstrike/gosubet?u-page=' + str(i) for i in xrange(1, num_pages + 1)]:
            request = Request(soup_url, headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'})
            soup = bs(urlopen(request))
            upcoming_matches = soup.find_all(class_='box')[1]
            match_urls = ['http://www.gosugamers.net' + match['href'] for match in upcoming_matches('a', 'match')]
            for match_url in match_urls:
                request = Request(match_url, headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'})
                match_soup = bs(urlopen(request))
                summary_and_league = match_soup.find('h1')
                summary = summary_and_league.find('label').text.strip()
                league = summary_and_league.find('a').text.strip()
                best_of_format = match_soup.find(class_='bestof').text.strip()
                hours = re.search('\d', best_of_format).group(0)
                datetime = match_soup.find(class_='datetime').text.strip()
                m = re.match('(?P<month>\w+) (?P<day>\d+), \w+, (?P<start_hour>\d\d):(?P<start_min>\d\d)', datetime)
                month = self.date_convers[m.groupdict()['month']]
                day = m.groupdict()['day']
                time = m.groupdict()['start_hour'] + ':' + m.groupdict()['start_min']
                event = {
                    'summary' : summary,
                    'description' : league + ' | ' + best_of_format,
                    'start' : {
                        'dateTime' : '2015-' + month + '-' + day + 'T' + time + ':00.000+01:00'
                    },
                    'end' : {
                        'dateTime' : '2015-' + month + '-' + day + 'T' + str(int(time[:2])++int(hours)) + time[2:] + ':00.000+01:00'
                    },
                    'source' : {
                        'url' : match_url
                    }
                }
                self.addEvent(event)

    def addEvent(self, event):
        # Check if the event exists within a day by finding the match with the same league and summary.
        # If it exists, update it with new info, otherwise add it

        filterTimeMin = event['start']['dateTime'][:11] + '00:00:00.000' + event['start']['dateTime'][-6:] 
        filterTimeMax = event['end']['dateTime'][:11] + '23:59:00.000' + event['end']['dateTime'][-6:]
        existing_events = self.service.events().list(calendarId=self.calendarId, timeMin=filterTimeMin,
                                                                            timeMax=filterTimeMax).execute()
        event_exists = False
        filename = os.path.join(dir, 'match_log')
        f = open(filename, 'a')
        for existing_event in existing_events['items']:
            if existing_event['source']['url'] == event['source']['url']:
                event_exists = True
                # if the time is different, update it
                if not self.sameEventTime(event, existing_event):
                    updated_event = self.service.events().update(calendarId=self.calendarId, eventId=existing_event['id'], body=event).execute()
                    f.write('*** Updated Event *** ' + str(datetime.now()) + '\n')
                    f.write('Old\n')
                    f.write(existing_event['summary'] + ' | ' + existing_event['start']['dateTime'] + ' -- ' + existing_event['end']['dateTime'] + ' | ' + existing_event['description'] + '\n')
                    f.write('New\n')
                    f.write(updated_event['summary'] + ' | ' + updated_event['start']['dateTime'] + ' -- ' + updated_event['end']['dateTime'] + ' | ' + updated_event['description'] + '\n')
                    f.write('\n')
                break
        
        if not event_exists:
            added_event = self.service.events().insert(calendarId=self.calendarId, body=event).execute()
            f.write('*** Added Event *** ' +  str(datetime.now()) + '\n')
            f.write(added_event['summary'] + ' | ' + added_event['start']['dateTime'] + ' -- ' + added_event['end']['dateTime'] + ' | ' + added_event['description'] + '\n')
            f.write('\n')
        f.close()

    def sameEventTime(self, eventA, eventB):
        return feed.date.rfc3339.tf_from_timestamp(eventA['start']['dateTime']) == feed.date.rfc3339.tf_from_timestamp(eventB['start']['dateTime']) and \
                feed.date.rfc3339.tf_from_timestamp(eventA['end']['dateTime']) == feed.date.rfc3339.tf_from_timestamp(eventB['end']['dateTime'])
