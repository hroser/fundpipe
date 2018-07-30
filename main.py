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

# random
from random import randint

# json 
import json

# tell jinja2 where to look for files
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

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
		pipe_id = fptools.validate_name(pipe_name)
		if pipe_id:
			# check if page already exists
			key = ndb.Key(fptools.Fundpipe, pipe_id)
			if key.get():
				err_pipe_name_exists = True
		else:
			err_pipe_name_format = True
			
		# check for bitcoin address errors
		pipe_owner_address_val = fptools.validate_btc_address(pipe_owner_address)
		if not pipe_owner_address_val:
			err_no_valid_btc_address = True
		
		#if (err_pipe_name_exists == False) and (err_no_valid_btc_address == False):
			# create new address
			#pipe_address = fptools.create_pipe_address()
			#if not pipe_address:
				#err_creating_new_address = True
			
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
		pipe = fptools.Fundpipe(id=pipe_id)
		pipe.pipe_name = pipe_name
		pipe.owner_address = pipe_owner_address
		pipe.fund_address = "0"
		pipe.refund_address = "0"
		pipe.funds_received = 0	# in satoshis
		pipe.refunds_received = 0	# in satoshis
		pipe.payout_pending = 0	# in satoshis
		pipe.volume = 0	# in satoshis
		pipe.status = "opening"
		update_required = True
		pipe.put()
		
		# redirect to pipe page
		self.redirect(str(pipe_id))
		
class PipePage(Handler):
	def get(self, requested_uri):
		# load pipe from database
		pipe_id = requested_uri.lower()
		key = ndb.Key(fptools.Fundpipe, pipe_id)
		pipe = key.get()
		
		# check if pipe exists
		if not pipe:
			self.response.out.write("Sorry this fundpipe does not exist")
			return
		'''
		# testing
		newamount = randint(1000,100000)
		
		# add amount to pipe
		fptools.update_pipe(pipe_id, newamount)
		
		# test create fund
		newfund = fptools.Fund()
		newfund.sender = "test";
		newfund.fundpipe = pipe_id;
		newfund.funded = newamount;
		newfund.received = 0;
		newfund.payout_pending = 0;
		newfund.put()
		'''
		# load funds
		funds = fptools.Fund.query(fptools.Fund.fundpipe == pipe_id).order(-fptools.Fund.created).fetch()
		
		# load refunds
		refunds = fptools.Refund.query(fptools.Refund.fundpipe == pipe_id).order(-fptools.Refund.created).fetch()
		
		# show pipe page
		self.render('pipe.html',
		pipe_name = pipe.pipe_name,
		fund_address = pipe.fund_address,
		funds = funds,
		refunds = refunds,
		project_received_total = 0.5 * pipe.funds_received,
		pipe_payout_pending = pipe.payout_pending,
		funders_received_from_funders = 0.5 * pipe.funds_received,
		funders_received_from_refunds = pipe.refunds_received,
		funders_received_total = 0.5 * pipe.funds_received + pipe.refunds_received,
		total_funded = pipe.funds_received,
		total_refunded = pipe.refunds_received,
		pipe_status = pipe.status)		
			
class Cron(Handler):
	def get(self):
		pass
		
class Notification(Handler):
	def get(self):
		
		'''
		sample call
		http://www.fundpipe.net/n?type=address;key=xxx;data={"address": "TESTADR", "amount_received": "0.01000000", "txid": "7af5cf9f2...", "confirmations": 0}
		'''
		# read key file
		keys_str = open('keys.json').read()
		keys = json.loads(keys_str)
		
		type = self.request.get('type')
		data = self.request.get('data')
		key = self.request.get('key')
		
		if (key != keys['fundpipe-apikey']):
			self.write('denied')
			return
		
		# get notification data
		if (type == "address"):
			notification_data = json.loads(data)
			if (float(notification_data['amount_received']) > 0):
				result = fptools.process_amount_received_notification(data)
				if (result == 0):
					self.write('success')
				else:
					self.write('fail')
		
	def post(self):
		notification = json.loads(self.request.body)
		
		type = notification['type']
		data = notification['data']
		
		# get notification data
		if (type == "address"):
			notification_data = json.loads(data)
			if (float(notification_data['amount_received']) > 0):
				result = fptools.process_amount_received_notification(data)
				if (result == 0):
					self.write('success')
				else:
					self.write('fail')
		
app = webapp2.WSGIApplication([
		webapp2.Route(r'/', handler=MainPage),
		webapp2.Route(r'/n/cron', handler=Cron),
		webapp2.Route(r'/n', handler=Notification),
		webapp2.Route(r'/<requested_uri>', handler=PipePage)
], debug=True)





