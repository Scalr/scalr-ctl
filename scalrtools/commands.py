'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os
import sys
import time 
import threading 

from ConfigParser import ConfigParser
from optparse import OptionParser, TitledHelpFormatter
from shutil import copyfile

from config import Environment
from api import ScalrConnection, ScalrAPIError
from api.view import TableViewer

progname = 'scalr'
DEFAULT_API_URL = 'https://api.scalr.net'

class ScalrError(BaseException):
	pass

class Command(object):
	name = ''
	help = ''
	
	config = None
	parser = None
	options = None
		
	def __init__(self, config, *args):
		self.config = config
		self.parser = OptionParser(usage='%s %s %s' % (progname, self.name, self.help))
		self.inject_options(self.parser)
		self.options = self.parser.parse_args(list(args))[0]
		
		#Allowing user to use name instead of id if possible
		if hasattr(self.options, 'farm_id') and not self.options.farm_id and self.options.farm_name:
			self.options.farm_id = self.connection.get_farm_id(self.options.farm_name)
			
			if not self.options.farm_id:
				raise ScalrError("Farm '%s' not found" % self.options.farm_name)
			
		if hasattr(self.options, 'farm_name') and not self.options.farm_name:
			self.options.farm_name = self.connection.get_farm_name(self.options.farm_id)
			
	def run(self):
		pass
	
	def call_api_method(self, callback, *args, **kwargs):
		try:
			return callback(*args, **kwargs)
		except ScalrAPIError, e:
			print e
			sys.exit()	
	
	def pretty(self, callback, *args, **kwargs):
		try:
			return TableViewer(callback(*args, **kwargs))
		except ScalrAPIError, e:
			return e
			sys.exit()
			
	def require(self, *args):
		if not all(args):
			print self.parser.format_help(TitledHelpFormatter())
			sys.exit()
	
	@classmethod
	def inject_options(cls, parser):
		pass	
		
	@classmethod
	def usage(cls):
		parser = OptionParser(usage='%s %s %s' % (progname, cls.name, cls.help)) 
		cls.inject_options(parser)
		return parser.format_help(TitledHelpFormatter())

	@property		
	def connection(self):
		conn = None
		#print 'self.config.environment.api_version', self.config.environment.api_version
		if self.config.environment:
			conn = ScalrConnection(self.config.environment.url, 
					self.config.environment.key_id, 
					self.config.environment.key, 
					env_id=self.config.environment.env_id,
					api_version=self.config.environment.api_version, 
					logger=self.config.logger)
		return conn

		
class ApacheVhostsList(Command):
	name = 'list-apache-virtual-hosts'
	
	def run(self):
		print self.pretty(self.connection.list_apache_virtual_hosts)


class DmCreateSource(Command):
	name = 'dm-create-source'
	help = '-t [http|svn] -u url [-l login -p password]'

	def __init__(self, config, *args):
		super(DmCreateSource, self).__init__(config, *args)
		self.require(self.options.type, self.options.url)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-t", "--type", dest="type", help="Source type [svn|http]")
		parser.add_option("-u", "--url", dest="url", help="Source URL")
		parser.add_option("-l", "--login", dest="auth_login", default=None, help="Source login")
		parser.add_option("-p", "--password", dest="auth_password", default=None, help="Source password")
	
	def run(self):
		args = (self.options.type, self.options.url, self.options.auth_login, self.options.auth_password)
		print self.pretty(self.connection.dm_create_source, *args)


class DmCreateApplication(Command):
	name = 'dm-create-application'
	help = '-n name -s source-id [-b pre_deploy_script -a post_deploy_script]'

	def __init__(self, config, *args):
		super(DmCreateApplication, self).__init__(config, *args)
		self.require(self.options.name, self.options.source_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--name", dest="name", help="Application name")
		parser.add_option("-s", "--source-id", dest="source_id", help="Source ID")
		parser.add_option("-b", "--pre-deploy script", dest="pre_deploy_script", default=None, help="Script to execute BEFORE deploy")
		parser.add_option("-a", "--post-deploy script", dest="post_deploy_script", default=None, help="Script to execute AFTER deploy")
	
	def run(self):
		args = (self.options.name, self.options.source_id, self.options.pre_deploy_script, self.options.post_deploy_script)
		print self.pretty(self.connection.dm_create_application, *args)
		

class DmDeployApplication(Command):
	name = 'dm-deploy-application'
	help = '{-a app-id | -n app-name} -r farm-role-id -p remote-path [--non-interactive]'

	test_url = 'https://scalr-test-deploy.googlecode.com/svn/trunk' 
	test_app = 'ScalrDemoApp'
	test_type = 'svn'
	def __init__(self, config, *args):
		
		super(DmDeployApplication, self).__init__(config, *args)
		if self.options.app_name == self.test_app:
			self.require(self.options.app_id or self.options.app_name, self.options.farm_role_id)
		else:
			self.require(self.options.app_id or self.options.app_name, self.options.farm_role_id, self.options.remote_path)

	@classmethod
	def inject_options(cls, parser):
		app_name_help = "The name of application could be used INSTEAD of ID. Use name %s to test deployment process on your role." % cls.test_app
		parser.add_option("-n", "--app-name", dest="app_name", default=None, help=app_name_help)
		parser.add_option("-a", "--app-id", dest="app_id", help="Application ID")
		parser.add_option("-r", "--farm-role-id", dest="farm_role_id", help="FarmRole ID")
		parser.add_option("-p", "--remote-path", dest="remote_path", default='/var/www/', help="Remote path where to deploy the app. Default is /var/www/")
		parser.add_option("--non-interactive", dest="non_interactive", action="store_true", help="Use this option to avoid checking farm state")
	
	def run(self):
		self.options.app_id = self.options.app_id or self.connection.get_application_id(self.options.app_name)
		self.options.app_name = self.options.app_name or self.connection.get_application_name(self.options.app_id)
		
		if self.options.app_name == self.test_app:
			self.options.app_name = self.test_app
			
			#check sources
			sources = [source for source in self.connection.dm_list_sources() if source.url==self.test_url]
			if sources:
				sid = sources[0].id
			else:
				result = self.call_api_method(self.connection.dm_create_source,self.test_type, self.test_url, None, None)
				print TableViewer(result)
				sid = result[0].source_id
	
			#check apps
			apps = [app for app in self.connection.dm_list_applications() if app.source_id==sid]
			if apps:
				self.options.app_id = apps[0].id
			else:
				result = self.call_api_method(self.connection.dm_create_application,self.options.app_name, sid, None, None)
				print TableViewer(result)
				self.options.app_id = result[0].app_id

		#deploy
		args = (self.options.app_id, self.options.farm_role_id, self.options.remote_path)
		tasks = self.call_api_method(self.connection.dm_deploy_application, *args)
		print TableViewer(tasks)
							
		#check task status in loop
		if not self.options.non_interactive and not isinstance(tasks,ScalrAPIError) and tasks:
			for task in tasks:
				
				print 'Deploying %s on server %s (DeploymentTaskID: %s)' % (self.options.app_name, task.server_id, task.task_id)
				
				for attempt in range(35): #600s
					try:
						ts_list = self.connection.dm_get_deployment_task_status(task.task_id)
						
						sys.stdout.write('.')
						sys.stdout.flush()
												
						if ts_list:
							status = ts_list[0].status
						
							if status == 'deployed':
								print "Application '%' has been successfully deployed on server %s." % (self.options.app_name, task.server_id)
								break
							
							elif status == 'failed':
								#show log
								try:
									print self.pretty(self.connection.dm_get_deployment_task_log,task.task_id)
								finally:
									print 'Deployment process has failed.'
								break
							
							elif status == 'pending':
								pass
							elif status == 'deploying':
								pass
							else:
								print status
							
						time.sleep(attempt)
						
					except (KeyboardInterrupt, SystemExit):
						break
				else:
					print "Maximum number of attempts was reached. On server %s application has not been deployed." % task.server_id
				print ''
				
		
class DmDeployApplicationAlias(DmDeployApplication):
	name = 'deploy'
	help = DmDeployApplication.help + '\nThis is an alias to dm-deploy-application command.'
				
	
class DmListDeploymentTasks(Command):
	name = 'dm-list-deployment-tasks'
	help = '-r farm-role-id -a app-id -s server-id'

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-a", "--app-id", dest="app_id", help="Application ID")
		parser.add_option("-r", "--farm-role-id", dest="farm_role_id", help="FarmRole ID")
		parser.add_option("-s", "--server-id", dest="server_id", default=None, help="Instance ID")
	
	def run(self):
		args = ( self.options.farm_role_id, self.options.app_id, self.options.server_id)
		print self.pretty(self.connection.dm_list_deployment_tasks, *args)
		
		
class DmGetDeploymentTaskStatus(Command):
	name = 'dm-get-deployment-task-status'
	help = '-t task-id'

	def __init__(self, config, *args):
		super(DmGetDeploymentTaskStatus, self).__init__(config, *args)
		self.require(self.options.task_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-t", "--task-id", dest="task_id", help="Deployment task ID")
	
	def run(self):
		print self.pretty(self.connection.dm_get_deployment_task_status, self.options.task_id)		
		
		
class DmSourcesList(Command):
	name = 'dm-list-sources'
	
	def run(self):
		print self.pretty(self.connection.dm_list_sources)
		

class DmApplicationsList(Command):
	name = 'dm-list-applications'
	
	def run(self):
		print self.pretty(self.connection.dm_list_applications)


class DmGetDeploymentTaskLog(Command):
	name = 'dm-get-deployment-task-log'
	help = '-t task-id [-s start-from -l limit]'

	def __init__(self, config, *args):
		super(DmGetDeploymentTaskLog, self).__init__(config, *args)
		self.require(self.options.task_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-t", "--task-id", dest="task_id", default=None, help="Task ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.task_id, self.options.start, self.options.limit)
		print self.pretty(self.connection.dm_get_deployment_task_log, *args)


class DNSZonesList(Command):
	name = 'list-dns-zones'
	
	def run(self):
		print self.pretty(self.connection.list_dns_zones)


class FarmsList(Command):
	name = 'list-farms'

	def run(self):
		print self.pretty(self.connection.list_farms)
		

class ScriptsList(Command):
	name = 'list-scripts'
	
	def run(self):
		print self.pretty(self.connection.list_scripts)
		
		
class DNSZoneRecordsList(Command):
	name = 'list-dns-zone-records'
	help = '-n name'

	def __init__(self, config, *args):
		super(DNSZoneRecordsList, self).__init__(config, *args)
		self.require(self.options.name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--zone-name", dest="name", default=None, help="Zone (Domain) name")
	
	def run(self):
		print self.pretty(self.connection.list_dns_zone_records, self.options.name)


class EventsList(Command):
	name = 'list-events'
	help = '{-f farm-id | -n name} [-s start-from -l limit]'

	def __init__(self, config, *args):
		super(EventsList, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.farm_id, self.options.start, self.options.limit)
		print self.pretty(self.connection.list_events, *args)


class LogsList(Command):
	name = 'list-logs'
	help = '{-f farm-id | -n name} [-i server-id -s start-from -l limit]'
	
	def __init__(self, config, *args):
		super(LogsList, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help="Instance ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.farm_id, self.options.server_id, self.options.start, self.options.limit)
		print self.pretty(self.connection.list_logs, *args)


class RolesList(Command):
	name = 'list-roles'
	help = '[-p platform -n name -x prefix -i image-id]'

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-p", "--platform", dest="platform", default=None, help="Cloud platform")
		parser.add_option("-n", "--name", dest="name", default=None, help="List roles with specified role name.")
		parser.add_option("-x", "--prefix", dest="prefix", default=None, help="List all roles begins with specified prefix.")
		parser.add_option("-i", "--image-id", dest="image_id", default=None, help="List roles with specified image id.")
	
	def run(self):
		args = (self.options.platform, self.options.name, self.options.prefix, self.options.image_id)
		print self.pretty(self.connection.list_roles, *args)


class ScriptGetDetails(Command):
	name = 'get-script-details'
	help = '-s script-id'

	def __init__(self, config, *args):
		super(ScriptGetDetails, self).__init__(config, *args)
		self.require(self.options.script_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-s", "--script-id", dest="script_id", default=None, help="Script ID")
	
	def run(self):
		print self.pretty(self.connection.get_script_details, self.options.script_id)
		

class BundleTaskGetStatus(Command):
	name = 'get-bundle-task-status'
	help = '-i bundle-task-id'
	
	def __init__(self, config, *args):
		super(BundleTaskGetStatus, self).__init__(config, *args)
		self.require(self.options.bt_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-i", "--bundle-task-id", dest="bt_id", default=None, help="ID of the bundle task")
	
	def run(self):
		print self.pretty(self.connection.get_bundle_task_status, self.options.bt_id)
		

class FarmGetDetails(Command):
	name = 'list-farm-roles'
	help = '{-f farm-id | -n name}'

	def __init__(self, config, *args):
		super(FarmGetDetails, self).__init__(config, *args)
		self.require(self.options.farm_id or self.options.farm_name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
	
	def run(self):
		print self.pretty(self.connection.get_farm_details, self.options.farm_id)


class FarmRoleProperties(Command):
	name = 'get-farm-role-properties'
	help = '{-f farm-id | -n name}'

	def __init__(self, config, *args):
		super(FarmRoleProperties, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
	
	def run(self):
		print self.pretty(self.connection.get_farm_role_properties, self.options.farm_id)	
		
		
class ServerList(Command):
	name = 'list-servers'
	help = '{-f farm-id | -n name} [-r farm-role-id]'

	def __init__(self, config, *args):
		super(ServerList, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-r", "--farm-role-id", dest="farm_role_id", default=None, help="Farm Role ID")
	
	def run(self):
		print self.pretty(self.connection.list_servers, self.options.farm_id, self.options.farm_role_id)	
		
				
class FarmGetStats(Command):
	name = 'get-farm-stats'
	help = '{-f farm-id | -n name} [-d date]'

	def __init__(self, config, *args):
		super(FarmGetStats, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-d", "--date", dest="date", default=None, help="Date (mm-yyyy)")
	
	def run(self):
		print self.pretty(self.connection.get_farm_stats, self.options.farm_id,self.options.date)	
		

class StatisticsGetGraphURL(Command):
	name = 'get-statistics-graph-url'
	help = '-o object-type -i object-id -n watcher-name -g graph-type'

	def __init__(self, config, *args):
		super(StatisticsGetGraphURL, self).__init__(config, *args)
		self.require(self.options.obj_type, self.options.obj_id, self.options.name, self.options.graph_type)

	@classmethod
	def inject_options(cls, parser):		
		id_help = "In case if object type is instance ObjectID shoudl be server id, in case if object type is role ObjectID should be role id \
		and in case if object type is farm ObjectID should be farm id"
		parser.add_option("-o", "--object-type", dest="obj_type", default=None, help="Object type. Valid values are: role, server or farm")
		parser.add_option("-i", "--object-id", dest="obj_id", default=None, help=id_help)
		parser.add_option("-n", "--watcher-name", dest="name", default=None, help="Watcher name could be CPU, NET, MEM or LA")
		parser.add_option("-g", "--graph-type", dest="graph_type", default=None, help="Graph type could be daily, weekly, monthly or yearly")
	
	def run(self):
		args = (self.options.obj_type, self.options.obj_id, self.options.name, self.options.graph_type)
		print self.pretty(self.connection.get_statistics_graph_URL, *args)	


class ServerTerminate(Command):
	name = 'terminate-server'
	help = '-i server-id [-d decrease-min-instances-setting]'

	def __init__(self, config, *args):
		super(ServerTerminate, self).__init__(config, *args)
		self.require(self.options.server_id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help='ServerID')
		parser.add_option("-d", "--decrease-min-instances", dest="decrease", default=None, help='Decrease MinInstances setting for role (Default: 0)')
	
	def run(self):
		print self.pretty(self.connection.terminate_server, self.options.server_id, self.options.decrease)			


class ServerImageCreate(Command):
	name = 'create-server-image'
	help = '-i server-id -n role-name'

	def __init__(self, config, *args):
		super(ServerImageCreate, self).__init__(config, *args)
		self.require(self.options.server_id, self.options.name)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help='ServerID')
		parser.add_option("-n", "--role-name", dest="name", default=None, help='Name for the new role')
		
	def run(self):
		print self.pretty(self.connection.create_server_image, self.options.server_id, self.options.name)	
	
	
class ServerLaunch(Command):
	name = 'launch-server'
	help = '-i farm-role-id [--increase-max-instances]'

	def __init__(self, config, *args):
		super(ServerLaunch, self).__init__(config, *args)
		self.require(self.options.farm_role_id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help='FarmRoleID on which scalr should launch new instance')
		parser.add_option("--increase-max-instances", dest="increase_max_instances", action="store_true", help='Increase min instances for this role')
	
	def run(self):
		print self.pretty(self.connection.launch_server, self.options.farm_role_id, self.options.increase_max_instances)
	
		
class FarmLaunch(Command):
	name = 'launch-farm'
	help = '{-f farm-id | -n farm-name} [--non-interactive]'

	def __init__(self, config, *args):
		super(FarmLaunch, self).__init__(config, *args)
		self.require(self.options.farm_id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="The ID of farm that you want to launch")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("--non-interactive", dest="non_interactive", action="store_true", help="Use this option to avoid checking farm state")
		
	def run(self):
		result = self.pretty(self.connection.launch_farm, self.options.farm_id)	
		
		if self.options.non_interactive:
			print result
		
		elif not isinstance(result,ScalrAPIError):
			print "Starting farm '%s'.." % self.options.farm_name,
			for seconds in waits(60):
				try:
					status = self.connection.get_farm_status(self.options.farm_id)
					sys.stdout.write('.')
					sys.stdout.flush()
					if status == 'Running':
						print 'Started.' 
						break
					time.sleep(seconds)
				except (KeyboardInterrupt, SystemExit):
					break
			else: 
				print 'Cannot start farm. Please try again.'

class FarmTerminate(Command):
	name = 'terminate-farm'
	help = '{-f farm-id | -n farm-name} -e keep-ebs, -i keep-eip -d keep-dns-zone [--non-interactive]'

	def __init__(self, config, *args):
		super(FarmTerminate, self).__init__(config, *args)
		self.require(self.options.farm_id or self.options.farm_name, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="The ID of farm that you want to terminate")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-e", "--keep-ebs", dest="keep_ebs", default=None, help="Keep EBS volumes created for roles on this farm 0|1")
		parser.add_option("-i", "--keep-eip", dest="keep_eip", default=None, help='Keep Elastic IPs created for roles on this farm 0|1')
		parser.add_option("-d", "--keep-dns-zone", dest="keep_dns_zone", default=None, help="Keep DNS zone that assigned to this farm on nameservers 0|1")
		parser.add_option("--non-interactive", dest="non_interactive", action="store_true", help="Use this option to avoid checking farm state")
	
	def run(self):
		args = (self.options.farm_id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)
		result = self.pretty(self.connection.terminate_farm, *args)	

		if self.options.non_interactive:
			print result
		
		elif not isinstance(result,ScalrAPIError):
			print "Stopping farm '%s'.." % self.options.farm_name,
			for seconds in waits(60):
				try:
					status = self.connection.get_farm_status(self.options.farm_id)
					sys.stdout.write('.')
					sys.stdout.flush()
					if status == 'Stopped':
						print 'Stopped.'
						break
					time.sleep(seconds)
				except (KeyboardInterrupt, SystemExit):
					break
			else: 
				print 'Cannot stop farm. Please try again.'
		
class ScriptExecute(Command):
	name = 'execute-script'
	help = '{-f farm-id | -n name} -e script-id -a async -t timeout [-i farm-role-id -s server-id -r revision -v variables]'
	#TODO: Test passing variables  

	def __init__(self, config, *args):
		super(ScriptExecute, self).__init__(config, *args)
		self.require(self.options.farm_id, self.options.script_id, self.options.mode, self.options.timeout)

	@classmethod
	def inject_options(cls, parser):		
		id_help = "Script will be executed on all instances with this farm role ID. You can get this ID by using GetFarmDetails API call"
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help=id_help)
		parser.add_option("-s", "--server-id", dest="server_id", default=None, help="Script will be executed on this server")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Execute script on specified farm")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-e", "--script-id", dest="script_id", default=None, help="Script ID")
		parser.add_option("-t", "--timeout", dest="timeout", default=None, help="Script execution timeout (seconds)")
		parser.add_option("-a", "--async", dest="mode", default=None, help="Excute script asynchronously (1) or synchronously (0)")
		parser.add_option("-r", "--revision", dest="revision", default=None, help="Execute specified revision of script")
		parser.add_option("-v", "--variables", dest="variables", default=None, help="Script variables.Example: key1=value1,key2=value2")
	
	def parse_variables(self, vars):
		'''
		k1=v1;k2=v2 -> dict(k1=v1,k2=v2)
		'''
		
		s = {}
		for pair in vars.split(','):
			k,v = pair.split('=')
			s[k] = v
		return s

	
	def run(self):
		args = (self.options.farm_id, self.options.script_id, self.options.timeout \
				, self.options.mode, self.options.farm_role_id, self.options.server_id, self.parse_variables(self.options.variables), self.options.revision)
		print self.pretty(self.connection.execute_script, *args)	


class ServerReboot(Command):
	name = 'reboot-server'
	help = '-s server-id'

	def __init__(self, config, *args):
		super(ServerReboot, self).__init__(config, *args)
		self.require(self.options.server_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-s", "--server-id", dest="server_id", default=None, help="Server ID")
	
	def run(self):
		print self.pretty(self.connection.reboot_server, self.options.server_id)	


class DNSZoneCreate(Command):
	name = 'create-dns-zone'
	help = '-d domain-name [{-f farm-id | -n farm-name} -i farm-role-id]'

	def __init__(self, config, *args):
		super(DNSZoneCreate, self).__init__(config, *args)
		self.require(self.options.name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-d", "--domain-name", dest="name", default=None, help="Domain (Application) name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help="Farm Role ID")
	
	def run(self):
		print self.pretty(self.connection.create_dns_zone, self.options.name, self.options.farm_id, self.options.farm_role_id)		
	
	
class DNSZoneRecordAdd(Command):
	name = 'add-dns-zone-record'
	help = '-z zone-name -t type -l ttl -n record-name -v record-value [-p priority -w weight -o port]'

	def __init__(self, config, *args):
		super(DNSZoneRecordAdd, self).__init__(config, *args)
		self.require(self.options.zone_name, self.options.type, self.options.ttl, self.options.record_name, self.options.record_value)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-z", "--zone-name", dest="zone_name", default=None, help="Zone (Domain) name")
		parser.add_option("-t", "--type", dest="type", default=None, help="Record type (A, MX, CNAME, NS, TXT, SRV)")
		parser.add_option("-l", "--ttl", dest="ttl", default=None, help="Record TTL")
		parser.add_option("-n", "--record-name", dest="record_name", default=None, help="Record name")
		parser.add_option("-v", "--record-value", dest="record_value", default=None, help="Record value")
		
		parser.add_option("-p", "--priority", dest="priority", default=None, help="Priority (for MX records)")
		parser.add_option("-w", "--weight", dest="weight", default=None, help="Weight (for SRV records)")
		parser.add_option("-o", "--port", dest="port", default=None, help="Port (for SRV records)")		
	
	def run(self):
		args = (self.options.zone_name, self.options.type, self.options.ttl, self.options.record_name, self.options.record_value,
				self.options.priority, self.options.weight, self.options.port)
		print self.pretty(self.connection.add_dns_zone_record, *args)	


class DNSZoneRecordRemove(Command):
	name = 'remove-dns-zone-record'
	help = '-n name -i record-id'

	def __init__(self, config, *args):
		super(DNSZoneRecordRemove, self).__init__(config, *args)
		self.require(self.options.name, self.options.record_id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--domain-name", dest="name", default=None, help="Domain (Application) name")
		parser.add_option("-i", "--record-id", dest="record_id", default=None, help="Record ID")
	
	def run(self):
		print self.pretty(self.connection.remove_dns_zone_record, self.options.name, self.options.record_id)			

	
class ApacheVhostCreate(Command):
	name = 'create-apache-vhost'
	help = '-d domain-name {-f farm-id | -n name} -i farm-role-id -r document-root -s enable-ssl [-k key-path -c cert-path]'
	
	def __init__(self, config, *args):
		super(ApacheVhostCreate, self).__init__(config, *args)
		self.require(self.options.domain, self.options.farm_id, self.options.farm_role_id, self.options.document_root, self.options.enable_ssl)
		pass			

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-d", "--domain-name", dest="domain", default=None, help="Domain (Application) name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-n", "--farm-name", dest="farm_name", default=None, help="The name of farm could be used INSTEAD of ID")
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help="Farm Role ID")
		parser.add_option("-r", "--document-root-dir", dest="document_root", default=None, help="Document root for virtualhost")
		parser.add_option("-s", "--enable-ssl", dest="enable_ssl", default=None, help="EnableSSL (1 - yes, 0 - no)")
		parser.add_option("-k", "--pk-path", dest="pk_path", default=None, help="Path to file with Private key for SSL")
		parser.add_option("-c", "--cert-path", dest="cert_path", default=None, help="Path to file with Certificate for SSL")
	
	def run(self):
		pk = None 
		cert = None
		
		if self.options.enable_ssl and int(self.options.enable_ssl):
			self.require(self.options.pk_path, self.options.cert_path)
			
			if not os.path.exists(self.options.cert_path):
				print '%s : file with certificate not found.' % self.options.cert_path
				sys.exit()
			else: 
				cert = open(self.options.cert_path, 'r').read()
				
			if not os.path.exists(self.options.pk_path):
				print '%s : file with private key not found.' % self.options.pk_path
				sys.exit()
			else: 
				pk = open(self.options.pk_path, 'r').read()
				
		args = (self.options.domain, self.options.farm_id, self.options.farm_role_id, self.options.document_root, self.options.enable_ssl, pk, cert)
		print self.pretty(self.connection.create_apache_vhost, *args)	
		
	
class ConfigureEnv(Command):
	name = 'configure'
	help = '-i key_id -a key -u api_url -e env_id'
		
	def __init__(self, config, *args):
		super(ConfigureEnv, self).__init__(config, *args)
		self.require(self.options.key_id, self.options.key, self.options.api_url)
			
	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-i", "--key-id", dest="key_id", default=None, help="Scalr API key ID")
		parser.add_option("-a", "--access-key", dest="key", default=None, help="Scalr API access key")
		parser.add_option("-e", "--env-id", dest="env_id", default=None, help="Scalr Environment ID")
		parser.add_option("-u", "--api-url", dest="api_url", default=DEFAULT_API_URL, help="Scalr API URL (IF you use open source Scalr installation)")
		
	def run(self):		
		e = Environment(url=self.options.api_url,
				key_id=self.options.key_id,
				key=self.options.key,
				env_id = self.options.env_id,
				api_version = '2.3.0')
		
		e.write(self.config.base_path)
		e = Environment.from_ini(self.config.base_path)
		print e


class EnvironmentsList(Command):
	name = 'list-environments'

	def run(self):
		print self.pretty(self.connection.list_environments)
		
		
class ShowConfig(Command):
	name = 'show-config'
		
	def run(self):		
		e = Environment.from_ini(self.config.base_path)
		print e
		
		
def waits(n):
	num = 0
	sum = 0
	while sum <= n:
		yield num
		num += 1
		sum += num

'''
class CountDownTimer(threading.Thread):

	def __init__(self, seconds):
		self.runTime = seconds
		threading.Thread.__init__(self)

	def run(self):
		counter = self.runTime
		for sec in range(self.runTime):
			print counter
			time.sleep(1.0)
			counter -= 1
		else:
			pass
	
	def stop(self):
		pass

class BasicProgressBar(object):
	def __init__(self, callback=None, callback_kwargs=None, counts=None, sleeptime=None, exithook=None, hook_kwargs=None):
		t = CountDownTimer(counts)
		t.run()
		result = callback(**callback_kwargs)
		t.stop()
'''