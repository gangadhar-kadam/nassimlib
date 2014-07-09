# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
import urllib
import json
# import gdata
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.tools import run
import oauth2client.client
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import logging
from webnotes.model.doc import Document
from webnotes.utils import flt, cstr
import gdata
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data
from gdata.auth import OAuthSignatureMethod, OAuthToken, OAuthInputParams
import pickle

import gdata.gauth
import gdata.contacts.client

rqst_token = ''


# The URL root for accessing Google Accounts.
# GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'


# Hardcoded dummy redirect URI for non-web apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

@webnotes.whitelist()
def genearate_calendar_cred(client_id, client_secret, app_name):
	webnotes.errprint("in the genearate_calendar_cred")

	flow = get_gcalendar_flow(client_id, client_secret, app_name)
	authorize_url = flow.step1_get_authorize_url()
	# return authorize_url
	return {
		"authorize_url": authorize_url,
	}	

def get_gcalendar_flow(client_id, client_secret, app_name):
	webnotes.errprint("in the get_gcalendar_flow")
	from oauth2client.client import OAuth2WebServerFlow
	if client_secret and client_id and app_name:
		flow = OAuth2WebServerFlow(client_id=client_id, 
			client_secret=client_secret,
			scope='https://www.googleapis.com/auth/calendar',
			redirect_uri='urn:ietf:wg:oauth:2.0:oob',
			user_agent=app_name)
	webnotes.errprint("flow")	
	webnotes.errprint(flow)
	# 'https://www.googleapis.com/auth/calendar',
	return flow

@webnotes.whitelist()
def generate_credentials(client_id, client_secret,authorization_code,app_name,user_name):
	webnotes.errprint("in the generate_credentials")
	flow = get_gcalendar_flow(client_id, client_secret, app_name)
	if authorization_code:
		credentials = flow.step2_exchange(authorization_code)
	final_credentials = credentials.to_json()
	# final_token=json.loads(final_credentials)
	set_values_calender(final_credentials,user_name)
	# webnotes.errprint(type(final_credentials))
	# webnotes.errprint(final_credentials)
	# return{
	# 	'final_credentials': final_credentials
	# }

def set_values_calender(final_credentials,user_name):
	webnotes.errprint("in the cal set_values")	
	# return json.loads(response)
	cr = Document('Profile',user_name)
	cr.credentials = final_credentials
	cr.save()
	webnotes.errprint(cr)
	import pickle
	# dictobj = {'Jack' : 123, 'John' : 456}

	# filename = "client"

	fileobj = open('client.pickle', 'wb')

	pickle.dump(final_credentials, fileobj)

	fileobj.close()
	webnotes.errprint(type(fileobj))

	webnotes.errprint("finish writing")



@webnotes.whitelist()
def get_google_authorize_url(client_id=None, client_secret=None, scope=None, user_agent=None, application_redirect_uri=None):
	# webnotes.errprint("int the contact")
	request_token = generate_request_tocken(client_id, client_secret)
	auth_url = request_token.generate_authorization_url()
	# webnotes.errprint(auth_url)
	return str(auth_url)

def generate_request_tocken(client_id=None, client_secret=None, scope=None, user_agent=None, application_redirect_uri=None):
	webnotes.errprint("in the request_token")
	scope='https://www.google.com/m8/feeds'
	application_redirect_uri='http://localhost:1000/'
	user_agent='PGCAL'
	if(client_id and client_secret and scope and user_agent and application_redirect_uri):
		# """Get request token."""
		client = gdata.contacts.client.ContactsClient(source=user_agent)
		request_token = client.get_oauth_token(client.auth_scopes, application_redirect_uri, client_id, str(client_secret))
		with open('data.pickle', 'w') as pickle_file:
			pickle.dump(request_token, pickle_file)
		webnotes.errprint(request_token)	
	return request_token
	
	# else:
	# 	webnotes.msgprint(" Please specify values for CLIENT ID, CLIENT_SECRET, SCOPE, USER_AGENT and APPLICATION_REDIRECT_URI ",raise_exception=1)

@webnotes.whitelist()
def g_callback(verification_code=None, user_agent=None):
	user_agent='PGCAL'
	webnotes.errprint("in the g_callback")
	# webnotes.errprint("in the g_callback")
	with open('data.pickle') as pickle_file:
		rqst_token = pickle.load(pickle_file)
		webnotes.errprint(rqst_token)

	if verification_code and user_agent:
		client = gdata.contacts.client.ContactsClient(source=user_agent)
		gdata.gauth.authorize_request_token(rqst_token, verification_code)
		"""Get all contacts."""
		client.auth_token = client.get_access_token(rqst_token)
	
		with open('client.pickle', 'w') as pickle_file:
			pickle.dump(client, pickle_file)
		webnotes.msgprint("Updated")

@webnotes.whitelist()
def read_contact():
	webnotes.errprint("in the read_contact")
	with open('client.pickle') as pickle_file:
		client = pickle.load(pickle_file)

	query = gdata.contacts.client.ContactsQuery(max_results=25, showdeleted='True', updated_min=None, updated_max=None)

	# to rerieve contacts from google
	feed = client.get_contacts(query=query)
	for contact in feed.entry:
		try:
			webnotes.errprint(contact.id)
			webnotes.errprint(contact.name)
		except err:
			webnotes.errprint(err.message)
