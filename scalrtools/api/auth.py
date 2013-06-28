#coding:utf-8

import utils
import urllib

class KeyAuth(object):
	"""
	Authenticate using an API Key
	"""
	def __init__(self, key_id, access_key):
		self.key_id = key_id
		self.access_key = access_key

	def authorize(self, request_body):
		"""
		Modify the request_body to authorize it
		"""
		signature, timestamp = utils.sign_http_request_v3(request_body, self.key_id, self.access_key)
		request_body["TimeStamp"] = timestamp
		request_body["Signature"] = signature

		request_body["KeyID"] = self.key_id


class LDAPAuth(object):
	"""
	Authenticate using LDAP
	"""
	def __init__(self, username, password):
		self.username = username
		self.password = password

	def authorize(self, request_body):
		assert "EnvID" in request_body, "EnvID must be specified for LDAP-authorized API calls"
		request_body.update({
			"AuthType": "ldap",
			"Login": self.username,
			"Password": self.password
		})