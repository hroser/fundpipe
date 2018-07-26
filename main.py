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

# to be able to import jinja2 , add to app.yaml
import jinja2
import webapp2

# for using datastore 
from google.appengine.ext import ndb
from base64 import b64encode
from base64 import b64decode

# use fundpipe tools
import fptools

# tell jinja2 where to look for files
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)
	
class Fundpipe(ndb.Model):
	"""Models a Fundpipe object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	owner_address = ndb.StringProperty()
	pipe_address = ndb.StringProperty()
	payout_pending = ndb.IntegerProperty()		# in satoshis
'''
class Fund(ndb.Model):
	"""Models a Fund object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	fundpipe = ndb.StringProperty()
	sender = ndb.StringProperty()
	receiver = ndb.StringProperty()
	fund_amount = ndb.IntegerProperty()		# in satoshis
	refund_owner = ndb.IntegerProperty()		# in satoshis
	refund_subsequent = ndb.IntegerProperty()		# in satoshis
	payout_pending = ndb.IntegerProperty()		# in satoshis
'''		
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
		err_creating_new_address = False
		
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
		pipe_owner_address_val = fptools.validate_btc_address(pipe_owner_address)
		if not pipe_owner_address_val:
			err_no_valid_btc_address = True
		
		if (err_pipe_name_exists == False) and (err_no_valid_btc_address == False):
			# create new address
			pipe_address = fptools.create_pipe_address(pipe_id)
			if not pipe_address:
				err_creating_new_address = True
			
		# output errors
		if (err_pipe_name_format == True) or (err_pipe_name_exists == True) or (err_no_valid_btc_address == True) or (err_creating_new_address == True):
			self.render('main.html', 
				pipe_name = pipe_name,  
				pipe_owner_address = pipe_owner_address, 
				err_pipe_name_format=err_pipe_name_format, 
				err_pipe_name_exists = err_pipe_name_exists, 
				err_no_valid_btc_address=err_no_valid_btc_address,
				err_creating_new_address = err_creating_new_address)
			return
		
		# if no error, write pipe to database
		pipe = Fundpipe(id=pipe_id)
		pipe.owner_address = pipe_owner_address
		pipe.pipe_address = pipe_address
		pipe.put()
		
		# redirect to pipe page
		self.redirect(str(pipe_name_val))
		
class PipePage(Handler):
	def get(self, requested_uri):
		# load pipe from database
		pipe_id = requested_uri.lower()
		key = ndb.Key(Fundpipe, pipe_id)
		pipe = key.get()
		
		# check if pipe exists
		if not pipe:
			self.response.out.write("Sorry this fundpipe does not exist")
			return
		
		# test create fund
		newfund = fptools.Fund()
		newfund.sender = "test";
		newfund.fundpipe = pipe_id;
		newfund.fund_amount = 100;
		newfund.put()
		
		# load funds
		funds = fptools.Fund.query(fptools.Fund.fundpipe == pipe_id).order(-fptools.Fund.created)
		
		# show pipe page
		self.render('pipe.html',
		pipe_name = pipe_id,
		pipe_address = pipe.pipe_address,
		funds = funds)		 
		
app = webapp2.WSGIApplication([
		webapp2.Route(r'/', handler=MainPage),
		webapp2.Route(r'/<requested_uri>', handler=PipePage)
], debug=True)





