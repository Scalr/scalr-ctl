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

import types_ as types

class ScalrConnection(object):
	'''
	implements Scalr API
	'''

	def __init__(self, url, key_id, access_key, env_id=None, api_version=None, logger=None):
		self.url = url
		self.key_id  = key_id
		self.access_key = access_key
		self.env_id = env_id
		self.api_version = api_version 
		self._logger = logger or logging.getLogger(__name__)
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
		request_body['AuthVersion'] = '3'
		if self.env_id and self.env_id != 'None':
			request_body['EnvID'] = self.env_id
		#request_body['SysDebug'] = '1'
		
		if {} != params :
			for key, value in params.items():
				if isinstance(value, dict):
					for k,v in value.items():
						request_body['%s[%s]'%(key,k)] = v
				else:
					request_body[key] = value
					
		signature, timestamp = sign_http_request_v3(request_body, self.key_id, self.access_key)	
		
		request_body["TimeStamp"] = timestamp	
		request_body["Signature"] = signature	
		
		post_data = urlencode(request_body)

		self._logger.debug('POST URL: \n%s' % self.url)
		self._logger.debug('POST DATA: \n%s' % post_data)
		
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
		except BaseException,e:
			raise ScalrAPIError("Cannot connect to Scalr: %s" % str(e))
			
		resp_body = response.read()
		self._logger.debug("SCALR RESPONSE: \n%s", resp_body)
		
		# Parse XML response
		xml = None
		try:
			xml = xml_strip(parseString(resp_body))
		except (Exception, BaseException), e:
			raise ScalrAPIError("Cannot parse XML. %s" % [str(e)])		
		
		self._logger.debug('VALID XML: \n%s' % xml.toprettyxml())
		
		return xml

	def dm_create_source(self, type, url, auth_login=None, auth_password=None):
		"""
		@return Result[]
		"""
		params = {}
		
		params['Type'] = type
		params['URL']  = url
		if auth_login	: params['AuthLogin'] 	= auth_login
		if auth_password: params['AuthPassword']= auth_password
		
		return self._request(command="DmSourceCreate", params=params, response_reader=self._read_dm_create_source_response)		
		
	def dm_create_application(self, name, source_id, pre_deploy_script=None, post_deploy_script=None):
		"""
		@return ApplicationID[]
		"""
		params = {}
		
		params['Name'] = name
		params['SourceID']  = source_id
		if pre_deploy_script	: params['PreDeployScript'] = pre_deploy_script
		if post_deploy_script	: params['PostDeployScript']= post_deploy_script
		
		return self._request(command="DmApplicationCreate", params=params, response_reader=self._read_dm_create_application_response)	
	
		
	def dm_list_sources(self):
		"""
		@return Source[]
		"""
		return self._request("DmSourcesList", response_reader=self._read_dm_list_sources_response)	
	
	
	def dm_list_applications(self):
		"""
		@return Application[]
		"""
		return self._request("DmApplicationsList", response_reader=self._read_dm_list_applications_response)	
	
	
	def dm_get_deployment_task_log(self, task_id, start_from=None, records_limit=None):
		"""
		@return DMTaskLog[]
		"""
		params = {}
		
		params['DeploymentTaskID'] = task_id
		if start_from	 : params['StartFrom'] 	  = start_from
		if records_limit : params['RecordsLimit'] = records_limit
		
		return self._request(command="DmDeploymentTaskGetLog", params=params, response_reader=self._dm_get_deployment_task_log_response)	
	
	
	def dm_deploy_application(self, app_id, farm_role_id, remote_path):
		"""
		@return DeployTaskResult[]
		"""
		params = {}
		
		params['ApplicationID'] = app_id
		params['FarmRoleID']  = farm_role_id
		params['RemotePath'] = remote_path
		
		return self._request(command="DmApplicationDeploy", params=params, response_reader=self._read_dm_deploy_application_response)		
	
	
	def dm_list_deployment_tasks(self, farm_role_id=None, app_id=None, server_id=None):
		"""
		@return ApplicationID[]
		"""
		params = {}
		
		if farm_role_id	: params['FarmRoleID'] = farm_role_id
		if app_id		: params['ApplicationID'] = app_id
		if server_id	: params['ServerID']= server_id
		
		return self._request(command="DmDeploymentTasksList", params=params, response_reader=self._read_dm_list_deployment_tasks_response)	
	

	def dm_get_deployment_task_status(self, task_id):
		"""
		@return DeployTaskResult[]
		"""
		params = {}
		
		params['DeploymentTaskID'] = task_id
		
		return self._request(command="DmDeploymentTaskGetStatus", params=params, response_reader=self._read_dm_get_deployment_task_status_response)		
		
	def list_apache_virtual_hosts(self):
		"""
		@return VirtualHost[]
		"""
		return self._request("ApacheVhostsList", response_reader=self._read_list_apache_virtual_hosts_response)
	
	
	def list_dns_zones(self):
		"""
		@return DNSZone[]
		"""
		return self._request("DNSZonesList", response_reader=self._read_list_dns_zones_response)

	
	def list_scripts(self):
		"""
		@return Script[]
		"""
		return self._request("ScriptsList", response_reader=self._read_list_scripts_response)
	
	
	def list_farms(self):
		"""
		@return Farm[]
		"""
		return self._request("FarmsList", response_reader=self._read_list_farms_response)
			
			
	def get_farm_status(self, id=None, name=None):
		"""
		@return String
		"""
		assert id or name
		for farm in self.list_farms():
			if farm.id == id or (name and farm.name == name):
				return farm.status
		return None
	
	
	def get_farm_id(self, name):
		"""
		@return String
		"""
		for farm in self.list_farms():
			if farm.name == name:
				return farm.id
		return None
	
	
	def get_farm_name(self, id):
		"""
		@return String
		"""
		for farm in self.list_farms():
			if farm.id == id:
				return farm.name
		return None
	
	
	def get_application_id(self, name):
		"""
		@return String
		"""
		for app in self.dm_list_applications():
			if app.name == name:
				return app.id
		return None
	
	
	def get_application_name(self, name):
		"""
		@return String
		"""
		for app in self.dm_list_applications():
			if app.id == name:
				return app.name
		return None
	
			
	def list_roles(self, platform=None, name=None, prefix=None, image_id=None):
		"""
		@return Role[]
		"""
		params = {}
		
		if platform : params['Platform']= platform
		if name		: params['Name'] 	= name
		if prefix	: params['Prefix'] 	= prefix
		if image_id : params['ImageID'] = image_id
		
		return self._request(command="RolesList", params=params, response_reader=self._read_list_roles_response)


	def list_dns_zone_records(self, zone_name):
		"""
		@return DnsZoneRecord[]
		"""
		params = {'ZoneName':zone_name} if zone_name else {}
		
		return self._request(command="DNSZoneRecordsList", params=params, response_reader=self._read_list_dns_zone_records_response)	
		
	
	def list_events(self, farm_id, start_from=None, records_limit=None):
		"""
		@return Event[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		if start_from	 : params['StartFrom'] 	  = start_from
		if records_limit : params['RecordsLimit'] = records_limit
		
		return self._request(command="EventsList", params=params, response_reader=self._read_list_events_response)		
	
	def list_logs(self, farm_id, server_id=None, start_from=None, records_limit=None):
		"""
		@return LogRecord[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		if server_id	 : params['ServerID'] = server_id
		if start_from	 : params['StartFrom'] 	  = start_from
		if records_limit : params['RecordsLimit'] = records_limit
		
		return self._request(command="LogsList", params=params, response_reader=self._read_list_logs_response)


	def get_farm_stats(self, farm_id, date=None):
		"""
		@return FarmStat[]
		"""
		params = {}
		
		params['FarmID']= farm_id
		if date: params['Date'] = date
		
		return self._request(command="FarmGetStats", params=params, response_reader=self._read_get_farm_stats_response)	
	
	
	def get_script_details(self,script_id):
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


	def get_statistics_graph_URL(self, object_type, object_id, watcher_name, graph_type):
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
	
		
	def launch_server(self, farm_role_id, increase_max_instances=False):
		"""
		@return ServerID
		"""
		params = {}
		
		params['FarmRoleID']= farm_role_id
		params['IncreaseMaxInstances'] = '1' if increase_max_instances else '0'
		
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
		@return FarmRole[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		
		return self._request(command="FarmGetDetails", params=params, response_reader=self._read_get_farm_details_response)	
			
	
	def get_farm_role_properties(self, farm_id):
		"""
		@return FarmRoleProperties[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		
		return self._request(command="FarmGetDetails", params=params, response_reader=self._read_get_farm_role_properties_response)		
	
	
	def list_servers(self, farm_id, farm_role_id = None):
		"""
		@return Server[]
		"""
		params = {}
		
		params['FarmID'] = farm_id
		#servers = self._request(command="FarmGetDetails", params=params, response_reader=self._read_list_servers_response)
		roles = self._request(command="FarmGetDetails", params=params, response_reader=self._read_get_farm_role_properties_response)
		servers = []
		for role in roles:
			if role.servers:
				for server in role.servers:
					server.name = role.name
					server.farm_role_id = role.farm_role_id
					servers.append(server)
				
			
		if farm_role_id:
			for server in servers:
				if server.farm_role_id != farm_role_id:
					servers.remove(server) 
		return servers
	
		
	def execute_script(self,farm_id,script_id,timeout,async,farm_role_id=None,server_id=None,config_variables=None,revision=None):
		"""
		@return Result
		"""
		params = {}
		#params['AuthVersion'] = '2'
		params['FarmID'] = farm_id
		params['ScriptID'] = script_id
		params['Timeout'] = timeout
		params['Async'] = async
		if farm_role_id: params['FarmRoleID'] = farm_role_id
		if server_id: params['ServerID'] = server_id
		if config_variables: params['ConfigVariables'] = config_variables
		if revision: params['Revision'] = revision
		
		return self._request(command="ScriptExecute", params=params, response_reader=self._read_execute_script_response)

	
	def list_environments(self):
		"""
		@return Environment[]
		"""
		return self._request("EnvironmentsList", response_reader=self._read_list_environments_response)
			
			
	def _read_dm_create_source_response(self, xml):
		return self._read_response(xml, node_name='SourceID', cls=types.SourceID, simple_response=True)
	
	
	def _read_dm_create_application_response(self, xml):
		return self._read_response(xml, node_name='ApplicationID', cls=types.ApplicationID, simple_response=True)
	
	
	def _read_dm_deploy_application_response(self, xml):
		return self._read_response(xml, node_name='DeploymentTasksSet', cls=types.DeploymentTaskResult)

	
	def _read_dm_list_deployment_tasks_response(self, xml):
		return self._read_response(xml, node_name='DeploymentTasksSet', cls=types.DeploymentTaskResult)		
	
	
	def _read_dm_list_sources_response(self, xml):
		return self._read_response(xml, node_name='SourceSet', cls=types.Source)			

	
	def _dm_get_deployment_task_log_response(self, xml):
		return self._read_response(xml, node_name='LogSet', cls=types.DMTaskLog, wrap_page=True)
	
	def _read_dm_get_deployment_task_status_response(self, xml):
		return self._read_response(xml, node_name='DeploymentTaskStatus', cls=types.DeploymentTask, simple_response=True)	
	

	def _read_dm_list_applications_response(self, xml):
		return self._read_response(xml, node_name='ApplicationSet', cls=types.Application)
	
	
	def _read_get_script_details_response(self, xml):
		return self._read_response(xml, node_name='ScriptRevisionSet', cls=types.ScriptRevision)
	
			
	def _read_list_apache_virtual_hosts_response(self, xml):
		return self._read_response(xml, node_name='ApacheVhostSet', cls=types.VirtualHost)
		
	
	def _read_list_dns_zones_response(self, xml):
		return self._read_response(xml, node_name='DNSZoneSet', cls=types.DNSZone)
	
	
	def _read_list_scripts_response(self, xml):
		return self._read_response(xml, node_name='ScriptSet', cls=types.Script)
	
	
	def _read_list_farms_response(self, xml):
		return self._read_response(xml, node_name='FarmSet', cls=types.Farm)
	
	
	def _read_list_roles_response(self, xml):
		return self._read_response(xml, node_name='RoleSet', cls=types.Role)
	
	
	def _read_list_dns_zone_records_response(self, xml):
		return self._read_response(xml, node_name='ZoneRecordSet', cls=types.DnsZoneRecord)
	
	
	def _read_list_events_response(self, xml):
		return self._read_response(xml, node_name='EventSet', cls=types.Event, wrap_page=True)
	
	
	def _read_list_logs_response(self, xml):
		return self._read_response(xml, node_name='LogSet', cls=types.LogRecord, wrap_page=True)
	
	
	def _read_get_farm_stats_response(self, xml):
		return self._read_response(xml, node_name='StatisticsSet', cls=types.FarmStat)
	

	def _read_get_farm_details_response(self, xml):
		return self._read_response(xml, node_name='FarmRoleSet', cls=types.FarmRole)
	
	
	def _read_get_farm_role_properties_response(self, xml):
		return self._read_response(xml, node_name='FarmRoleSet', cls=types.FarmRoleProperties)
	
	
	def _read_list_servers_response(self, xml):
		return self._read_response(xml, node_name='ServerSet', cls=types.Server) # FarmRoleSet
	
		
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
	
	
	def _read_list_environments_response(self, xml):
		return self._read_response(xml, node_name='EnvironmentSet', cls=types.Environment)
		

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
				#utterly experimental, can ruin everything
				for node in xml.getElementsByTagName(node_name):
					for child in node.childNodes:
						ret.append(cls.fromxml(child))
						
				'''	
				#this block of code was substituted by experemental one
				for child in response.childNodes:
					
					if node_name == child.nodeName:
						obj_set = child.childNodes
						for node in obj_set:
							ret.append(cls.fromxml(node))
				'''
						
			if wrap_page:
				page = types.Page.fromxml(response)
				page.scalr_objects = ret
				return page
		#print ret
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


def sign_http_request_v3(data, key_id, access_key, timestamp=None):
	date = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", timestamp or time.gmtime())
	data['TimeStamp']=date
	canonical_string = 	"%s:%s:%s" % (data['Action'], key_id, data['TimeStamp'])
	digest = hmac.new(access_key, canonical_string, hashlib.sha256).digest()
	sign = binascii.b2a_base64(digest).strip()
	return sign, date		

		
def sign_http_request_v1(data, key, timestamp=None):
	date = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", timestamp or time.gmtime())
	data['TimeStamp']=date
	canonical_string = get_canonical_string(data) if hasattr(data, "__iter__") else data
	digest = hmac.new(key, canonical_string, hashlib.sha256).digest()
	sign = binascii.b2a_base64(digest).strip()
	
	return sign, date


def get_canonical_string (params={}):
	s = ""
	for key in sorted(params.keys(), key=str.lower):
		s = s + str(key) + str(params[key])
	return s
