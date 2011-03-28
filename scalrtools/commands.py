'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os
import sys

from ConfigParser import ConfigParser
from optparse import OptionParser, TitledHelpFormatter
from shutil import copyfile

from prettytable import PrettyTable	

from config import Environment, Repository, Application, Scripts
from api import ScalrConnection, ScalrAPIError
from api.view import TableViewer


class Command(object):
	name = None
	help = None
	
	config = None
	parser = None
	options = None
		
	def __init__(self, config, *args):
		self.config = config
		self.parser = OptionParser(usage=self.help)
		self.inject_options(self.parser)
		self.options = self.parser.parse_args(list(args))[0]
			
	def run(self):
		pass
	
	def api_call(self, callback, *args, **kwargs):
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
		parser = OptionParser(usage=cls.help) 
		cls.inject_options(parser)
		return parser.format_help(TitledHelpFormatter())

	@property		
	def connection(self):
		conn = None
		if self.config.environment:
			conn = ScalrConnection(self.config.environment.url, 
					self.config.environment.key_id, 
					self.config.environment.key, 
					self.config.environment.api_version, 
					logger=self.config.logger)
		return conn

		
class ApacheVhostsList(Command):
	name = 'list-apache-virtual-hosts'
	help = 'scalr-tools list-apache-virtual-hosts'
	
	def run(self):
		print self.api_call(self.connection.list_apache_virtual_hosts)


class DNSZonesList(Command):
	name = 'list-dns-zones'
	help = 'scalr-tools list-dns-zones'
	
	def run(self):
		print self.api_call(self.connection.list_dns_zones)


class FarmsList(Command):
	name = 'list-farms'
	help = 'scalr-tools list-farms'

	def run(self):
		print self.api_call(self.connection.list_farms)
		

class ScriptsList(Command):
	name = 'list-scripts'
	help = 'scalr-tools list-scripts'
	
	def run(self):
		print self.api_call(self.connection.list_scripts)
		
		
class DNSZoneRecordsList(Command):
	name = 'list-dns-zone-records'
	help = 'scalr-tools list-dns-zone-records -n name'

	def __init__(self, config, *args):
		super(DNSZoneRecordsList, self).__init__(config, *args)
		self.require(self.options.name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--zone-name", dest="name", default=None, help="Zone (Domain) name")
	
	def run(self):
		print self.api_call(self.connection.list_dns_zone_records, self.options.name)


class EventsList(Command):
	name = 'list-events'
	help = 'scalr-tools list-events -f farm-id [-s start-from -l limit]'

	def __init__(self, config, *args):
		super(EventsList, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.id, self.options.start, self.options.limit)
		print self.api_call(self.connection.list_events, *args)


class LogsList(Command):
	name = 'list-logs'
	help = 'scalr-tools list-logs -f farm-id [-i server-id -s start-from -l limit]'
	
	def __init__(self, config, *args):
		super(LogsList, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-i", "--server-id", dest="server_id", default=None, help="Instance ID")
		parser.add_option("-s", "--start-from", dest="start", default=None, help="Start from specified event number (Can be used for paging)")
		parser.add_option("-l", "--record-limit", dest="limit", default=None, help="Limit number of returned events (Can be used for paging)")
	
	def run(self):
		args = (self.options.id, self.options.server_id, self.options.start, self.options.limit)
		print self.api_call(self.connection.list_logs, *args)


class RolesList(Command):
	name = 'list-roles'
	help = 'scalr-tools list-roles [-p platform -n name -x prefix -i image-id]'

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-p", "--platform", dest="platform", default=None, help="Cloud platform")
		parser.add_option("-n", "--name", dest="name", default=None, help="List roles with specified role name.")
		parser.add_option("-x", "--prefix", dest="prefix", default=None, help="List all roles begins with specified prefix.")
		parser.add_option("-i", "--image-id", dest="image_id", default=None, help="List roles with specified image id.")
	
	def run(self):
		args = (self.options.platform, self.options.name, self.options.prefix, self.options.image_id)
		print self.api_call(self.connection.list_roles, *args)


class ScriptGetDetails(Command):
	name = 'get-script-details'
	help = 'scalr-tools get-script-details -s script-id'

	def __init__(self, config, *args):
		super(ScriptGetDetails, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-s", "--script-id", dest="id", default=None, help="Script ID")
	
	def run(self):
		print self.api_call(self.connection.get_script_details, self.options.id)
		

class BundleTaskGetStatus(Command):
	name = 'get-bundle-task-status'
	help = 'scalr-tools get-bundle-task-status -i bundle-task-id'
	
	def __init__(self, config, *args):
		super(BundleTaskGetStatus, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-i", "--bundle-task-id", dest="id", default=None, help="ID of the bundle task")
	
	def run(self):
		print self.api_call(self.connection.get_bundle_task_status, self.options.id)
		

class FarmGetDetails(Command):
	name = 'get-farm-details'
	help = 'scalr-tools get-farm-details -f farm-id'

	def __init__(self, config, *args):
		super(FarmGetDetails, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
	
	def run(self):
		print self.api_call(self.connection.get_farm_details, self.options.id)	


class FarmGetStats(Command):
	name = 'get-farm-stats'
	help = 'scalr-tools get-farm-stats -f farm-id [-d date]'

	def __init__(self, config, *args):
		super(FarmGetStats, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="Farm ID")
		parser.add_option("-d", "--date", dest="date", default=None, help="Date (mm-yyyy)")
	
	def run(self):
		print self.api_call(self.connection.get_farm_stats, self.options.id,self.options.date)	
		

class StatisticsGetGraphURL(Command):
	name = 'get-statistics-graph-url'
	help = 'scalr-tools get-statistics-graph-url -o object-type -i object-id -n watcher-name -g graph-type'

	def __init__(self, config, *args):
		super(StatisticsGetGraphURL, self).__init__(config, *args)
		self.require(self.options.obj_type, self.options.id, self.options.name, self.options.graph_type)

	@classmethod
	def inject_options(cls, parser):		
		id_help = "In case if object type is instance ObjectID shoudl be server id, in case if object type is role ObjectID should be role id \
		and in case if object type is farm ObjectID should be farm id"
		parser.add_option("-o", "--object-type", dest="obj_type", default=None, help="Object type. Valid values are: role, server or farm")
		parser.add_option("-i", "--object-id", dest="id", default=None, help=id_help)
		parser.add_option("-n", "--watcher-name", dest="name", default=None, help="Watcher name could be CPU, NET, MEM or LA")
		parser.add_option("-g", "--graph-type", dest="graph_type", default=None, help="Graph type could be daily, weekly, monthly or yearly")
	
	def run(self):
		args = (self.options.obj_type, self.options.id, self.options.name, self.options.graph_type)
		print self.api_call(self.connection.get_statistics_graph_URL, *args)	


class ServerTerminate(Command):
	name = 'terminate-server'
	help = 'scalr-tools terminate-server -i server-id [-d decrease-min-instances-setting]'

	def __init__(self, config, *args):
		super(ServerTerminate, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--server-id", dest="id", default=None, help='ServerID')
		parser.add_option("-d", "--decrease-min-instances", dest="decrease", default=None, help='Decrease MinInstances setting for role (Default: 0)')
	
	def run(self):
		print self.api_call(self.connection.terminate_server, self.options.id, self.options.decrease)			


class ServerImageCreate(Command):
	name = 'create-server-image'
	help = 'scalr-tools create-server-image -i server-id -n role-name'

	def __init__(self, config, *args):
		super(ServerImageCreate, self).__init__(config, *args)
		self.require(self.options.id, self.options.name)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--server-id", dest="id", default=None, help='ServerID')
		parser.add_option("-n", "--role-name", dest="name", default=None, help='Name for the new role')
		
	def run(self):
		print self.api_call(self.connection.create_server_image, self.options.id, self.options.name)	
	
	
class ServerLaunch(Command):
	name = 'launch-server'
	help = 'scalr-tools launch-server -i farm-role-id'

	def __init__(self, config, *args):
		super(ServerLaunch, self).__init__(config, *args)
		self.require(self.options.farm_role_id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help='FarmRoleID on which scalr should launch new instance')
	
	def run(self):
		print self.api_call(self.connection.launch_server, self.options.farm_role_id)
	
	
class FarmLaunch(Command):
	name = 'launch-farm'
	help = 'scalr-tools launch-farm -f farm-id'

	def __init__(self, config, *args):
		super(FarmLaunch, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="The ID of farm that you want to launch")
	
	def run(self):
		print self.api_call(self.connection.launch_farm, self.options.id)	
	
	
class FarmTerminate(Command):
	name = 'terminate-farm'
	help = 'scalr-tools terminate-farm -f farm-id -e keep-ebs, -i keep-eip -d keep-dns-zone'

	def __init__(self, config, *args):
		super(FarmTerminate, self).__init__(config, *args)
		self.require(self.options.id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)

	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-f", "--farm-id", dest="id", default=None, help="The ID of farm that you want to terminate")
		parser.add_option("-e", "--keep-ebs", dest="keep_ebs", default=None, help="Keep EBS volumes created for roles on this farm 0|1")
		parser.add_option("-i", "--keep-eip", dest="keep_eip", default=None, help='Keep Elastic IPs created for roles on this farm 0|1')
		parser.add_option("-d", "--keep-dns-zone", dest="keep_dns_zone", default=None, help="Keep DNS zone that assigned to this farm on nameservers 0|1")
	
	def run(self):
		args = (self.options.id, self.options.keep_ebs, self.options.keep_eip, self.options.keep_dns_zone)
		print self.api_call(self.connection.terminate_farm, *args)	
		
		
class ScriptExecute(Command):
	name = 'execute-script'
	help = 'scalr-tools execute-script -f farm-id -e script-id -a async -t timeout [-i farm-role-id -s server-id -r revision -v variables]'
	#TODO: Test passing variables  

	def __init__(self, config, *args):
		super(ScriptExecute, self).__init__(config, *args)
		self.require(self.options.farm_id, self.options.script_id, self.options.async, self.options.timeout)

	@classmethod
	def inject_options(cls, parser):		
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
		print self.api_call(self.connection.execute_script, *args)	


class ServerReboot(Command):
	name = 'reboot-server'
	help = 'scalr-tools reboot-server -s server-id'

	def __init__(self, config, *args):
		super(ServerReboot, self).__init__(config, *args)
		self.require(self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-s", "--server-id", dest="id", default=None, help="Server ID")
	
	def run(self):
		print self.api_call(self.connection.reboot_server, self.options.id)	


class DNSZoneCreate(Command):
	name = 'create-dns-zone'
	help = 'scalr-tools create-dns-zone -n domain-name [-f farm-id -i farm-role-id]'

	def __init__(self, config, *args):
		super(DNSZoneCreate, self).__init__(config, *args)
		self.require(self.options.name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--domain-name", dest="name", default=None, help="Domain (Application) name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
		parser.add_option("-i", "--farm-role-id", dest="farm_role_id", default=None, help="Farm Role ID")
	
	def run(self):
		print self.api_call(self.connection.create_dns_zone, self.options.name, self.options.farm_id, self.options.farm_role_id)		
	
	
class DNSZoneRecordAdd(Command):
	name = 'add-dns-zone-record'
	help = 'scalr-tools add-dns-zone-record -z zone-name -t type -l ttl -n record-name -v record-value [-p priority -w weight -o port]'

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
		print self.api_call(self.connection.add_dns_zone_record, *args)	


class DNSZoneRecordRemove(Command):
	name = 'remove-dns-zone-record'
	help = 'scalr-tools remove-dns-zone-record -n name -i record-id'

	def __init__(self, config, *args):
		super(DNSZoneRecordRemove, self).__init__(config, *args)
		self.require(self.options.name, self.options.id)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--domain-name", dest="name", default=None, help="Domain (Application) name")
		parser.add_option("-i", "--record-id", dest="id", default=None, help="Record ID")
	
	def run(self):
		print self.api_call(self.connection.remove_dns_zone_record, self.options.name, self.options.id)			

	
class ApacheVhostCreate(Command):
	name = 'create-apache-vhost'
	help = 'scalr-tools create-apache-vhost -d domain-name -f farm-id -i farm-role-id -r document-root -s enable-ssl [-k key-path -c cert-path]'
	
	def __init__(self, config, *args):
		super(ApacheVhostCreate, self).__init__(config, *args)
		self.require(self.options.domain, self.options.farm_id, self.options.farm_role_id, self.options.document_root, self.options.enable_ssl)
		pass			

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-d", "--domain-name", dest="domain", default=None, help="Domain (Application) name")
		parser.add_option("-f", "--farm-id", dest="farm_id", default=None, help="Farm ID")
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
		print self.api_call(self.connection.create_apache_vhost, *args)	
		
	
class ConfigureEnv(Command):
	name = 'configure-env'
	help = 'scalr-tools configure-env -a key_id -s key -u api_url'
		
	def __init__(self, config, *args):
		super(ConfigureEnv, self).__init__(config, *args)
		self.require(self.options.key_id, self.options.key, self.options.api_url)
			
	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-a", "--access-key", dest="key_id", default=None, help="Access key")
		parser.add_option("-s", "--secret-key", dest="key", default=None, help="Secret key")
		parser.add_option("-u", "--api-url", dest="api_url", default=None, help="API URL")
		
	def run(self):		
		e = Environment(url=self.options.api_url,
				key_id=self.options.key_id,
				key=self.options.key,
				api_version = '2.2.0')
		
		e.write(self.config.base_path)
		
		s = Scripts(svn='1698', git='1700')
		s.write(self.config.base_path)
		
		s = Scripts.from_ini(self.config.base_path)
		
		e = Environment.from_ini(self.config.base_path)
		table = PrettyTable(fields=('setting','value'))
		table.add_row(('url', e.url))
		table.add_row(('key', e.key[:40]+'...' if len(e.key)>40 else e.key))
		table.add_row(('key id', e.key_id))
		table.add_row(('version', e.api_version))
		
		table.add_row(('svn', s.svn))
		table.add_row(('git', s.git))		
		
		print table
		
class ConfigureRepo(Command):
	name = 'configure-repo'
	help = 'scalr-tools configure-repo -n name -t svn|git -u repo_url -l login -p password'
	
	def __init__(self, config, *args):
		super(ConfigureRepo, self).__init__(config, *args)
		self.require(self.options.type, self.options.url, self.options.name)
		
	@classmethod
	def inject_options(cls, parser):		
		parser.add_option("-t", "--type", dest="type", default=None, help="SVN or GIT")
		parser.add_option("-u", "--url", dest="url", default=None, help="Repository URL")
		parser.add_option("-l", "--login", dest="login", default=None, help="Repository username")
		parser.add_option("-p", "--password", dest="password", default=None, help="Repository password")
		parser.add_option("-n", "--name", dest="name", default=None, help="Repository name")
		
		parser.add_option("-c", "--cert-path", dest="cert_path", default=None, help="Path to certificate in case of using GIT")
		parser.add_option("-k", "--pkey-path", dest="pk_path", default=None, help="Path to private key in case of using GIT")
				
	def run(self):		
		r = Repository(name = self.options.name,
				url = self.options.url,
				type = self.options.type,
				login = self.options.login,
				password = self.options.password)
		
		r.write(self.config.base_path, self.options.name)
		
		key_path = os.path.join(self.config.base_path, 'keys')
		cert_path = os.path.join(key_path, self.options.name+'.cert')
		pk_path = os.path.join(key_path, self.options.name+'.pk')
		
		if self.options.cert_path and self.options.pk_path:
			if not os.path.exists(key_path):
				os.makedirs(key_path)
			try:
				copyfile(self.options.cert_path, cert_path)
				copyfile(self.options.pk_path, pk_path)
			except IOError, e:
				print e
				sys.exit
		
		r = Repository.from_ini(self.config.base_path, self.options.name)

		table = PrettyTable(fields=('setting','value'))
		table.add_row(('name', r.name))
		table.add_row(('type', r.type))
		table.add_row(('url', r.url))
		table.add_row(('login', r.login))
		table.add_row(('password', r.password))
		table.add_row(('cert', cert_path if cert_path and os.path.exists(cert_path) else None))
		table.add_row(('pkey', pk_path if pk_path and os.path.exists(pk_path) else None))
		print table
		
class ConfigureApp(Command):
	name = 'configure-app'
	help = 'scalr-tools configure-app -n name -r repo-name -i farm-role-id -f farm-id -p remote-path'
	
	def __init__(self, config, *args):
		super(ConfigureApp, self).__init__(config, *args)
		self.require(self.options.name, self.options.repo_name, self.options.farm_id, self.options.farm_role_id, self.options.remote_path)
		
	@classmethod
	def inject_options(cls, parser):
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
		
		table = PrettyTable(fields=('setting','value'))
		table.add_row(('name', a.name))
		table.add_row(('repo name', a.repo_name))
		table.add_row(('farm id', a.farm_id))
		table.add_row(('farm role id', a.farm_role_id))
		table.add_row(('remote path', a.remote_path))
		print table
		
class AppsList(Command):
	name = 'list-apps'
	help = 'scalr-tools list-apps'
	
	def run(self):	
		config = ConfigParser()
		path = os.path.join(self.config.base_path, Application.config_name)
		config.read(path)
		column_names = ['name', 'repo name', 'farm id', 'farm role id', 'remote path']
		pt = PrettyTable(column_names, caching=False)
		for app_name in config.sections():
			a = Application.from_ini(self.config.base_path, app_name)
			row = [a.name, a.repo_name, a.farm_id, a.farm_role_id, a.remote_path]
			pt.add_row(row)
		print str(pt)
			
			
class ReposList(Command):
	name = 'list-repos'
	help = 'scalr-tools list-repos'
	
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
	
						
class Deploy(Command):
	name = 'deploy'
	help = 'scalr-tools deploy -n name'

	def __init__(self, config, *args):
		super(Deploy, self).__init__(config, *args)
		self.require(self.options.name)

	@classmethod
	def inject_options(cls, parser):
		parser.add_option("-n", "--name", dest="name", default=None, help="Application name")
	
	def run(self):
		print self.options.name
		self.config.set_application(self.options.name)
		
		farm_id = self.config.application.farm_id
		farm_role_id = self.config.application.farm_role_id
		remote_path = self.config.application.remote_path
		repo_name = self.config.application.repo_name
		
		self.config.set_repository(repo_name)
		
		url = self.config.repository.url
		login = self.config.repository.login
		password = self.config.repository.password
		repo_type = self.config.repository.type
		
		self.config.set_scripts()
		
		script_id = getattr(self.config.scripts, repo_type.lower())
		
		timeout = '1200'
		async = '0'
		revision = '1'
		
		variables = dict(svn_repo_url = url,
						svn_user = login,
						svn_password = password,
						svn_co_dir = remote_path)
		
		kwargs = dict(farm_id=farm_id, 
				script_id=script_id, 
				timeout=timeout, 
				async=async, 
				farm_role_id=farm_role_id, 
				config_variables=variables, 
				revision=revision)
		
		print self.api_call(self.connection.execute_script, **kwargs)	

