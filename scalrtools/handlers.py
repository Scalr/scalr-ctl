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
		conn = config.get_connection()	
		try:
			print TableViewer(conn.apache_virtual_hosts_list())
		except ScalrAPIError, e:
			print e
			sys.exit()


class DNSZonesList(BaseHandler):
	subcommand = 'dns_zones_list'

	def __init__(self, config, *args):
		pass			


class DNSZoneRecordsList(BaseHandler):
	subcommand = 'dns_zone_record_list'

	def __init__(self, config, *args):
		pass			


class EventsList(BaseHandler):
	subcommand = 'events_list'

	def __init__(self, config, *args):
		pass			


class FarmsList(BaseHandler):
	subcommand = 'farms_list'

	def __init__(self, config, *args):
		pass			


class LogsList(BaseHandler):
	subcommand = 'logs_list'

	def __init__(self, config, *args):
		pass			


class RolesList(BaseHandler):
	subcommand = 'roles_list'

	def __init__(self, config, *args):
		pass			


class ScriptsList(BaseHandler):
	subcommand = 'scripts_list'

	def __init__(self, config, *args):
		pass			


class ScriptGetDetails(BaseHandler):
	subcommand = 'get_script_details'

	def __init__(self, config, *args):
		pass			


class BundleTaskGetStatus(BaseHandler):
	subcommand = 'get_bundle_task_status'

	def __init__(self, config, *args):
		pass	
			

class FarmGetDetails(BaseHandler):
	subcommand = 'get_farm_details'

	def __init__(self, config, *args):
		pass			


class FarmGetStats(BaseHandler):
	subcommand = 'get_farm_stats'

	def __init__(self, config, *args):
		pass			


class StatisticsGetGraphURL(BaseHandler):
	subcommand = 'get_statistics_graph_URL'

	def __init__(self, config, *args):
		pass			


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
	subcommand = 'terminate_farm'

	def __init__(self, config, *args):
		pass			


class DNSZoneRecordAdd(BaseHandler):
	subcommand = 'add_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class DNSZoneRecordRemove(BaseHandler):
	subcommand = 'remove_dns_zone_record'

	def __init__(self, config, *args):
		pass			


class ScriptExecute(BaseHandler):
	subcommand = 'execute_script'

	def __init__(self, config, *args):
		pass			


class ServerReboot(BaseHandler):
	subcommand = 'reboot_server'

	def __init__(self, config, *args):
		pass	
