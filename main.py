# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# import library os for reading path directory name ..
import os
import datetime

# for routing subdomains
from webapp2_extras import routes

# for logging
import logging


# for working with regular expressions
import re

# to be able to import jinja2 , add to app.yaml
import jinja2
import webapp2

# for storing data in google cloud storage
import logging
import lib.cloudstorage as gcs

from google.appengine.api import app_identity

# for using datastore 
from google.appengine.ext import ndb
from google.appengine.api import images
from base64 import b64encode
from base64 import b64decode

# validate user inputs
# import validate 

# use fundpipe tools
import fptools

# for REST APIs
import urllib
import urllib2
import json

# tell jinja2 where to look for files
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Wldata(ndb.Model):
	"""Models a wielange data objects"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	last_edit = ndb.DateTimeProperty(auto_now_add=True)
	login_fail_last = ndb.DateTimeProperty()
	pygl_uri = ndb.StringProperty()
	password_hash = ndb.StringProperty()
	email = ndb.StringProperty()
	title = ndb.StringProperty()
	text0 = ndb.TextProperty()
	text1 = ndb.TextProperty()
	text2 = ndb.TextProperty()
	comments_active = ndb.BooleanProperty()
	login_fails_consec = ndb.IntegerProperty()		# consecutive login fails
	abuse_report_count = ndb.IntegerProperty()		# count abuse reports
	image_id0 = ndb.StringProperty()
	image_id1 = ndb.StringProperty()
	image_id2 = ndb.StringProperty()
	
class message(ndb.Model):
	"""Models a message object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	sender = ndb.StringProperty()
	recipient = ndb.StringProperty()
	text = ndb.TextProperty()
	encrypted = ndb.BooleanProperty()
	
class Fundpipe(ndb.Model):
	"""Models a Fundpipe object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	owner_address = ndb.StringProperty()
	
class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		output = self.render_str(template, **kw)
		self.write(output)
		
class MainPage(Handler):
	def get(self):
		# show main page
		self.render('main.html')
		
	def post(self):
		# parameters
		pipe_name = self.request.get('pipe_name')
		pipe_owner_address = self.request.get('pipe_owner_address')
		
		# errors
		err_pipe_name_format = False
		err_pipe_name_exists = False
		err_no_valid_btc_address = False
		
		# check for pipe name errors
		pipe_name_val = fptools.validate_name(pipe_name)
		if pipe_name_val:
			pipe_id = pipe_name_val.lower()
			# check if page already exists
			key = ndb.Key(Fundpipe, pipe_id)
			if key.get():
				err_pipe_name_exists = True
		else:
			err_pipe_name_format = True
			
		# check for bitcoin address errors
		# TODO
			
		# output errors
		if (err_pipe_name_format == True) or (err_pipe_name_exists == True) or (err_no_valid_btc_address == True):
			self.render('main.html', pipe_name = pipe_name,  
				pipe_owner_address = pipe_owner_address, 
				err_pipe_name_format=err_pipe_name_format, 
				err_pipe_name_exists = err_pipe_name_exists, 
				err_no_valid_btc_address=err_no_valid_btc_address)
			return
		
		# if no error, write pipe to database
		pipe = Fundpipe(id=pipe_id)
		pipe.owner_address = pipe_owner_address
		pipe.put()
		
class NewMessagePage(Handler):
	def get(self):
		# show send page
		self.render('new-message.html')
		
	def post(self):
		recipient = self.request.get('recipient')
		message_text = self.request.get('messagetext')
		
		# create new database entry
		newmessage = message()
		newmessage.sender = "test";
		newmessage.recipient = recipient;
		newmessage.text = message_text;
		newmessage.put()
		
class LoginPage(Handler):
	def get(self):
		# show send page
		self.render('login.html')
		
	def post(self):
		useraddress = self.request.get('useraddress')
		userpassword = self.request.get('userpassword')
		
class VerifyPage(Handler):
	def get(self):
		# show send page
		self.render('verify.html')
		
	def post(self):
		useraddress = self.request.get('useraddress')
		userpassword = self.request.get('userpassword')
		userpasswordrepeat = self.request.get('userpasswordrepeat')
		
		# create user
		newuser = user()
		newuser.address = useraddress;
		newuser.passwordhash = userpassword;
		newuser.put()
		
		cookievalue = useraddress + '.' + bmt.make_cookie_hash(useraddress)
		
		self.response.set_cookie('user', cookievalue, max_age=86400, path='/', domain='bitcoin-messenger.appspot.com', secure=False)
		
		verifyinstructions_text = "To verify that your are the owner of bitcoin address ... please send ... BTC to address."
		
		self.render('verify.html', verifyinstructions_text=verifyinstructions_text)
		
		 
		
app = webapp2.WSGIApplication([
		webapp2.Route(r'/new', handler=NewMessagePage),
		webapp2.Route(r'/login', handler=LoginPage),
		webapp2.Route(r'/verify', handler=VerifyPage),
    webapp2.Route(r'/', handler=MainPage),
], debug=True)





