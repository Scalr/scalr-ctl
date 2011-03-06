'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

import os
import sys 

from optparse import OptionParser

usage= '''
	Usage:\n scalr-tools command [args][kwargs]
	Commands:
	Command could be one of Scalr API calls 
	See reference manual for details: http://wiki.scalr.net/API/API_Reference 
	or one of commands listed below:
	
	configure 	keys|help
	list 		app|repo|help
	add 		app|repo|help
	remove 		app|repo|help
	deploy 		application_name|help
	help
	
	'''

def main():
	
	params = sys.argv[1:]
	
	if not params:
		print 'Please specify appropreate params'
		sys.exit()

	command = params[0]	
	args = []
	kwargs = {}

	for entry in params[1:]:
		argument = entry.split('=')
		if len(argument)==1:
			args.append(argument[0])
		elif len(argument)==2 and argument[0]:
			kwargs[argument[0]] = argument[1]
		else:
			print usage

	
	api_calls = dict(
			DNSZoneCreate 			= 'create_dns_zone',
			ApacheVhostCreate 		= 'create_apache_vhost',
			ServerImageCreate 		= 'create_server_image',
			
			ApacheVhostsList 		= 'apache_virtual_host_list',
			DNSZonesList 			= 'dns_zones_list',
			DNSZoneRecordsList 		= 'dns_zone_record_list',
			EventsList 				= 'events_list',
			FarmsList 				= 'farms_list',
			LogsList 				= 'logs_list',
			RolesList 				= 'roles_list',
			ScriptsList				= 'scripts_list',
			
			ScriptGetDetails 		= 'get_script_details',
			BundleTaskGetStatus 	= 'get_bundle_task_status',
			FarmGetDetails 			= 'get_farm_details',
			
			FarmGetStats 			= 'get_farm_stats',
			StatisticsGetGraphURL	= 'get_statistics_graph_URL',
			
			ServerLaunch 			= 'launch_server',
			FarmLaunch 				= 'launch_farm',
			
			ServerTerminate 		= 'terminate_server',
			FarmTerminate 			= 'terminate_farm',
			
			DNSZoneRecordAdd 		= 'add_dns_zone_record',
			DNSZoneRecordRemove 	= 'remove_dns_zone_record',
			
			ScriptExecute 			= 'execute_script',
			ServerReboot 			= 'reboot_server'
			)
	
	commands = ['configure', 'list', 'add', 'remove','deploy','help']
	
	runner = Runner()
	action = getattr(runner, command.lower())	
	action(args, kwargs)


def get_connection():
	#settings.ini
	return None


class Configurator:
	
	def __init__(self):
		self.etc_path = ''
		self.settings_path = os.path.join(self.etc_path, 'settings.ini')
		self.apps_path = os.path.join(self.etc_path, 'apps.ini')
		self.repos_path = os.path.join(self.etc_path, 'repos.ini')

	def set_credintials(self,url=None,key_id=None,key=None):
		pass
	
	def get_credentials(self):
		url=None
		key_id=None
		key=None
		
		return (url,key_id, key)
	
	def list_apps(self):
		pass
	
	def list_repos(self):
		pass
	
	def add_app(self,app_name,repo_name,farm_id,role_id,target_dir):
		pass
	
	def add_repo(self, name, type, url, user, password):
		pass
	
	def remove_app(self, name):
		pass
	
	def remove_repo(self, name):
		pass


class Application:
	
	app_name = None
	repo_name = None
	farm_id = None
	role_id = None
	target_dir = None 
		
	def __init__(self,app_name,repo_name=None,farm_id=None,role_id=None,target_dir=None):
		pass
		
	def write(self, fp):
		pass
	
	def read(self, fp):
		pass
	
	def remove(self, fp):
		pass
	
	@classmethod
	def from_ini(cls, ini):
		return Application('')


class Repo:		
	name = None
	type = None
	url = None
	user = None
	password = None 
		
	def __init__(self,name,type=None,url=None,user=None,password=None):
		pass
		
	def write(self, path):
		pass
	
	def read(self, path):
		pass
	
	def remove(self, path):
		pass
	
	@classmethod
	def from_ini(cls, ini):
		return Repo('')	
	
	
class Runner:
	
	def __init__(self):
		pass	
	
	def configure(self, *args, **kwargs):
		if not args or not args[0]:
			print "Configuring everything"
		elif args[0][0] == 'keys':
			print "configuring keys" 
		else:
			print 'Usage: scalr-tools configure [keys]' 
	
	def list(self, *args, **kwargs):
		if args and args[0]:
			if args[0][0] == 'app':
				print "list app"
			elif args[0][0] == 'repo':
				print "list repo"
		else:
			print "Usage: scalr-tools list app|repo"
	
	def add(self, *args, **kwargs):
		if args and args[0]:
			if args[0][0] == 'app':
				print "add app"
			elif args[0][0] == 'repo':
				print "add repo"
		else:
			print "Usage: scalr-tools add app|repo"
		
	def remove(self, *args, **kwargs):
		if args and args[0]:
			if args[0][0] == 'app':
				print "remove app"
			elif args[0][0] == 'repo':
				print "remove repo"
		else:
			print "Usage: scalr-tools remove app|repo"
	
	def deploy(self, *args, **kwargs):
		conn = get_connection()
		if args and args[0] and args[0][0]:
			print "deploy %s" % args[0][0]
		else:
			print "Usage: scalr-tools deploy appname"
	
	def help(self, *args, **kwargs):
		print help
	
	
if __name__=='__main__':
	main()
	