'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

import binascii
import hashlib
import logging
import hmac


try:
	import timemodule as time
except ImportError:
	import time
		
from xml.dom.minidom import parseString
from urllib import urlencode, splitnport
from urllib2 import urlopen, Request, URLError, HTTPError

import types

class ScalrConnection(object):
	'''
	implements Scalr API
	'''

	def __init__(self, url, key_id, access_key, api_version=None):
		self.url = url
		self.key_id  = key_id
		self.access_key = access_key
		self.api_version = api_version or '2.1.0'
		self._logger = logging.getLogger(__name__)
		self.last_transaction_id = None
	
		
	def fetch(self, command, **params):
		"""
		@return object
		"""
		# Perform HTTP request
		request_body = {}
		request_body["Action"] = command
		request_body["Version"] = self.api_version
		request_body["KeyID"] = self.key_id
		
		if {} != params :
			for key, value in params.items():
				if isinstance(value, dict):
					for k,v in value.items():
						request_body['%s[%s]'%(key,k)] = v
				else:
					request_body[key] = value

		signature, timestamp = sign_http_request(request_body, self.access_key)	
		
		request_body["TimeStamp"] = timestamp	
		request_body["Signature"] = signature	
		
		post_data = urlencode(request_body)
		
		response = None
		try:
			req = Request(self.url, post_data, {})
			response = urlopen(req)
		except URLError, e:
			if isinstance(e, HTTPError):
				resp_body = e.read() if e.fp is not None else ""
				raise ScalrAPIError("Request failed. %s. URL: %s. Service message: %s" % (e, self.url, resp_body))				
			else:
				host, port = splitnport(req.host, req.port or 443)
				raise ScalrAPIError("Cannot connect to Scalr on %s:%s. %s" 
						% (host, port, str(e)))

		resp_body = response.read()
		self._logger.debug("Scalr response: %s", resp_body)

		# Parse XML response
		xml = None
		try:
			xml = xml_strip(parseString(resp_body))
		except (Exception, BaseException), e:
			raise ScalrAPIError("Cannot parse XML. %s" % [str(e)])		
		return xml
		
	
		
	def apache_virtual_host_list(self):
		"""
		@return VirtualHost[]
		"""
		return self._request("ApacheVhostsList", self._read_apache_virtual_host_list_response)
	
	
	def dns_zones_list(self):
		"""
		@return DNSZone[]
		"""
		return self._request("DNSZonesListResponse", self._read_dns_zones_list_response)

	
	def scripts_list(self):
		"""
		@return Script[]
		"""
		return self._request("ScriptsList", self._read_scripts_list_response)
	
	def farms_list(self):
		"""
		@return Farm[]
		"""
		return self._request("FarmsList", self._read_farms_list_response)
	
	
	def roles_list(self, platform=None, name=None, prefix=None, image_id=None):
		"""
		@return Role[]
		"""
		params = {}
		
		if platform : params['Platform']= platform
		if name		: params['Name'] 	= name
		if prefix	: params['Prefix'] 	= prefix
		if image_id : params['ImageID'] = image_id
		
		return self._request(command="RolesList", params=params, response_reader=self._read_roles_list_response)


	def dns_zone_record_list(self, zone_name):
		"""
		@return DnsZoneRecord[]
		"""
		params = {'ZoneName':zone_name} if zone_name else {}
		
		return self._request(command="DNSZoneRecordsList", params=params, response_reader=self._read_roles_list_response)	
		
	
	def events_list(self, farm_id, name=None, start_from=None, records_limit=None):
		"""
		@return Event[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		if name			 : params['Name'] 		  = name
		if start_from	 : params['StartFrom'] 	  = start_from
		if records_limit : params['RecordsLimit'] = records_limit
		
		return self._request(command="EventsList", params=params, response_reader=self._read_events_list_response)		
	
	def logs_list(self, farm_id, server_id=None, start_from=None, records_limit=None):
		"""
		@return LogRecord[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		if server_id	 : params['ServerID'] = server_id
		if start_from	 : params['StartFrom'] 	  = start_from
		if records_limit : params['RecordsLimit'] = records_limit
		
		return self._request(command="LogsList", params=params, response_reader=self._read_logs_list_response)


	def farm_get_stats(self, farm_id, date=None):
		"""
		@return FarmStat[]
		"""
		params = {}
		
		params['FarmID']= farm_id
		if date: params['Date'] = date
		
		return self._request(command="FarmGetStats", params=params, response_reader=self._read_get_farm_stats_response)	
	
	
	def script_get_details(self,script_id):
		"""
		@return ScriptDetails
		"""
		params = {}
		
		params['ScriptID']= script_id
		
		return self._request(command="ScriptGetDetails", params=params, response_reader=self._read_get_script_details_response)

		
	def get_bundle_task_status(self, bundle_task_id):
		"""
		@return BundleTask
		"""
		params = {}
		
		params['BundleTaskID']= bundle_task_id
		
		return self._request(command="BundleTaskGetStatus", params=params, response_reader=self._read_get_bundle_task_status_response)	


	def get_statistic_graph_URL(self, object_type, object_id, watcher_name, graph_type):
		"""
		@return GraphURL
		"""
		params = {}
		
		params['ObjectType'] = object_type
		params['ObjectID'] = object_id
		params['WatcherName'] = watcher_name
		params['GraphType'] = graph_type
		
		return self._request(command="StatisticsGetGraphURL", params=params, response_reader=self._read_get_statistic_graph_URL_response)	
	

	def terminate_farm(self, farm_id,keep_ebs,keep_eip,keep_dns_zone):
		"""
		@return Result
		"""
		params = {}
		
		params['FarmID'] = farm_id
		params['KeepEBS'] = keep_ebs
		params['KeepEIP'] = keep_eip
		params['KeepDNSZone'] = keep_dns_zone
		
		return self._request(command="FarmTerminate", params=params, response_reader=self._read_terminate_farm_response)	


	def launch_farm(self, farm_id):
		"""
		@return Result
		"""
		params = {}
		
		params['FarmID'] = farm_id
		
		return self._request(command="FarmLaunch", params=params, response_reader=self._read_launch_farm_response)	
	
	
	#not tested
	def create_server_image(self, server_id, role_name):
		"""
		@return BundleTaskID
		"""
		params = {}
		
		params['ServerID']= server_id
		params['RoleName']= role_name
		
		return self._request(command="ServerImageCreate", params=params, response_reader=self._read_create_server_image_response)	
	
		
	def launch_server(self, farm_role_id):
		"""
		@return ServerID
		"""
		params = {}
		
		params['FarmRoleID']= farm_role_id
		
		return self._request(command="ServerLaunch", params=params, response_reader=self._read_launch_server_response)	



	def create_apache_vhost(self, domain_name,farm_id,farm_role_id,document_root_dir,enable_ssl,ssl_private_key=None,ssl_certificate=None):
		"""
		@return Result
		"""
		params = {}
		
		params['DomainName'] = domain_name
		params['FarmID'] = farm_id
		params['FarmRoleID'] = farm_role_id
		params['DocumentRootDir'] = document_root_dir
		params['EnableSSL'] = enable_ssl
		#TODO: Find out how to use SSL certs & keys and where to base64encode it. 
		if ssl_private_key: params['SSLPrivateKey'] = binascii.b2a_base64(ssl_private_key).strip()
		if ssl_certificate: params['SSLCertificate'] = binascii.b2a_base64(ssl_certificate).strip()
		
		return self._request(command="ApacheVhostCreate", params=params, response_reader=self._read_create_apache_vhost_response)			
		
		
	def create_dns_zone(self, domain_name, farm_id=None,farm_role_id=None):
		"""
		@return Result
		"""
		params = {}
		
		params['DomainName']= domain_name
		if farm_id: params['FarmID'] = farm_id
		if farm_role_id: params['FarmRoleID'] = farm_role_id
		
		return self._request(command="DNSZoneCreate", params=params, response_reader=self._read_create_dns_zone_response)			


	def add_dns_zone_record(self, zone_name,type,ttl,record_name,value,priority=None,weight=None,port=None):
		"""
		@return Result
		"""
		params = {}
		
		params['ZoneName'] = zone_name
		params['Type'] = type
		params['TTL'] = ttl
		params['Name'] = record_name
		params['Value'] = value
		if priority: params['Priority'] = priority
		if weight: params['Weight'] = weight
		if port: params['Port'] = port
		
		return self._request(command="DNSZoneRecordAdd", params=params, response_reader=self._read_add_dns_zone_record_response)	


	def remove_dns_zone_record(self, dzone_name, record_id):
		"""
		@return Result
		"""
		params = {}
		
		params['ZoneName']= dzone_name
		params['RecordID'] = record_id
		
		return self._request(command="DNSZoneRecordRemove", params=params, response_reader=self._read_remove_dns_zone_record_response)	


	def reboot_server(self, server_id):
		"""
		@return Result
		"""
		params = {}
		
		params['ServerID'] = server_id
		
		return self._request(command="ServerReboot", params=params, response_reader=self._read_reboot_server_response)		
	

	def terminate_server(self, server_id, decrease_min_instances_setting=None):
		"""
		@return Result
		"""
		params = {}
		
		params['ServerID'] = server_id
		if decrease_min_instances_setting: params['DecreaseMinInstancesSetting'] = decrease_min_instances_setting
		
		return self._request(command="ServerTerminate", params=params, response_reader=self._read_terminate_server_response)	

	
	def get_farm_details(self, farm_id):
		"""
		@return Result
		"""
		params = {}
		
		params['FarmID'] = farm_id
		
		return self._request(command="FarmGetDetails", params=params, response_reader=self._read_get_farm_details_response)	
			
		
	def execute_script(self,farm_id,script_id,timeout,async,farm_role_id=None,server_id=None,config_variables=None,revision=None):
		"""
		@return Result
		"""
		params = {}
		
		params['FarmID'] = farm_id
		params['ScriptID'] = script_id
		params['Timeout'] = timeout
		params['Async'] = async
		if farm_role_id: params['FarmRoleID'] = farm_role_id
		if server_id: params['ServerID'] = server_id
		#TODO: find out how to pass config variables
		if config_variables: params['ConfigVariables'] = config_variables
		if revision: params['Revision'] = revision
		
		return self._request(command="ScriptExecute", params=params, response_reader=self._read_execute_script_response)
			
			

	def _read_get_script_details_response(self, xml):
		return self._read_response(xml, node_name='ScriptRevisionSet', cls=types.ScriptRevision)
	
			
	def _read_apache_virtual_host_list_response(self, xml):
		return self._read_response(xml, node_name='ApacheVhostSet', cls=types.VirtualHost)
		
	
	def _read_dns_zones_list_response(self, xml):
		return self._read_response(xml, node_name='DNSZoneSet', cls=types.DNSZone)
	
	
	def _read_scripts_list_response(self, xml):
		return self._read_response(xml, node_name='ScriptSet', cls=types.Script)
	
	
	def _read_farms_list_response(self, xml):
		return self._read_response(xml, node_name='FarmSet', cls=types.Farm)
	
	
	def _read_roles_list_response(self, xml):
		return self._read_response(xml, node_name='RoleSet', cls=types.Role)
	
	
	def _read_dns_zone_record_list_response(self, xml):
		return self._read_response(xml, node_name='ZoneRecordSet', cls=types.DnsZoneRecord)
	
	
	def _read_events_list_response(self, xml):
		return self._read_response(xml, node_name='EventSet', cls=types.Event, wrap_page=True)
	
	
	def _read_logs_list_response(self, xml):
		return self._read_response(xml, node_name='LogSet', cls=types.LogRecord, wrap_page=True)
	
	
	def _read_get_farm_stats_response(self, xml):
		return self._read_response(xml, node_name='StatisticsSet', cls=types.FarmStat)
	

	def _read_get_farm_details_response(self, xml):
		return self._read_response(xml, node_name='FarmRoleSet', cls=types.FarmRole)
	
	
	def _read_get_bundle_task_status_response(self, xml):
		return self._read_response(xml, node_name='BundleTaskGetStatusResponse', cls=types.BundleTask, simple_response=True)
	
	
	def _read_create_server_image_response(self, xml):
		return self._read_response(xml, node_name='ServerCreateImageResponse', cls=types.BundleTaskID, simple_response=True)
	
	
	def _read_launch_server_response(self, xml):
		return self._read_response(xml, node_name='ServerLaunchResponse', cls=types.ServerID, simple_response=True)
	
	
	def _read_get_statistic_graph_URL_response(self, xml):
		return self._read_response(xml, node_name='StatisticsGetGraphURLResponse', cls=types.GraphURL, simple_response=True)
	
	
	def _read_create_apache_vhost_response(self, xml):
		return self._read_response(xml, node_name='ApacheVhostCreate', cls=types.Result, simple_response=True)
	
	
	def _read_create_dns_zone_response(self, xml):
		return self._read_response(xml, node_name='DNSZoneCreateResponse', cls=types.Result, simple_response=True)
	
	
	def _read_add_dns_zone_record_response(self, xml):
		return self._read_response(xml, node_name='DNSZoneRecordAddResponse', cls=types.Result, simple_response=True)
	

	def _read_remove_dns_zone_record_response(self, xml):
		return self._read_response(xml, node_name='DNSZoneRecodRemoveResponse', cls=types.Result, simple_response=True)
	

	def _read_terminate_farm_response(self, xml):
		return self._read_response(xml, node_name='FarmTerminateResponse', cls=types.Result, simple_response=True)
	
	
	def _read_launch_farm_response(self, xml):
		return self._read_response(xml, node_name='FarmLaunchResponse', cls=types.Result, simple_response=True)


	def _read_reboot_server_response(self, xml):
		return self._read_response(xml, node_name='ServerRebootResponse', cls=types.Result, simple_response=True)	
	
	
	def _read_terminate_server_response(self, xml):
		return self._read_response(xml, node_name='TerminateInstanceResponse', cls=types.Result, simple_response=True)		
	
	
	def _read_execute_script_response(self, xml):
		return self._read_response(xml, node_name='ExecuteScriptResponse', cls=types.Result, simple_response=True)	
	
	

	def _read_response(self, xml, node_name, cls, wrap_page=False, simple_response=False):
		response = xml.documentElement
		ret = list()
		
		if not self.is_document_empty(response):
			self.last_transaction_id = self.get_transaction_id(response)
			
			if response.nodeName == 'Error':
				raise ScalrAPIError.fromxml(response)

			if simple_response:
				ret.append(cls.fromxml(response))
			else:			
				for child in response.childNodes:
					if node_name == child.nodeName:
						obj_set = child.childNodes
						for node in obj_set:
							ret.append(cls.fromxml(node))
						
			if wrap_page:
				page = types.Page.fromxml(response)
				page.scalr_objects = ret
				return page

		return ret

				
	def _request (self, command, params={}, response_reader=None, response_reader_args=None):
		xml = self.fetch(command, **params)
		response_reader_args = response_reader_args or ()
		return response_reader(xml, *response_reader_args)
	
		
	def get_transaction_id(self, response):
		id = None
		for child in response.childNodes:
			if 'TransactionID' == child.nodeName:
				return child.firstChild.nodeValue.strip()
		return id
	
	
	def is_document_empty(self, response):
		return not response.firstChild.hasChildNodes() if response and response.firstChild else False

	
class ScalrAPIError(Exception):
	
	@classmethod
	def fromxml(cls, xml):
		child = types.get_items_first_child(xml, 'Message')
		msg = child.nodeValue.strip() if child else 'Cannot parse document'
		return ScalrAPIError(msg)
	
		
def xml_strip(el):
	for child in list(el.childNodes):
		if child.nodeType==child.TEXT_NODE and child.nodeValue.strip() == '':
			el.removeChild(child)
		else:
			xml_strip(child)
	return el	

		
def sign_http_request(data, key, timestamp=None):
	date = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", timestamp or time.gmtime())
	data['TimeStamp']=date
	canonical_string = get_canonical_string(data) if hasattr(data, "__iter__") else data
	digest = hmac.new(key, canonical_string, hashlib.sha256).digest()
	sign = binascii.b2a_base64(digest).strip()
	
	return sign, date


def get_canonical_string (params={}):
	s = ""
	for key, value in sorted(params.items()):
		s = s + str(key) + str(value)
	return s