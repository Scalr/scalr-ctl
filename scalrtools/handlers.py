'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os
import sys

from ConfigParser import ConfigParser
from optparse import OptionParser

from prettytable import PrettyTable	

from config import Environment, Repository, Application
from api import ScalrAPIError
from view import TableViewer

class BaseHandler:
	subcommand = None
	config = None
	help = None
		
	def __init__(self, config, *args):
		pass
	
	def run(self):
		pass
	
	
class ConfigureEnv(BaseHandler):
	subcommand = 'configure-env'
	help = 'scalrtools configure-env -a key_id -s key -u api_url'
		
	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-a", "--access-key", dest="key_id", default=None, help="Access key")
		parser.add_option("-s", "--secret-key", dest="key", default=None, help="Secret key")
		parser.add_option("-u", "--api-url", dest="api_url", default=None, help="API URL")
		
		self.options = parser.parse_args(list(args))[0]
		
		if not(self.options.key_id and self.options.key and self.options.api_url):
			print parser.format_help()
			sys.exit()
		
		self.config = config
	
	def run(self):		
		e = Environment(url=self.options.api_url,
				key_id=self.options.key_id,
				key=self.options.key,
				api_version = '2.2.0')
		
		e.write(self.config.base_path)
		
		e = Environment.from_ini(self.config.base_path)
		print 'URL:%s\nkey_id:%s\nkey:%s\napi_version:%s' % (e.url, e.key_id, e.key, e.api_version)
		
		
class ConfigureRepo(BaseHandler):
	subcommand = 'configure-repo'
	help = 'scalrtools configure-repo -n name -t svn|git -u repo_url -l login -p password'
	
	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-t", "--type", dest="type", default=None, help="SVN or GIT")
		parser.add_option("-u", "--url", dest="url", default=None, help="Repository URL")
		parser.add_option("-l", "--login", dest="login", default=None, help="Repository username")
		parser.add_option("-p", "--password", dest="password", default=None, help="Repository password")
		parser.add_option("-n", "--name", dest="name", default=None, help="Repository name")
		
		self.options = parser.parse_args(list(args))[0]
		
		if not(self.options.type and self.options.login and self.options.password and self.options.url and self.options.name):
			print parser.format_help()
			sys.exit()
				
		self.config = config
		
	def run(self):		
		r = Repository(name = self.options.name,
				url = self.options.url,
				type = self.options.type,
				login = self.options.login,
				password = self.options.password)
		
		r.write(self.config.base_path, self.options.name)
		
		r = Repository.from_ini(self.config.base_path, self.options.name)
		print 'Name:%s\nType:%s\nURL:%s\nLogin:%s\nPassword:%s\n' % (r.name, r.type, r.url, r.login, r.password)
		
		
class ConfigureApp(BaseHandler):
	subcommand = 'configure-app'
	help = 'scalrtools configure-app -n name -r repo-name -i farm-role-id -f farm-id -p remote-path'
	
	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-n", "--name", dest="name", default=None, help="Application name")
		parser.add_option("-r", "--repo", dest="repo_name", default=None, help="Repository name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="FarmID")
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help="FarmRoleID")
		parser.add_option("-p", "--remote-path", dest="remote_path", default=None, help="Path on remote server where to deploy application")
		
		self.options = parser.parse_args(list(args))[0]
		
		if not(self.options.name and self.options.repo_name and self.options.farm_id and self.options.farm_role_id and self.options.remote_path):
			print parser.format_help()
			sys.exit()
			
		self.config = config

	def run(self):		
		a = Application(name = self.options.name,
				repo_name = self.options.repo_name,
				farm_id = self.options.farm_id,
				farm_role_id = self.options.farm_role_id,
				remote_path = self.options.remote_path)
		
		a.write(self.config.base_path, self.options.name)
		
		a = Application.from_ini(self.config.base_path, self.options.name)
		print 'Name:%s\nRepo:%s\nFarmID:%s\nFarmRoleID:%s\nRemotePath:%s\n' % (a.name, a.repo_name, a.farm_id, a.farm_role_id, a.remote_path)
		
		
class AppsList(BaseHandler):
	subcommand = 'list-apps'
	help = 'scalrtools list-apps'
	
	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):	
		config = ConfigParser()
		path = os.path.join(self.config.base_path, Application.config_name)
		config.read(path)
		#TODO: fill column names automatically 
		column_names = ['name', 'repo_name', 'farm_id', 'farm_role_id', 'remote_path']
		pt = PrettyTable(column_names, caching=False)
		for app_name in config.sections():
			a = Application.from_ini(self.config.base_path, app_name)
			row = [a.name, a.repo_name, a.farm_id, a.farm_role_id, a.remote_path]
			pt.add_row(row)
		print str(pt)
			
			
class ReposList(BaseHandler):
	subcommand = 'list-repos'
	help = 'scalrtools list-repos'
	
	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):	
		config = ConfigParser()
		path = os.path.join(self.config.base_path, Repository.config_name)
		config.read(path)
		column_names = ['name', 'type', 'url', 'login', 'password']
		pt = PrettyTable(column_names, caching=False)
		for repo_name in config.sections():
			a = Repository.from_ini(self.config.base_path, repo_name)
			row = [a.name, a.type, a.url, a.login, a.password]
			pt.add_row(row)
		print str(pt)
			

class Deploy(BaseHandler):
	subcommand = 'deploy'

	def __init__(self, config, *args):
		pass
			

class DNSZoneCreate(BaseHandler):
	subcommand = 'create_dns_zone'

	def __init__(self, config, *args):
		pass			


class ApacheVhostCreate(BaseHandler):
	subcommand = 'create_apache_vhost'

	def __init__(self, config, *args):
		pass			


class ServerImageCreate(BaseHandler):
	subcommand = 'create_server_image'

	def __init__(self, config, *args):
		pass			


class ApacheVhostsList(BaseHandler):
	subcommand = 'apache-virtual-host-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.apache_virtual_hosts_list())
		except ScalrAPIError, e:
			print e
			sys.exit()


class DNSZonesList(BaseHandler):
	subcommand = 'dns-zones-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.dns_zones_list())
		except ScalrAPIError, e:
			print e
			sys.exit()	


class DNSZoneRecordsList(BaseHandler):
	subcommand = 'dns-zone-records-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-n", "--zone-name", dest="name", default=None, help="Zone (Domain) name")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.name:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.dns_zone_records_list(self.options.name))
		except ScalrAPIError, e:
			print e
			sys.exit()			


class EventsList(BaseHandler):
	subcommand = 'events-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.events_list(self.options.id, self.options.start, self.options.limit))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class FarmsList(BaseHandler):
	subcommand = 'farms-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.farms_list())
		except ScalrAPIError, e:
			print e
			sys.exit()			


class LogsList(BaseHandler):
	subcommand = 'logs-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help="Instance ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.logs_list(self.options.id, self.options.server_id, self.options.start, self.options.limit))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class RolesList(BaseHandler):
	subcommand = 'roles-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-p", "--platform", dest="platform", default=None, help="Cloud platform")
		parser.add_option("-n", "--name", dest="name", default=None, help="List roles with specified role name.")
		parser.add_option("-x", "--prefix", dest="prefix", default=None, help="List all roles begins with specified prefix.")
		parser.add_option("-i", "--image-id", dest="image_id", default=None, help="List roles with specified image id.")
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.roles_list(self.options.platform, self.options.name, self.options.prefix, self.options.image_id))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class ScriptsList(BaseHandler):
	subcommand = 'scripts-list'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		self.options = parser.parse_args(list(args))[0]
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.scripts_list())
		except ScalrAPIError, e:
			print e
			sys.exit()		


class ScriptGetDetails(BaseHandler):
	subcommand = 'get-script-details'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-s", "--script-id", dest="id", default=None, help="Script ID")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.get_script_details(self.options.id))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class BundleTaskGetStatus(BaseHandler):
	subcommand = 'get-bundle-task-status'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-i", "--bundle-task-id", dest="id", default=None, help="ID of the bundle task")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.get_bundle_task_status(self.options.id))
		except ScalrAPIError, e:
			print e
			sys.exit()	
			

class FarmGetDetails(BaseHandler):
	subcommand = 'get-farm-details'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.get_farm_details(self.options.id))
		except ScalrAPIError, e:
			print e
			sys.exit()		


class FarmGetStats(BaseHandler):
	subcommand = 'get-farm-stats'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-d", "--date", dest="date", default=None, help="Date (mm-yyyy)")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.get_farm_stats(self.options.id,self.options.date))
		except ScalrAPIError, e:
			print e
			sys.exit()			


class StatisticsGetGraphURL(BaseHandler):
	subcommand = 'get-statistics-graph-url'

	def __init__(self, config, *args):
		id_help = "In case if object type is instance ObjectID shoudl be server id, in case if object type is role ObjectID should be role id \
		and in case if object type is farm ObjectID should be farm id"
		parser = OptionParser(usage=self.help)
		parser.add_option("-o", "--object-type", dest="obj_type", default=None, help="Object type. Valid values are: role, server or farm")
		parser.add_option("-i", "--object-id", dest="id", default=None, help=id_help)
		parser.add_option("-n", "--watcher-name", dest="name", default=None, help="Watcher name could be CPU, NET, MEM or LA")
		parser.add_option("-g", "--graph-type", dest="graph_type", default=None, help="Graph type could be daily, weekly, monthly or yearly")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id or not self.options.obj_type or not self.options.name or not self.options.graph_type:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.get_statistics_graph_URL(self.options.obj_type, self.options.id, self.options.name, self.options.graph_type))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class ServerLaunch(BaseHandler):
	subcommand = 'launch_server'

	def __init__(self, config, *args):
		pass			


class FarmLaunch(BaseHandler):
	subcommand = 'launch_farm'

	def __init__(self, config, *args):
		pass			


class ServerTerminate(BaseHandler):
	subcommand = 'terminate_server'

	def __init__(self, config, *args):
		pass			


class FarmTerminate(BaseHandler):
	subcommand = 'terminate-farm'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="The ID of farm that you want to terminate")
		parser.add_option("-e", "--keep-ebs", dest="keep_ebs", default=None, help="Keep EBS volumes created for roles on this farm")
		parser.add_option("-i", "--keep-eip", dest="keep_eip", default=None, help='Keep Elastic IPs created for roles on this farm')
		parser.add_option("-d", "--keep-dns-zone", dest="keep_dns_zone", default=None, help="Keep DNS zone that assigned to this farm on nameservers")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id or not self.options.keep_ebs or not self.options.keep_eip or not self.options.keep_dns_zone:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.terminate_farm(self.options.id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone))
		except ScalrAPIError, e:
			print e
			sys.exit()			


class DNSZoneRecordAdd(BaseHandler):
	subcommand = 'add_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class DNSZoneRecordRemove(BaseHandler):
	subcommand = 'remove_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class ScriptExecute(BaseHandler):
	subcommand = 'execute-script'

	def __init__(self, config, *args):
		id_help = "Script will be executed on all instances with this farm role ID. You can get this ID by using GetFarmDetails API call"
		parser = OptionParser(usage=self.help)
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help=id_help)
		parser.add_option("-s", "--server-id", dest="server_id", default=None, help="Script will be executed on this server")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Execute script on specified farm")
		parser.add_option("-e", "--script-id", dest="script_id", default=None, help="Script ID")
		parser.add_option("-t", "--timeout", dest="timeout", default=None, help="Script execution timeout (seconds)")
		parser.add_option("-a", "--async", dest="async", default=None, help="Excute script asynchronously (1) or synchronously (0)")
		parser.add_option("-r", "--revision", dest="revision", default=None, help="Execute specified revision of script")
		parser.add_option("-v", "--variables", dest="variables", default=None, help="Script variables")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.farm_id or not self.options.script_id or not self.options.async or not self.options.timeout:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.execute_script(self.options.farm_id, self.options.script_id, self.options.timeout \
					, self.options.async, self.options.farm_role_id, self.options.server_id, self.options.revision, self.options.variables))
		except ScalrAPIError, e:
			print e
			sys.exit()				


class ServerReboot(BaseHandler):
	subcommand = 'reboot-server'

	def __init__(self, config, *args):
		parser = OptionParser(usage=self.help)
		parser.add_option("-s", "--server-id", dest="id", default=None, help="Server ID")
		self.options = parser.parse_args(list(args))[0]
		
		if not self.options.id:
			print parser.format_help()
			sys.exit()
			
		self.config = config
	
	def run(self):
		conn = self.config.get_connection()	
		try:
			print TableViewer(conn.reboot_server(self.options.id))
		except ScalrAPIError, e:
			print e
			sys.exit()	
