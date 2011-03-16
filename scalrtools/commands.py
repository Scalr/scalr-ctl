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
from api.view import TableViewer


class Command(object):
	name = None
	config = None
	help = None
		
	def __init__(self, config, *args):
		self.config = config
		self.parser = OptionParser(usage=self.help)
		self.inject_options(self.parser)
		self.options = self.parser.parse_args(list(args))[0]
		
	def run(self):
		pass
	
	def inject_options(self, parser):
		pass
	
	def validate_options(self):
		pass
	
	def api_call(self, callback, *args, **kwargs):
		try:
			return TableViewer(callback(*args, **kwargs))
		except ScalrAPIError, e:
			return e
			sys.exit()
			
	def require(self, *args):
		if not all(args):
			print self.parser.format_help()
			sys.exit()

class ApacheVhostsList(Command):
	name = 'list-apache-virtual-hosts'
	
	def run(self):
		print self.api_call(self.config.get_connection().list_apache_virtual_hosts)


class DNSZonesList(Command):
	name = 'list-dns-zones'
	
	def run(self):
		print self.api_call(self.config.get_connection().list_dns_zones)


class FarmsList(Command):
	name = 'list-farms'

	def run(self):
		print self.api_call(self.config.get_connection().list_farms)
		

class ScriptsList(Command):
	name = 'list-scripts'
	
	def run(self):
		print self.api_call(self.config.get_connection().list_scripts)
		
		
class DNSZoneRecordsList(Command):
	name = 'list-dns-zone-records'

	def __init__(self, config, *args):
		super(DNSZoneRecordsList, self).__init__(config, *args)
		self.require(self.options.name)

	def inject_options(self, parser):
		parser.add_option("-n", "--zone-name", dest="name", default=None, help="Zone (Domain) name")
	
	def run(self):
		print self.api_call(self.config.get_connection().list_dns_zone_records, self.options.name)


class EventsList(Command):
	name = 'list-events'

	def __init__(self, config, *args):
		super(EventsList, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.id, self.options.start, self.options.limit)
		print self.api_call(self.config.get_connection().list_events, *args)


class LogsList(Command):
	name = 'list-logs'
	def __init__(self, config, *args):
		super(LogsList, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help="Instance ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.id, self.options.server_id, self.options.start, self.options.limit)
		print self.api_call(self.config.get_connection().list_logs, *args)


class RolesList(Command):
	name = 'list-roles'

	def inject_options(self, parser):
		parser.add_option("-p", "--platform", dest="platform", default=None, help="Cloud platform")
		parser.add_option("-n", "--name", dest="name", default=None, help="List roles with specified role name.")
		parser.add_option("-x", "--prefix", dest="prefix", default=None, help="List all roles begins with specified prefix.")
		parser.add_option("-i", "--image-id", dest="image_id", default=None, help="List roles with specified image id.")
	
	def run(self):
		args = (self.options.platform, self.options.name, self.options.prefix, self.options.image_id)
		print self.api_call(self.config.get_connection().list_roles, *args)


class ScriptGetDetails(Command):
	name = 'get-script-details'

	def __init__(self, config, *args):
		super(ScriptGetDetails, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-s", "--script-id", dest="id", default=None, help="Script ID")
	
	def run(self):
		print self.api_call(self.config.get_connection().get_script_details, self.options.id)
		

class BundleTaskGetStatus(Command):
	name = 'get-bundle-task-status'
	
	def __init__(self, config, *args):
		super(BundleTaskGetStatus, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-i", "--bundle-task-id", dest="id", default=None, help="ID of the bundle task")
	
	def run(self):
		print self.api_call(self.config.get_connection().get_bundle_task_status, self.options.id)
		

class FarmGetDetails(Command):
	name = 'get-farm-details'

	def __init__(self, config, *args):
		super(FarmGetDetails, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
	
	def run(self):
		print self.api_call(self.config.get_connection().get_farm_details, self.options.id)	


class FarmGetStats(Command):
	name = 'get-farm-stats'

	def __init__(self, config, *args):
		super(FarmGetStats, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-d", "--date", dest="date", default=None, help="Date (mm-yyyy)")
	
	def run(self):
		print self.api_call(self.config.get_connection().get_farm_stats, self.options.id,self.options.date)	
		

class StatisticsGetGraphURL(Command):
	name = 'get-statistics-graph-url'

	def __init__(self, config, *args):
		super(StatisticsGetGraphURL, self).__init__(config, *args)
		self.require(self.options.obj_type, self.options.id, self.options.name, self.options.graph_type)

	def inject_options(self, parser):		
		id_help = "In case if object type is instance ObjectID shoudl be server id, in case if object type is role ObjectID should be role id \
		and in case if object type is farm ObjectID should be farm id"
		parser.add_option("-o", "--object-type", dest="obj_type", default=None, help="Object type. Valid values are: role, server or farm")
		parser.add_option("-i", "--object-id", dest="id", default=None, help=id_help)
		parser.add_option("-n", "--watcher-name", dest="name", default=None, help="Watcher name could be CPU, NET, MEM or LA")
		parser.add_option("-g", "--graph-type", dest="graph_type", default=None, help="Graph type could be daily, weekly, monthly or yearly")
	
	def run(self):
		args = (self.options.obj_type, self.options.id, self.options.name, self.options.graph_type)
		print self.api_call(self.config.get_connection().get_statistics_graph_URL, *args)	
		

class FarmTerminate(Command):
	name = 'terminate-farm'

	def __init__(self, config, *args):
		super(FarmTerminate, self).__init__(config, *args)
		self.require(self.options.id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)

	def inject_options(self, parser):		
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="The ID of farm that you want to terminate")
		parser.add_option("-e", "--keep-ebs", dest="keep_ebs", default=None, help="Keep EBS volumes created for roles on this farm")
		parser.add_option("-i", "--keep-eip", dest="keep_eip", default=None, help='Keep Elastic IPs created for roles on this farm')
		parser.add_option("-d", "--keep-dns-zone", dest="keep_dns_zone", default=None, help="Keep DNS zone that assigned to this farm on nameservers")
	
	def run(self):
		args = (self.options.id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)
		print self.api_call(self.config.get_connection().terminate_farm, *args)	
		
		
class ScriptExecute(Command):
	name = 'execute-script'

	def __init__(self, config, *args):
		super(ScriptExecute, self).__init__(config, *args)
		self.require(self.options.farm_id, self.options.script_id, self.options.async, self.options.timeout)

	def inject_options(self, parser):		
		id_help = "Script will be executed on all instances with this farm role ID. You can get this ID by using GetFarmDetails API call"
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help=id_help)
		parser.add_option("-s", "--server-id", dest="server_id", default=None, help="Script will be executed on this server")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Execute script on specified farm")
		parser.add_option("-e", "--script-id", dest="script_id", default=None, help="Script ID")
		parser.add_option("-t", "--timeout", dest="timeout", default=None, help="Script execution timeout (seconds)")
		parser.add_option("-a", "--async", dest="async", default=None, help="Excute script asynchronously (1) or synchronously (0)")
		parser.add_option("-r", "--revision", dest="revision", default=None, help="Execute specified revision of script")
		parser.add_option("-v", "--variables", dest="variables", default=None, help="Script variables")
	
	def run(self):
		args = (self.options.farm_id, self.options.script_id, self.options.timeout \
					, self.options.async, self.options.farm_role_id, self.options.server_id, self.options.revision, self.options.variables)
		print self.api_call(self.config.get_connection().execute_script, *args)	


class ServerReboot(Command):
	name = 'reboot-server'

	def __init__(self, config, *args):
		super(ServerReboot, self).__init__(config, *args)
		self.require(self.options.id)

	def inject_options(self, parser):
		parser.add_option("-s", "--server-id", dest="id", default=None, help="Server ID")
	
	def run(self):
		print self.api_call(self.config.get_connection().reboot_server, self.options.id)	
		
	
class ConfigureEnv(Command):
	name = 'configure-env'
	help = 'scalrtools configure-env -a key_id -s key -u api_url'
		
	def __init__(self, config, *args):
		super(ConfigureEnv, self).__init__(config, *args)
		self.require(self.options.key_id, self.options.key, self.options.api_url)
			
	def inject_options(self, parser):
		parser.add_option("-a", "--access-key", dest="key_id", default=None, help="Access key")
		parser.add_option("-s", "--secret-key", dest="key", default=None, help="Secret key")
		parser.add_option("-u", "--api-url", dest="api_url", default=None, help="API URL")
		
	def run(self):		
		e = Environment(url=self.options.api_url,
				key_id=self.options.key_id,
				key=self.options.key,
				api_version = '2.2.0')
		
		e.write(self.config.base_path)
		
		e = Environment.from_ini(self.config.base_path)
		print 'URL:%s\nkey_id:%s\nkey:%s\napi_version:%s' % (e.url, e.key_id, e.key, e.api_version)
		
		
class ConfigureRepo(Command):
	name = 'configure-repo'
	help = 'scalrtools configure-repo -n name -t svn|git -u repo_url -l login -p password'
	
	def __init__(self, config, *args):
		super(ConfigureRepo, self).__init__(config, *args)
		self.require(self.options.type, self.options.login, self.options.password, self.options.url, self.options.name)
		
	def inject_options(self, parser):		
		parser.add_option("-t", "--type", dest="type", default=None, help="SVN or GIT")
		parser.add_option("-u", "--url", dest="url", default=None, help="Repository URL")
		parser.add_option("-l", "--login", dest="login", default=None, help="Repository username")
		parser.add_option("-p", "--password", dest="password", default=None, help="Repository password")
		parser.add_option("-n", "--name", dest="name", default=None, help="Repository name")
		
	def run(self):		
		r = Repository(name = self.options.name,
				url = self.options.url,
				type = self.options.type,
				login = self.options.login,
				password = self.options.password)
		
		r.write(self.config.base_path, self.options.name)
		
		r = Repository.from_ini(self.config.base_path, self.options.name)
		print 'Name:%s\nType:%s\nURL:%s\nLogin:%s\nPassword:%s\n' % (r.name, r.type, r.url, r.login, r.password)
		
		
class ConfigureApp(Command):
	name = 'configure-app'
	help = 'scalrtools configure-app -n name -r repo-name -i farm-role-id -f farm-id -p remote-path'
	
	def __init__(self, config, *args):
		super(ConfigureApp, self).__init__(config, *args)
		self.require(self.options.name, self.options.repo_name, self.options.farm_id, self.options.farm_role_id, self.options.remote_path)
		
	def inject_options(self, parser):
		parser.add_option("-n", "--name", dest="name", default=None, help="Application name")
		parser.add_option("-r", "--repo", dest="repo_name", default=None, help="Repository name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="FarmID")
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help="FarmRoleID")
		parser.add_option("-p", "--remote-path", dest="remote_path", default=None, help="Path on remote server where to deploy application")

	def run(self):		
		a = Application(name = self.options.name,
				repo_name = self.options.repo_name,
				farm_id = self.options.farm_id,
				farm_role_id = self.options.farm_role_id,
				remote_path = self.options.remote_path)
		
		a.write(self.config.base_path, self.options.name)
		
		a = Application.from_ini(self.config.base_path, self.options.name)
		print 'Name:%s\nRepo:%s\nFarmID:%s\nFarmRoleID:%s\nRemotePath:%s\n' % (a.name, a.repo_name, a.farm_id, a.farm_role_id, a.remote_path)
		
		
class AppsList(Command):
	name = 'list-apps'
	help = 'scalrtools list-apps'
	
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
			
			
class ReposList(Command):
	name = 'list-repos'
	help = 'scalrtools list-repos'
	
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



class DNSZoneRecordAdd(Command):
	name = 'add_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class DNSZoneRecordRemove(Command):
	name = 'remove_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class DNSZoneCreate(Command):
	name = 'create_dns_zone'

	def __init__(self, config, *args):
		pass			


class ApacheVhostCreate(Command):
	name = 'create_apache_vhost'

	def __init__(self, config, *args):
		pass			


class ServerImageCreate(Command):
	name = 'create_server_image'

	def __init__(self, config, *args):
		pass		
	

class ServerLaunch(Command):
	name = 'launch_server'

	def __init__(self, config, *args):
		pass			


class FarmLaunch(Command):
	name = 'launch_farm'

	def __init__(self, config, *args):
		pass			


class ServerTerminate(Command):
	name = 'terminate_server'

	def __init__(self, config, *args):
		pass			
		
			
class Deploy(Command):
	name = 'deploy'

	def __init__(self, config, *args):
		pass
	