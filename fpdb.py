#comment
import re
import random
import string
import hashlib
from google.cloud import datastore
import json
import logging
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
def ndb_add_fund():
	# add fund to database
	client = datastore.Client('fundpipe')
	query = client.query(kind='Fund')
	return list(query.fetch())
	'''
	newfund = Fund()
	newfund.sender = "ooooo";
	newfund.fundpipe = pipe_id;
	newfund.fund_amount = 1000;
	newfund.put()
	'''
