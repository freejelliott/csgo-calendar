import os
import re
import httplib2
import feed.date.rfc3339

from apiclient.discovery import build
from bs4 import BeautifulSoup as bs
from urllib2 import urlopen, Request
from datetime import date, timedelta, datetime
import datetime as dt
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
        header = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'}
        request = Request(url, headers = header)
        soup = bs(urlopen(request))
        # absolutely unreadable shit. sorry kinda not sorry
        # we have a few pages to work through
        num_pages = int(soup.find_all(class_='box')[1].find_all('a')[-1]['href'][-1])
        for soup_url in ['http://www.gosugamers.net/counterstrike/gosubet?u-page=' + str(i) for i in xrange(1, num_pages + 1)]:
            request = Request(soup_url, headers = header)
            soup = bs(urlopen(request))
            upcoming_matches = soup.find_all(class_='box')[1]
            # list comprehensions make me happy
            match_urls = ['http://www.gosugamers.net' + match['href'] for match in upcoming_matches('a', 'match')]
            # we go through all the upcoming matches that are on the page
            for match_url in match_urls:
                request = Request(match_url, headers = header)
                match_soup = bs(urlopen(request))
                summary_and_league = match_soup.find('h1')
                summary = summary_and_league.find('label').text.strip()
                league_info = summary_and_league.find('a')

                league_url = 'http://www.gosugamers.net' + league_info['href']
                stream_urls = []
                streams =  []
                if re.search('/counterstrike/events', league_url):
                    request = Request(league_url, headers = header)
                    league_soup = bs(urlopen(request))
                    for stream_soup in league_soup.find(id='streams').find_all('h3'):
                        streams.append(stream_soup.text.strip())
                    for stream_soup in league_soup.find_all(class_='stream-box'):
                        m = re.search('twitch|hitbox|mlg', str(stream_soup))
                        if m:
                            if m.group(0) == 'twitch':
                                stream_urls.append(stream_soup.find('object')['data'])
                                stream_urls[-1] = stream_urls[-1].replace('widgets/live_embed_player.swf?channel=', '')
                            elif m.group(0) == 'hitbox':
                                stream_urls.append(stream_soup.find('iframe')['src'])
                                stream_urls[-1] = stream_urls[-1].replace('#!/embed/', '')
                            elif m.group(0) == 'mlg':
                                stream_urls.append(stream_soup.find('iframe')['src'])
                                stream_urls[-1] = stream_urls[-1].replace('player/embed/', '').replace('?autoplay=0', '')
                        else:
                            stream_urls.append('Unknown streaming platform. Sorry, got no url for you.')

                league = league_info.text.strip()
                best_of_format = match_soup.find(class_='bestof').text.strip()
                length = int(re.search('\d', best_of_format).group(0))
                datetime_info = match_soup.find(class_='datetime').text.strip()
                m = re.match('(?P<month>\w+) (?P<day>\d+), \w+, (?P<start_hour>\d\d):(?P<start_min>\d\d)', datetime_info)
                month = int(self.date_convers[m.groupdict()['month']])
                day = int(m.groupdict()['day'])
                start_hour = int(m.groupdict()['start_hour'])
                start_min = int(m.groupdict()['start_min'])
                datetime_info = datetime(2015, month, day, start_hour, start_min)
                stream_info = '-- Streams --\n'
                if len(streams) == 0:
                    stream_info = 'A stream was not found for this match'
                else:
                    for i in xrange(len(streams)):
                        stream_info += '  ' + streams[i] + ': ' + stream_urls[i] + '\n'

                event = {
                    'summary' : summary,
                    'description' : '-- Event --\n  ' + league + ' | ' + best_of_format + '\n\n' + stream_info,
                    'start' : {
                        'dateTime' : str(datetime_info.isoformat('T')) + '+01:00'
                    },
                    'end' : {
                        'dateTime' : str((datetime_info+timedelta(hours=length)).isoformat('T')) + '+01:00'
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
                # if the time is different or description is different, update it
                if not self.sameEventTime(event, existing_event) or event['description'] != existing_event['description']:
                    updated_event = self.service.events().update(calendarId=self.calendarId, eventId=existing_event['id'], body=event).execute()
                    f.write('*** Updated Event *** ' + str(datetime.now()) + '\n')
                    f.write('Old\n')
                    f.write(existing_event['summary'] + ' | ' + existing_event['start']['dateTime'] + ' -- ' + existing_event['end']['dateTime'] + '\n' + existing_event['description'] + '\n')
                    f.write('New\n')
                    f.write(updated_event['summary'] + ' | ' + updated_event['start']['dateTime'] + ' -- ' + updated_event['end']['dateTime'] + '\n' + updated_event['description'] + '\n')
                    f.write('\n')
                break
        
        if not event_exists:
            added_event = self.service.events().insert(calendarId=self.calendarId, body=event).execute()
            f.write('*** Added Event *** ' +  str(datetime.now()) + '\n')
            f.write(added_event['summary'] + ' | ' + added_event['start']['dateTime'] + ' -- ' + added_event['end']['dateTime'] + '\n' + added_event['description'] + '\n')
            f.write('\n')
        f.close()

    def sameEventTime(self, eventA, eventB):
        return feed.date.rfc3339.tf_from_timestamp(eventA['start']['dateTime']) == feed.date.rfc3339.tf_from_timestamp(eventB['start']['dateTime']) and \
                feed.date.rfc3339.tf_from_timestamp(eventA['end']['dateTime']) == feed.date.rfc3339.tf_from_timestamp(eventB['end']['dateTime'])
