#comment
import re
import random
import string
import hashlib
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import json
import logging

class Fundpipe(ndb.Model):
	"""Models a Fundpipe object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	pipe_name = ndb.StringProperty()
	owner_address = ndb.StringProperty()
	fund_address = ndb.StringProperty()
	refund_address = ndb.StringProperty()
	funds_received = ndb.IntegerProperty()		# in satoshis
	refunds_received = ndb.IntegerProperty()		# in satoshis
	payout_pending = ndb.IntegerProperty()		# in satoshis
	status = ndb.StringProperty()		# opening, open, closed
	update_required = ndb.BooleanProperty()		# if true, fundpipe needs to be updated

class Fund(ndb.Model):
	"""Models a Fund object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	fundpipe = ndb.StringProperty()
	sender = ndb.StringProperty()
	receiver = ndb.StringProperty()
	funded = ndb.IntegerProperty()		# in satoshis
	received = ndb.IntegerProperty()		# in satoshis
	payout_pending = ndb.IntegerProperty()		# in satoshis
	
class Refund(ndb.Model):
	"""Models a Refund object"""
	created = ndb.DateTimeProperty(auto_now_add=True)
	fundpipe = ndb.StringProperty()
	sender = ndb.StringProperty()
	receiver = ndb.StringProperty()
	refunded = ndb.IntegerProperty()		# in satoshis

def format_text_bold(text_inputstring):
	text_string = text_inputstring.group()
	text_outputstring = "<b>"+text_string[1:-1]+"</b>"
	return text_outputstring
	
def format_text_center(text_inputstring):
	text_string = text_inputstring.group()
	text_outputstring = "<center>"+text_string[2:-2]+"</center>"
	return text_outputstring
	
def format_text_links(text_inputstring):
	text_string = text_inputstring.group()
	if text_string[0:4] == "http":
		text_outputstring = "<a href=\"" + text_string + "\">" + text_string + "</a>"
	elif (text_string.find('@') >= 0):
		text_outputstring = "<a href=\"mailto:" + text_string + "\">" + text_string + "</a>"
	else:
		text_outputstring = "<a href=\"http://" + text_string + "\">" + text_string + "</a>"
	return text_outputstring
	
def validate_password(password_inputstring):
	if re.match(r'^[A-Za-z0-9@#$%^!?&+=]{6,}$', password_inputstring):
		return password_inputstring
	else:
		return None	
		
def validate_name(uri_inputstring):
	if re.match(r'^[A-Za-z0-9\-]{2,160}$', uri_inputstring):
		uri_inputstring = uri_inputstring.lower()
		return uri_inputstring
	else:
		return None	
  
def validate_email(email_inputstring):
	if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email_inputstring):
		return email_inputstring
	else:
		return None	
	
def validate_btc_address(btc_address):
	# read key file
	keys_str = open('keys.json').read()
	keys = json.loads(keys_str)
	
	# get bitcoin balance, use to verify bitcoin address
	api_key = keys['blockio-apikey']
	url = 'https://block.io/api/v2/get_address_balance/?api_key={}&addresses={}'.format(api_key, btc_address)
	response = urlfetch.fetch(url)
	
	# load json answer
	try:
		j = json.loads(response.content)
	except: 
		return None
	
	# check answer
	if (response.status_code == 200) and (j['status'] == 'success') :
		return btc_address
	else:
		if 'error_message' in j['data']:
			logging.debug("blockio api call error get_address_balance: " + j['data']['error_message'])
		return None	
	
def create_pipe_address():
	# read key file
	keys_str = open('keys.json').read()
	keys = json.loads(keys_str)
	
	# get bitcoin balance, use to verify bitcoin address
	api_key = keys['blockio-apikey']
	url = 'https://block.io/api/v2/get_new_address/?api_key={}'.format(api_key)
	response = urlfetch.fetch(url)
	
	# load json answer
	try:
		j = json.loads(response.content)
	except: 
		return None
	
	# check answer
	if (response.status_code == 200) and (j['status'] == 'success') :
		return j['data']['address']
	else:
		if 'error_message' in j['data']:
			logging.debug("blockio api call error get_new_address: " + j['data']['error_message'])
		return None	
	
def ndb_add_fund():
	# add fund to database
		newfund = Fund()
		newfund.sender = "ooooo";
		newfund.fundpipe = pipe_id;
		newfund.funded = 1000;
		newfund.put()
		
def update_pipe(pipe_id, amount):
	# distribute amount to funds
	proportion_project = 0.2
	
	# load fundpipe and funds
	funds = Fund.query(Fund.fundpipe == pipe_id)
	pipe = ndb.Key(Fundpipe, pipe_id).get()
	
	# update funds
	if (pipe.volume > 0):
		for fund in funds:
			# calculate and add proportion
			fund_add = int(float(fund.funded)/float(pipe.volume) * float((1-proportion_project) * amount))
			fund.received += fund_add
			fund.payout_pending += fund_add
		ndb.put_multi(funds)
		# add partial amount to project
		pipe_add = int(proportion_project * amount)
	else:
		# add full amount to project
		pipe_add = amount
	
	# update pipe
	pipe.volume += amount
	pipe.received += pipe_add
	pipe.payout_pending += pipe_add
	pipe.put()
	
	return

def process_amount_received_notification(data):
	notification_data = json.loads(data)
	
	# load pipe
	address = notification_data['address']
	pipe_list = Fundpipe.query(Fundpipe.pipe_address == address).fetch(1)

	if len(pipe_list) == 0:
		return 1
	pipe = pipe_list[0]
	pipe_id = pipe.key.id()
	
	# convert btc to satoshis
	amount = int(float(notification_data['amount_received']) * 100000000)
	
	# add amount to pipe
	update_pipe(pipe_id, amount)
	
	# create fund
	newfund = Fund()
	newfund.sender = "test22";
	newfund.fundpipe = pipe_id;
	newfund.funded = amount;
	newfund.received = 0;
	newfund.payout_pending = 0;
	newfund.put()
	
	return 0
		
#function make_salt returns a string of 5 random characters
def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(5))
	
# function make_pw_hash(name, pw) returns a hashed password 
# of the format: 
# HASH(name + pw + salt),salt
# use sha256

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (h, salt)

def make_cookie_hash(name):
	pw = 'ueSn!du98!hdWkO6'
	h = hashlib.sha256(name + pw).hexdigest()
	return h

def check_cookie_hash(name, hash):
	pw = 'ueSn!du98!hdWkO6'
	h = hashlib.sha256(name + pw).hexdigest()
	result = False;
	if h == hash:
		result = True;
	return result
	
# function valid_pw() returns True if a user's password 
# matches its hash
	
def valid_pw(name, pw, h):
	salt = h.split(',')[1]
	return h == make_pw_hash(name, pw, salt)
