'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

try:
	import timemodule as time
except ImportError:
	import time

from scalrtools.collections_ import OrderedDict
		
class Page(object):
	total_records = None
	start_from = None
	records_limit = None
	scalr_objects = None
	
	def __init__(self,total_records=None, start_from=None, records_limit=None, scalr_objects=None):
		self.total_records = total_records
		self.start_from = start_from
		self.records_limit = records_limit
		self.scalr_objects = scalr_objects or []
	
	@classmethod	
	def fromxml(cls,xml):
		get_value = lambda tag: get_items_first_child(xml, tag).nodeValue.strip()
		page = Page()
		page.total_records = get_value('TotalRecords')
		page.start_from = get_value('StartFrom')
		page.records_limit = get_value('RecordsLimit')
		return page


class ScalrObject(object):
	__titles__ = None
	__aliases__ = None
	
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
	

	@classmethod
	def parse_response(cls,xml):
		result = {}
		for key,tag in cls.__titles__.items():
			elements = xml.getElementsByTagName(tag)
			
			if not elements: 
				continue 
			
			parent_node = elements[0]
			if parent_node.hasChildNodes and parent_node.firstChild:
				
				#parent node has only one text child 
				if '#text' == parent_node.firstChild.nodeName:
					result[key] = parent_node.firstChild.nodeValue.strip() if parent_node else None
				
				#parent node has has many Items, each has one child with text child node	
				elif 'Item' == parent_node.firstChild.nodeName:
					vars = []
					for item in parent_node.childNodes:
						vars.append(item.firstChild.firstChild.nodeValue.strip())
					result[key] = vars
					
				#parent node has has many childs, each has one text child	
				else:
					internal_vars = {}
					for child in parent_node.childNodes:
						if child.hasChildNodes and child.firstChild and '#text'==child.firstChild.nodeName:
							value = child.firstChild.nodeValue.strip() 
							internal_vars[str(child.nodeName)] = str(value)
					result[key] = internal_vars
		return result


	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		return cls(**kv)


class DynamicScalrObject(ScalrObject):
	data = None
	__title__ = None

	@classmethod
	def parse_response(cls,xml):
		elements = xml.getElementsByTagName(cls.__title__)
		
		if not elements: 
			return {}
		
		parent_node = elements[0]
		
		if parent_node.hasChildNodes and parent_node.firstChild:
				
			internal_vars = {}
			for child in parent_node.childNodes:
				if child.hasChildNodes and child.firstChild and '#text'==child.firstChild.nodeName:
					value = child.firstChild.nodeValue.strip() 
					internal_vars[str(child.nodeName)] = str(value)
			return internal_vars
	

class ServerPlatformProperties(DynamicScalrObject):
	__title__ = 'ServerPlatformProperties'
	
	
class ServerInfo(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['server_id'] = 'ServerID'
	__titles__['platform'] = 'Platform'
	__titles__['remote_ip'] = 'RemoteIP'
	__titles__['local_ip'] = 'LocalIP'
	__titles__['status'] = 'Status'
	__titles__['index'] = 'Index'
	__titles__['added_at'] = 'AddedAt'
	
	
	server_id = None
	platform = None
	remote_ip = None
	local_ip = None
	status = None
	index = None	
	added_at = None	

'''
class ServerPlatformProperties(ScalrObject):
	
	__titles__ = OrderedDict()
	__titles__['instance_id'] = 'InstanceID'
	__titles__['owner_id'] = 'OwnerID'
	__titles__['imageid_ami'] = 'ImageIDAMI'
	__titles__['public_dns_name'] = 'PublicDNSname'
	__titles__['private_dns_name'] = 'PrivateDNSname'
	__titles__['public_ip'] = 'PublicIP'
	__titles__['private_ip'] = 'PrivateIP'
	__titles__['keyname'] = 'Keyname'
	__titles__['ami_launch_index'] = 'AMIlaunchindex'
	__titles__['instance_type'] = 'Instancetype'
	__titles__['launch_time'] = 'Launchtime'
	__titles__['architecture'] = 'Architecture'
	__titles__['root_device_type'] = 'Rootdevicetype'
	__titles__['instance_state'] = 'Instancestate'
	__titles__['placement'] = 'Placement'
	__titles__['security_groups'] = 'Securitygroups'	
	
	instance_id = None
	owner_id = None
	imageid_ami = None
	public_dns_name = None
	private_dns_name = None
	public_ip = None	
	private_ip = None	
	keyname = None
	ami_launch_index = None
	instance_type = None
	launch_time = None
	architecture = None
	root_device_type = None	
	instance_state = None	
	placement = None	
	security_groups = None	
'''

class FarmRole(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['farm_role_id'] = 'ID'
	__titles__['role_id'] = 'RoleID'
	__titles__['name'] = 'Name'
	__titles__['platform'] = 'Platform'
	__titles__['category'] = 'Category'
	__titles__['cloud_location'] = 'CloudLocation'
	
	__aliases__ = dict(ID = 'FarmRoleID')
	
	farm_role_id = None
	role_id = None
	name = None
	platform = None
	category = None
	cloud_location = None	
	
	
class FarmRoleProperties(ScalrObject):
	__titles__ = OrderedDict()	
	__titles__['farm_role_id'] = 'ID'
	__titles__['name'] = 'Name'
	__titles__['scaling_properties'] = 'ScalingProperties'
	__titles__['platform_properties'] = 'PlatformProperties'
	__titles__['mysql_properties'] = 'MySQLProperties'
	
	name = None
	farm_role_id = None	
	platform_properties = None
	mysql_properties = None
	scaling_properties = None
	servers = None
			
	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		
		servers = xml.getElementsByTagName('ServerSet')[0].childNodes
		if servers:
			kv['servers'] = [Server.fromxml(child) for child in servers]
			
		if kv and kv.has_key('mysql_properties'): 
			mp = kv['mysql_properties']
			if mp and mp.has_key('LastBackupTime'):
				mp['LastBackupTime'] = pretty_time(mp['LastBackupTime'])
				
		return cls(**kv)

		
class Server(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['external_ip'] = 'ExternalIP'
	__titles__['internal_ip'] = 'InternalIP'
	__titles__['server_id'] = 'ServerID'
	__titles__['name'] = 'Name'
	__titles__['farm_role_id'] = 'ID'
	__titles__['status'] = 'Status'
	__titles__['uptime'] = 'Uptime'
	__titles__['scalarizr_version'] = 'ScalarizrVersion'
	__titles__['platform_properties'] = 'PlatformProperties'
	
	server_id = None
	platform_properties = None
	external_ip = None
	internal_ip = None
	status = None
	scalarizr_version = None
	uptime = None
	
	name = None
	farm_role_id = None	
	
	__aliases__ = dict(ScalarizrVersion = 'Agent')

	@classmethod
	def parse_response(cls,xml):
		result = {}
		for key,tag in cls.__titles__.items():
			elements = xml.getElementsByTagName(tag)
			#print elements
			
			if not elements: 
				continue 
			
			parent_node = elements[0]
			if parent_node.hasChildNodes and parent_node.firstChild:
				
				#parent node has only one text child 
				if '#text' == parent_node.firstChild.nodeName:
					result[key] = parent_node.firstChild.nodeValue.strip() if parent_node else None
				
				#parent node has has many Items, each has one child with text child node	
				elif 'Item' == parent_node.firstChild.nodeName:
					vars = []
					for item in parent_node.childNodes:
						vars.append(item.firstChild.firstChild.nodeValue.strip())
					result[key] = vars
					
				#parent node has has many childs, each has one text child	
				else:
					internal_vars = {}
					for child in parent_node.childNodes:
						if child.hasChildNodes and child.firstChild and '#text'==child.firstChild.nodeName:
							value = child.firstChild.nodeValue.strip() 
							internal_vars[str(child.nodeName)] = str(value)
					result[key] = internal_vars
		return result	
	
	
class Source(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['type'] = 'Type'
	__titles__['url'] = 'URL'
	__titles__['auth_type'] = 'AuthType'
	
	id = None
	type = None
	url = None
	auth_type = None
	

class SourceID(ScalrObject):
	__titles__ = {'source_id' : 'SourceID'}
	source_id = None
	
	
class Application(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['name'] = 'Name'
	__titles__['source_id'] = 'SourceID'
	__titles__['pre_deploy_script'] = 'PreDeployScript'
	__titles__['post_deploy_script'] = 'PostDeployScript'
	
	id = None
	name = None
	source_id = None
	pre_deploy_script = None
	post_deploy_script = None

	
class ApplicationID(ScalrObject):
	__titles__ = {'app_id' : 'ApplicationID'}
	app_id = None
	

class DeploymentTask(ScalrObject):
	__titles__ = {'status' : 'DeploymentTaskStatus'}
	status = None


class DMTaskLog(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['time_stamp'] = 'Timestamp'
	__titles__['message'] = 'Message'

	id = None
	type = None
	time_stamp = None
	message = None

	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		kv['time_stamp'] = pretty_time(kv['time_stamp'])
		return DMTaskLog(**kv)	
	
class DeploymentTaskResult(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['server_id'] = 'ServerID'
	__titles__['task_id'] = 'DeploymentTaskID'
	__titles__['farm_role_id'] = 'FarmRoleID'
	__titles__['remote_path'] = 'RemotePath'
	__titles__['status'] = 'Status'
	__titles__['errmsg'] = 'ErrorMessage'
	
	task_id = None
	server_id = None
	farm_role_id = None
	remote_path = None
	status = None
	errmsg = None
	
class Result(ScalrObject):
	__titles__ = {'result' : 'Result'}
	result = None

	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		if kv['result'] == '1':
			kv['result'] = 'Success'
		return Result(**kv)	

class ServerID(ScalrObject):
	__titles__ = {'server_id' : 'ServerID'}
	server_id = None
	

class BundleTaskID(ScalrObject):
	__titles__ = {'bundle_task_id' : 'BundleTaskID'}
	bundle_task_id = None
	
	
class GraphURL(ScalrObject):
	__titles__ = {'graph_url' : 'GraphURL'}
	graph_url = None
	
	
class BundleTask(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['bundle_task_status'] = 'BundleTaskStatus'
	__titles__['failure_reason'] = 'FailureReason'
	
	bundle_task_status = None
	failure_reason = None


class ScriptRevision(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['revision'] = 'Revision'
	__titles__['date'] = 'Date'
	__titles__['config_variables'] = 'ConfigVariables'
	
	revision = None
	date = None
	config_variables = None
	
		
class LogRecord(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['server_id'] = 'ServerID'
	__titles__['message'] = 'Message'
	__titles__['severity'] = 'Severity'
	__titles__['time_stamp'] = 'Timestamp'
	__titles__['source'] = 'Source'
	
	server_id = None
	message = None
	severity = None
	time_stamp = None
	source = None
	
	_log_levels = {'1':'debug','2':'info','3':'warning','4':'error','5':'fatal'}
	
	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		kv['severity'] = cls._log_levels.get(kv['severity'],None)
		kv['time_stamp'] = pretty_time(kv['time_stamp'])
		return LogRecord(**kv)


class Event(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['type'] = 'Type'
	__titles__['time_stamp'] = 'Timestamp'
	__titles__['message'] = 'Message'

	id = None
	type = None
	time_stamp = None
	message = None
	
	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		kv['time_stamp'] = pretty_time(kv['time_stamp'])
		return Event(**kv)
		
			
class Role(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['name'] = 'Name'
	__titles__['owner'] = 'Owner'
	__titles__['architecture'] = 'Architecture'
	
	name = None
	owner = None
	architecture = None
	
	
class FarmStat(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['month'] = 'Month'
	__titles__['year'] = 'Year'
	__titles__['bandwidth_in'] = 'BandwidthIn'
	__titles__['bandwidth_out'] = 'BandwidthOut'
	__titles__['bandwidth_total'] = 'BandwidthTotal'
	
	month = None
	year = None
	bandwidth_in = None
	bandwidth_out = None
	bandwidth_total = None

	
class DnsZoneRecord(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['type'] = 'Type'
	__titles__['ttl'] = 'TTL'
	__titles__['priority'] = 'Priority'
	__titles__['name'] = 'Name'
	__titles__['value'] = 'Value'
	__titles__['weight'] = 'Weight'
	__titles__['port'] = 'Port'
	__titles__['is_system'] = 'IsSystem'
	
	id = None
	type = None
	ttl = None
	priority = None
	name = None
	value = None
	weight = None
	port = None
	is_system = None

		
class Farm(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['name'] = 'Name'
	__titles__['comments'] = 'Comments'
	__titles__['status'] = 'Status'
	
	id = None
	name = None
	comments = None
	status = None	

	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		kv['status'] = 'Running' if '1'==kv['status'] else 'Stopped'
		return cls(**kv)


class Script(ScalrObject): 
	__titles__ =  OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['name'] = 'Name'
	__titles__['description'] = 'Description'
	__titles__['latest_revision'] = 'LatestRevision'

	
	id = None
	name = None
	description = None
	latest_revision = None	
	
		
class DNSZone(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['zone_name'] = 'ZoneName'
	__titles__['farm_id'] = 'FarmID'
	__titles__['farm_role_id'] = 'FarmRoleID'
	__titles__['status'] = 'Status'
	__titles__['last_modified_at'] = 'LastModifiedAt'
	__titles__['ip_set'] = 'IpSet'
	
	zone_name = None
	farm_id = None
	farm_role_id = None
	status = None
	last_modified_at = None	
	ip_set = None	
		
		
class VirtualHost(ScalrObject):
	__titles__ = OrderedDict()

	__titles__['name'] = 'Name'
	__titles__['farm_id'] = 'FarmID'
	__titles__['farm_role_id'] = 'FarmRoleID'
	__titles__['is_ssl_enabled'] = 'IsSSLEnabled'
	__titles__['last_modified_at'] = 'LastModifiedAt'
	
	name = None
	farm_id = None
	farm_role_id = None
	is_ssl_enabled = None
	last_modified_at = None
	
	
class Environment(ScalrObject):
	__titles__ = OrderedDict()
	__titles__['id'] = 'ID'
	__titles__['name'] = 'Name'
	
	id = None
	name = None
	

def get_items_first_child(xml,tag): 
	elements = xml.getElementsByTagName(tag)
	return elements[0].firstChild if elements else None

def pretty_time(stamp):
	return time.strftime('%m.%d.%Y %X', time.gmtime(float(stamp)))
