'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

try:
	import timemodule as time
except ImportError:
	import time

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
							internal_vars[child.nodeName] = value
					result[key] = internal_vars
		return result


	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		return cls(**kv)


class FarmRole(ScalrObject):
	__titles__ = {
			'id' : 'ID',
			'role_id' : 'RoleID',
			'name' : 'Name',
			'platform' : 'Platform',
			'category' : 'Category',
			'cloud_location' : 'CloudLocation',
			'scaling_properties' : 'ScalingProperties',
			'platform_properties' : 'PlatformProperties',
			'mysql_properties' : 'MySQLProperties',
			'server_set' : 'ServerSet'
			}
	
	id = None
	role_id = None
	name = None
	platform = None
	category = None
	cloud_location = None	
	platform_properties = None
	mysql_properties = None
	scaling_properties = None
	server_set = None
	

	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		servers = xml.getElementsByTagName('ServerSet')[0].childNodes
		if servers:
			kv['server_set'] = [Server.fromxml(child) for child in servers]
		return cls(**kv)

	def __hash__(self):
		return hash(self.__dict__)
		
class Server(ScalrObject):
	__titles__ = {
			'server_id' : 'ServerID',
			'platform_properties' : 'PlatformProperties',
			'external_ip' : 'ExternalIP',
			'internal_ip' : 'InternalIP',
			'status' : 'Status',
			'scalarizr_version' : 'ScalarizrVersion',
			'uptime' : 'Uptime'}
	
	server_id = None
	platform_properties = None
	external_ip = None
	internal_ip = None
	status = None
	scalarizr_version = None
	uptime = None
	

class Result(ScalrObject):
	__titles__ = {'result' : 'Result'}
	result = None


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
	__titles__ = {
			'bundle_task_status' : 'BundleTaskStatus',
			'failure_reason':'FailureReason'}
	
	bundle_task_status = None
	failure_reason = None


class ScriptRevision(ScalrObject):
	__titles__ = {
		'revision' : 'Revision',
		'date' : 'Date',
		'config_variables' : 'ConfigVariables'
	}
	
	revision = None
	date = None
	config_variables = None
	
		
class LogRecord(ScalrObject):
	__titles__ = {
		'server_id' : 'ServerID', 
		'message' : 'Message',
		'severity' : 'Severity',
		'time_stamp' : 'Timestamp',
		'source' : 'Source'
	}
	
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
		kv['time_stamp'] = time.strftime('%m.%d.%Y %X', time.gmtime(float(kv['time_stamp'])))
		return LogRecord(**kv)


class Event(ScalrObject):
	__titles__ = {
		'id' : 'ID',
		'type' : 'Type',
		'time_stamp' : 'Timestamp',
		'message' : 'Message'
	}
	id = None
	type = None
	time_stamp = None
	message = None
	
	@classmethod
	def fromxml (cls, xml):	
		kv = cls.parse_response(xml)
		kv['time_stamp'] = time.strftime('%m.%d.%Y %X', time.gmtime(float(kv['time_stamp'])))
		return Event(**kv)
		
			
class Role(ScalrObject):
	__titles__ = {
		'name' : 'Name',
		'owner' : 'Owner',
		'architecture' : 'Architecture'
	}
	
	name = None
	owner = None
	architecture = None
	
	
class FarmStat(ScalrObject):
	__titles__ = {
		'month' : 'Month', 
		'year' : 'Year',
		'bandwidth_in' : 'BandwidthIn',
		'bandwidth_out' : 'BandwidthOut',
		'bandwidth_total' : 'BandwidthTotal',
	}
	
	month = None
	year = None
	bandwidth_in = None
	bandwidth_out = None
	bandwidth_total = None

	
class DnsZoneRecord(ScalrObject):
	__titles__ = {
		'id' : 'ID',
		'type' : 'Type',
		'ttl' : 'TTL',
		'priority' : 'Priority',
		'name' : 'Name',
		'value' : 'Value',
		'weight' : 'Weight',
		'port' : 'Port',
		'is_system' : 'IsSystem'
	}
	
	__data__ = None
	
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
	__titles__ = {
		'id' : 'ID',
		'name' : 'Name',
		'comments' : 'Comments',
		'status' : 'Status'
	}
	
	id = None
	name = None
	comments = None
	status = None	


class Script(ScalrObject): 
	__titles__ = {
		'id' : 'ID',
		'name' : 'Name',
		'description' : 'Description',
		'latest_revision' : 'LatestRevision'
	}
	
	id = None
	name = None
	description = None
	latest_revision = None	
	
		
class DNSZone(ScalrObject):
	__titles__ = {
		'zone_name' : 'ZoneName',
		'farm_id' : 'FarmID',
		'farm_role_id' : 'FarmRoleID',
		'status' : 'Status',
		'last_modified_at' : 'LastModifiedAt',
		'ip_set' : 'IpSet'
	}
	
	zone_name = None
	farm_id = None
	farm_role_id = None
	status = None
	last_modified_at = None	
	ip_set = None	
		
		
class VirtualHost(ScalrObject):
	__titles__ = {
		'name' : 'Name',
		'farm_id' : 'FarmID',
		'farm_role_id' : 'FarmRoleID',
		'is_ssl_enabled' : 'IsSSLEnabled',
		'last_modified_at' : 'LastModifiedAt'
	}
	
	name = None
	farm_id = None
	farm_role_id = None
	is_ssl_enabled = None
	last_modified_at = None
	

def get_items_first_child(xml,tag): 
	elements = xml.getElementsByTagName(tag)
	return elements[0].firstChild if elements else None

#TODO: make __titles__ OrderedDict and check right order 