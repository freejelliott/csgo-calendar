import gflags
import re
import httplib2
import feed.date.rfc3339

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from bs4 import BeautifulSoup as bs
from urllib2 import urlopen
from datetime import date, timedelta

from oauth2client.client import SignedJwtAssertionCredentials


class CSGOCalendar:
    'Provides access to a Google Calendar through the Google Calendar API'
    def __init__(self, faceit_path):
        client_email = '459471911785-ruid59gu06t6jr7djbo6t4882qrr0u19@developer.gserviceaccount.com'
        with open('My Project-e6813da287b5.p12') as f:
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

        self.faceit_path = faceit_path
    
    def updateAll(self):
        #self.updateFaceItInfo()
        self.updateCEVOInfo()
        self.updateESEAInfo()
        self.updateStarLadderInfo()
        self.updateGameShowInfo()

    def updateFaceItInfo(self):
        f = open(self.faceit_path, 'r')

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
            soup = bs(urlopen(url))
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
        # Check if the event already exists
        # We make an assumption that if a match has happened to have a changed time,
        # it will have been changed within the day it was on
        # and also that a single league won't have multiple matches with same team in a day
        timeMin = event['start']['dateTime'][:11] + '00:00:00.000' + event['start']['dateTime'][-6:] 
        timeMax = event['end']['dateTime'][:11] + '23:59:00.000' + event['end']['dateTime'][-6:]
        existing_events = self.service.events().list(calendarId=self.calendarId, timeMin=timeMin,
                                                                            timeMax=timeMax).execute()
        eventExists = False
        for existing_event in existing_events['items']:
            m = re.search(r'CEVO|ESEA|FACEIT|StarLadder|GameShow', event['description'])
            n = re.search(r'CEVO|ESEA|FACEIT|StarLadder|GameShow', existing_event['description'])

            if m.group(0) == n.group(0) and existing_event['summary'] == event['summary']:
                if (feed.date.rfc3339.tf_from_timestamp(event['start']['dateTime']) == \
                    feed.date.rfc3339.tf_from_timestamp(existing_event['start']['dateTime']) and \
                    feed.date.rfc3339.tf_from_timestamp(event['end']['dateTime']) == \
                    feed.date.rfc3339.tf_from_timestamp(existing_event['end']['dateTime'])):
                    eventExists = True
                elif event['description'] != existing_event['description']:
                    # We delete the event if the time or description has been changed. It'll just get added again below
                    print 'Deleted Event'
                    print existing_event
                    self.service.events().delete(calendarId=self.calendarId, eventId=existing_event['id']).execute()
                break
        if not eventExists:
            self.service.events().insert(calendarId=self.calendarId, body=event).execute()
            print 'Added Event'
            print event
                
    
    
            
            


    
def main():
    calendar = CSGOCalendar('/home/jelliott/csgo_cal_updater/faceitinfo')
    calendar.updateAll()

if __name__ == "__main__":
    main()
