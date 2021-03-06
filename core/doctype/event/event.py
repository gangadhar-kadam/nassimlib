# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import webnotes
import httplib2
import json
# import httplib2
from gdata.gauth import OAuth2Token
import urllib
import urlparse

from webnotes.model.bean import getlist
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.tools import run
import oauth2client.client
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import atom.http_core

from webnotes.utils import getdate, cint, add_months, date_diff, add_days, nowdate
from webnotes.model.doc import Document


weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl
		
	def validate(self):
		if self.doc.starts_on and self.doc.ends_on and self.doc.starts_on > self.doc.ends_on:
			webnotes.msgprint(webnotes._("Event End must be after Start"), raise_exception=True)

	def on_update(self):
		# webnotes.errprint("In on Update")
		name=webnotes.session.user
		credentials_json= webnotes.conn.sql(""" select credentials from tabProfile 
			where name ='%s'"""%(webnotes.session.user), as_list=1)
		webnotes.errprint("credentials_json")
		webnotes.errprint(credentials_json)
		if len(credentials_json) == 0:
			webnotes.msgprint("Create Credentials for current user")
		if self.doc.event_id:
			self.update_event(credentials_json[0][0])
		else:
			dic=self.create_dict()
			event=self.create_event(dic)
			service=create_service(credentials_json[0][0])
			# if service:
			recurring_event= self.create_recurringevent(event,service)
			if recurring_event:
				self.doc.event_id=recurring_event['id']
			self.doc.save()

	def create_dict(self):
		webnotes.errprint("in dict")
		name=webnotes.session.user
		webnotes.errprint(name)
		list1=[]
		for p in getlist(self.doclist,'event_individuals'):
			list1.append(p.person)
		   	
		dic = {'summary': self.doc.subject,'location': 'pune','start': self.doc.starts_on,'end': self.doc.ends_on,'attendees': list1 }
		return dic

	def create_recurringevent(self,event,service):
		recurring_event=''
		# webnotes.errprint(type(service))
		# webnotes.errprint("in recurring event")
		if service:
			recurring_event = service.events().insert(calendarId='primary', body=event).execute()
		return recurring_event

	def create_event(self,dic):
		webnotes.errprint("in create event")
		
		event = { 
				'summary': dic['summary'],
				'location': dic['location'],
				'start': {
					'dateTime': dic['start'].replace(' ','T')+'.00+05:30'
				},
				'end': {
					'dateTime': dic['end'].replace(' ','T')+'.00+05:30'
				},
				'attendees': [
					{
						'email': dic['attendees']
					}	
				]
			}
				
		
		return event
	def update_event(self, credentials_json):
		webnotes.errprint("in update")
		#self.create_dict()
		dic=self.create_dict()
		
		#self.create_service()
		service=create_service(credentials_json)
		event = service.events().get(calendarId='primary', eventId=self.doc.event_id).execute()
		webnotes.errprint(event)
		#self.create_event(dic)
		event=self.create_event(dic)
		webnotes.errprint(event)
		updated_event = service.events().update(calendarId='primary', eventId=self.doc.event_id, body=event).execute()

		#return updated_event	

			
def get_match_conditions():
	return """(tabEvent.event_type='Public' or tabEvent.owner='%(user)s'
		or exists(select * from `tabEvent User` where 
			`tabEvent User`.parent=tabEvent.name and `tabEvent User`.person='%(user)s')
		or exists(select * from `tabEvent Role` where 
			`tabEvent Role`.parent=tabEvent.name 
			and `tabEvent Role`.role in ('%(roles)s')))
		""" % {
			"user": webnotes.session.user,
			"roles": "', '".join(webnotes.get_roles(webnotes.session.user))
		}
			
def send_event_digest():
	today = nowdate()
	for user in webnotes.conn.sql("""select name, email, language 
		from tabProfile where ifnull(enabled,0)=1 
		and user_type='System User' and name not in ('Guest', 'Administrator')""", as_dict=1):
		events = get_events(today, today, user.name, for_reminder=True)
		if events:
			text = ""
			webnotes.set_user_lang(user.name, user.language)
			webnotes.load_translations("core", "doctype", "event")

			text = "<h3>" + webnotes._("Events In Today's Calendar") + "</h3>"
			for e in events:
				if e.all_day:
					e.starts_on = "All Day"
				text += "<h4>%(starts_on)s: %(subject)s</h4><p>%(description)s</p>" % e

			text += '<p style="color: #888; font-size: 80%; margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee;">'\
				+ webnotes._("Daily Event Digest is sent for Calendar Events where reminders are set.")+'</p>'

			from webnotes.utils.email_lib import sendmail
			sendmail(recipients=user.email, subject=webnotes._("Upcoming Events for Today"),
				msg = text)
				
@webnotes.whitelist()
def get_events(start, end, user=None, for_reminder=False):
	if not user:
		user = webnotes.session.user
	roles = webnotes.get_roles(user)
	events = webnotes.conn.sql("""select name, subject, description,
		starts_on, ends_on, owner, all_day, event_type, repeat_this_event, repeat_on,
		monday, tuesday, wednesday, thursday, friday, saturday, sunday
		from tabEvent where ((
			(date(starts_on) between date('%(start)s') and date('%(end)s'))
			or (date(ends_on) between date('%(start)s') and date('%(end)s'))
			or (date(starts_on) <= date('%(start)s') and date(ends_on) >= date('%(end)s'))
		) or (
			date(starts_on) <= date('%(start)s') and ifnull(repeat_this_event,0)=1 and
			ifnull(repeat_till, "3000-01-01") > date('%(start)s')
		))
		%(reminder_condition)s
		and (event_type='Public' or owner='%(user)s'
		or exists(select * from `tabEvent User` where 
			`tabEvent User`.parent=tabEvent.name and person='%(user)s')
		or exists(select * from `tabEvent Role` where 
			`tabEvent Role`.parent=tabEvent.name 
			and `tabEvent Role`.role in ('%(roles)s')))
		order by starts_on""" % {
			"start": start,
			"end": end,
			"reminder_condition": "and ifnull(send_reminder,0)=1" if for_reminder else "",
			"user": user,
			"roles": "', '".join(roles)
		}, as_dict=1)
			
	# process recurring events
	start = start.split(" ")[0]
	end = end.split(" ")[0]
	add_events = []
	remove_events = []
	
	def add_event(e, date):
		new_event = e.copy()
		new_event.starts_on = date + " " + e.starts_on.split(" ")[1]
		if e.ends_on:
			new_event.ends_on = date + " " + e.ends_on.split(" ")[1]
		add_events.append(new_event)
	
	for e in events:
		if e.repeat_this_event:
			event_start, time_str = e.starts_on.split(" ")
			if e.repeat_on=="Every Year":
				start_year = cint(start.split("-")[0])
				end_year = cint(end.split("-")[0])
				event_start = "-".join(event_start.split("-")[1:])
				
				# repeat for all years in period
				for year in range(start_year, end_year+1):
					date = str(year) + "-" + event_start
					if date >= start and date <= end:
						add_event(e, date)
						
				remove_events.append(e)

			if e.repeat_on=="Every Month":
				date = start.split("-")[0] + "-" + start.split("-")[1] + "-" + event_start.split("-")[2]
				
				# last day of month issue, start from prev month!
				try:
					getdate(date)
				except ValueError:
					date = date.split("-")
					date = date[0] + "-" + str(cint(date[1]) - 1) + "-" + date[2]
					
				start_from = date
				for i in xrange(int(date_diff(end, start) / 30) + 3):
					if date >= start and date <= end and date >= event_start:
						add_event(e, date)
					date = add_months(start_from, i+1)

				remove_events.append(e)

			if e.repeat_on=="Every Week":
				weekday = getdate(event_start).weekday()
				# monday is 0
				start_weekday = getdate(start).weekday()
				
				# start from nearest weeday after last monday
				date = add_days(start, weekday - start_weekday)
				
				for cnt in xrange(int(date_diff(end, start) / 7) + 3):
					if date >= start and date <= end and date >= event_start:
						add_event(e, date)

					date = add_days(date, 7)
				
				remove_events.append(e)

			if e.repeat_on=="Every Day":				
				for cnt in xrange(date_diff(end, start) + 1):
					date = add_days(start, cnt)
					if date >= event_start and date <= end \
						and e[weekdays[getdate(date).weekday()]]:
						add_event(e, date)
				remove_events.append(e)

	for e in remove_events:
		events.remove(e)
		
	events = events + add_events
	
	for e in events:
		# remove weekday properties (to reduce message size)
		for w in weekdays:
			del e[w]
			
	return events


def create_service(credentials_json):
	webnotes.errprint("in the create_service")
	app_key=webnotes.conn.sql("select value from `tabSingles` where doctype='OAuth Settings' and field in ('app_key');",as_list=1)
	# print token_details
	webnotes.errprint(app_key[0][0])
	if app_key:
		developerKey=app_key[0][0]


	if credentials_json:
		credentials = oauth2client.client.Credentials.new_from_json(credentials_json)
		# developerKey = webnotes.conn.sql("select app_key from tabProfile where name = '%s'"%(webnotes.session.user), as_list=1)
		if developerKey:
			#json_object = json.load(response)
			#json_object = json.loads(response.read())
			#webnotes.errprint(json_object)
			http = ''
			http = httplib2.Http()
			http = credentials.authorize(http)
			service = build(serviceName='calendar', version='v3', http=http, 
				developerKey=developerKey[0][0])	
			return service	



@webnotes.whitelist()
def sync_google_event(_type='Post'):
	webnotes.errprint("in the sync_google_event")
	page_token = None
	credentials_json= webnotes.conn.sql(""" select credentials  from tabProfile 
            where name ='%s'"""%(webnotes.session.user), as_list=1)
	service = create_service(credentials_json[0][0])
	webnotes.errprint("service")
	webnotes.errprint(service)
	# ser=json.loads(service)
	# webnotes.errprint(ser)

	while True:
		events = service.events().list(calendarId='primary', pageToken=page_token).execute()
		webnotes.errprint("events")
		webnotes.errprint(events)
		for event in events['items']:
			eventlist=webnotes.conn.sql("select event_id from `tabEvent`", as_list=1)
	        s= webnotes.conn.sql("select modified from `tabEvent` where event_id= %s ",(event['id']) , as_list=1)
	        a=[]
	        a.append(event['id'])
	        m=[]
	        m.append(event['updated'])
	        if a not in eventlist:
	                webnotes.errprint("created event")
	                d = Document("Event")
	                d.event_id=event['id']
	                d.subject=event['summary']
	                d.starts_on=event['start']['dateTime']
	                d.ends_on=event['end']['dateTime']
	                d.save()
	                webnotes.errprint(d.name)
	        elif m > s:
	                r=webnotes.conn.sql("update `tabEvent` set starts_on=%s, ends_on=%s,subject=%s where event_id=%s",(event['start']['dateTime'],event['end']['dateTime'],event['summary'],event['id']))
	                webnotes.errprint(event['id'])
	        else:
	        	pass
		page_token = events.get('nextPageToken')
		if not page_token:
			break

def refresh_token():
	print "in the refresh_token"
	print webnotes.session.user
	# webnotes.errprint("in the refresh_token")
	credentials_json= webnotes.conn.sql(""" select credentials from tabProfile 
	where name ='%s'"""%('pranali.k@indictranstech.com'), as_list=1)
	# print credentials_json
	# @decorator.oauth_required
	auth_token1 = OAuth2TokenFromCredentials(credentials_json[0][0])
	print auth_token1.access_token
	# auth_token=json.dumps(serialize(auth_token1))
	# print type(auth_token)


	# print auth_token["access_token"]

	# UpdateFromCredentials()

	# webnotes.errprint(json.loads(auth_token))



class OAuth2TokenFromCredentials(OAuth2Token):
	def __init__(self, credentials):
		print "in the classs"
		# print type(credentials)
		http = httplib2.Http()
		self.credentials =json.loads(credentials)
		print self.credentials
		super(OAuth2TokenFromCredentials, self).__init__(None, None, None, None)
		self.UpdateFromCredentials()

		# self._refresh(httplib2.Http().request)


	def UpdateFromCredentials(self):
		print "in the update"
		print self.credentials["client_id"]
		self.client_id =  self.credentials["client_id"]
		print self.client_id
		self.client_secret =  self.credentials["client_secret"]
		self.user_agent =  self.credentials["user_agent"]
		self.token_uri = self.credentials["token_uri"]
		self.access_token = self.credentials["access_token"]
		self.refresh_token = self.credentials["refresh_token"]
		self.token_expiry = self.credentials["token_expiry"]
		self._invalid = self.credentials["invalid"]
		print self.user_agent 
		print 'finish'
		self._refresh(httplib2.Http().request)



	# def generate_authorize_url(self, *args, **kwargs): raise NotImplementedError
	# def get_access_token(self, *args, **kwargs): raise NotImplementedError
	# def revoke(self, *args, **kwargs): raise NotImplementedError
	# def _extract_tokens(self, *args, **kwargs): raise NotImplementedError

	def _refresh(self,unused_request):
		print "in the _refresh"
		# pyresponse = json.load(fetchsamples()) 
		# print "hi"
		self._refresh(httplib2.Http().request)
		print "self.credentials"
		self.UpdateFromCredentials()


	# def _refresh(self, request):
	# 	# headers={}
	# 	print "in the refresh"
	# 	# token_uri=self.credentials["token_uri"]
	# 	print self.token_uri
	# 	print self.user_agent
	# 	body = urllib.urlencode({
 #       'grant_type': 'refresh_token',
 #       'client_id': self.client_id,
 #       'client_secret': self.client_secret,
 #       'refresh_token' : self.refresh_token  
 #            })
	# 	print 'body'

	# 	print body

	# 	# headers={
	# 	# 'user-agent': self.user_agent,
 #  #       }
  
 #        # print headers['user-agent']
 #        http_request = atom.http_core.HttpRequest(uri='https://accounts.google.com/o/oauth2/token', method='POST', headers='Gcal')
 #     	http_request.add_body_part(body, mime_type='application/x-www-form-urlencoded')
 #  #    	response = request(http_request)
 #  #    	body = response.read()
 #  #    	if response.status == 200:
  #    		self._extract_tokens(body)
  #    	else:
  #    		self._invalid = True
  #    	print response
     	# return response

	# def _extract_tokens(self, body):
	# 	print "in the ext"
	# 	d = simplejson.loads(body)
	# 	self.access_token = d['access_token']
	# 	self.refresh_token = d.get('refresh_token', self.refresh_token)
	# 	if 'expires_in' in d:
	# 		self.token_expiry = datetime.timedelta(
	# 			seconds = int(d['expires_in'])) + datetime.datetime.now()
	# 	else:
	# 		self.token_expiry = None


