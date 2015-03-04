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
    
    def updateAll(self):
        self.updateFaceItInfo()
        self.updateCEVOInfo()
        self.updateESEAInfo()
        self.updateStarLadderInfo()
        self.updateGameShowInfo()

    def updateFaceItInfo(self):
        f = open('', 'r')

        month = 'unknown'
        date = 'unknown'
        for line in f:
            if line == '\n':
                continue
            m = re.match(r'^(\w+) (\d+)', line)
            if m:
                month = m.group(1)
                date = m.group(2)
                if len(date) == 1:
                    date = '0' + date
                continue
            details = re.split('-', line)
            m = re.match(r'^(\d\d)', details[0])
            time = m.group(1)
            match_name = details[-2]
            match_map = details[-1]
           
            event = {
                    'summary' : match_name,
                    'description' : match_map + ' FACEIT League 2015',
                    'start' : {
                        'dateTime' : '2015-'+self.date_convers[month]+'-'+date+'T'+time+':00:00.000+01:00'
                    },
                    'end' : {
                        'dateTime' : '2015-'+self.date_convers[month]+'-'+date+'T'+str(int(time)+1)+':00:00.000+01:00'
                    }
            }

            self.addEvent(event)


    def updateCEVOInfo(self):
        soup = bs(urlopen('file:///home/jelliott/csgo_cal_updater/cevo.html'))
        for wrapper in soup.find_all(class_='schedule-timeline-wrapper'):
            wrapper_name = wrapper.find(class_=re.compile(r'^schedule-timeline-name')).text.strip()
            if wrapper_name == 'Preseason' or wrapper_name == 'Regular Season':
                # we don't care about these (for now)
                continue

            # assume pro div will always be first, so use find (instead of find_all)
            pro_div_info = wrapper.find(class_='division-information clearfix row-wrapper row_2col')
            games_info = pro_div_info.find_all(class_='round-match row')
            for game in games_info:
                # teams playing
                team_info = game.find_all(class_='round-match-team')
                datetime_info = game.find(class_='round-match-date')
                teamA = team_info[0].text.strip()
                teamB = team_info[1].text.strip()
                summary = teamA + ' vs ' +teamB

                # date and time
                m = re.match(r'^\w\w\w, (\w\w\w) (\d\d)\w\w (\d?\d:\d\d)(\w)\w', datetime_info.text.strip())
                month = self.date_convers[m.group(1)]
                day = m.group(2)
                if len(day) == 1:
                    day = '0' + day
                time = m.group(3)
                noon = m.group(4)
                # if hour is a single digit
                if len(time) == 4:
                    time = '0' + time
                if noon == 'P':
                    time = str(int(time[:2]) + 12) + time[2:]
                start_time = '2015-'+month+'-'+day+'T'+time+':00.000-06:00'
                end_time = '2015-'+month+'-'+day+'T'+str(int(time[:2])+1)+time[2:]+':00.000-06:00'

                # maps and league
                desc = game.find(class_='round-match-maps').text.replace('\t', '')
                desc = 'CEVO ' + wrapper_name + ': ' + desc.replace(',', ', ')

                event = {
                    'summary' : summary,
                    'description' : desc,
                    'start' : {
                        'dateTime' : start_time
                    },
                    'end' : {
                        'dateTime' : end_time
                    }
                }
                self.addEvent(event)

    def updateESEAInfo(self):
        time = 'unknown'
        for i in xrange(7):
            the_date = date.today()+timedelta(days=i)
            url = 'http://play.esea.net/index.php?s=league&date='+str(the_date)+'&region_id=all&division_level=invite'
            request = Request(url, headers={'Cookie' : 'settings_time_zone=Australia/Sydney'})
            soup = bs(urlopen(request))
            for match in soup.find_all(class_='match-container'):
                m = re.search(r'Completed|Live|Schedule Pending', match.find('img').string)
                if not m:
                    m = re.search('(\d?\d:\d\d)(\w)m$', match.find('img').string)
                    if m.group(2) == 'a':
                        time = '0'+m.group(1)
                    else:
                        # potential bug here dealing with if a match is at midnight
                        # ceebs dealing with unless it's a problem later
                        time = str(int(m.group(1)[0])+12)+m.group(1)[1:]

                    anchor_tags = match.find_all('a')
                    summary = anchor_tags[1].string + ' vs ' + anchor_tags[3].string
                    desc = 'ESEA ' + match.find(class_='match-footer').string
                    start_time = str(the_date) + 'T' + time + ':00.000+11:00'
                    end_time = str(the_date) + 'T' + time[0] + str(int(time[1]) + 1) + time[2:] + ':00.000+11:00'
                    event = {
                        'summary' : summary,
                        'description' : desc,
                        'start' : {
                            'dateTime' : start_time
                        },
                        'end' : {
                            'dateTime' : end_time
                        }
                    }
                    self.addEvent(event)


    def updateStarLadderInfo(self):
        pass

    def updateGameShowInfo(self):
        pass

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
            m = re.search(r'CEVO|ESEA|FACEIT|StarLadder|GameShow|iBUYPOWER', event['description'])
            n = re.search(r'CEVO|ESEA|FACEIT|StarLadder|GameShow|iBUYPOWER', existing_event['description'])
            
            if m.group(0) == n.group(0) and existing_event['summary'] == event['summary']:
                event_exists = True
                # if the time is different, or the description is different, update it
                if not self.sameEventTime(event, existing_event) or existing_event['description'] !=  event['description']:
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
