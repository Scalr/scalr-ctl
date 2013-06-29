'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''
import os

from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from prettytable import PrettyTable
from scalrtools.api.auth import KeyAuth, LDAPAuth


class ScalrCfgError(BaseException):
	pass


class ScalrEnvError(ScalrCfgError):
	pass

	
class ConfigSection(object):
	config_name = None
	options = {}
	
	def __init__(self, **kwargs):
		for arg in kwargs:
			if hasattr(self, arg):
				setattr(self, arg, kwargs[arg])

	def write(self, base_path, section):
		config = ConfigParser()
		
		path = os.path.join(base_path, self.config_name)
		if os.path.exists(path):
			config.read(path)
		elif not os.path.exists(os.path.dirname(path)):
			os.makedirs(os.path.dirname(path))
			
		if not config.has_section(section):
			config.add_section(section)
		
		for option in self.options:
			config.set(section, self.options[option], getattr(self, option))
			
		file = open(path, 'w')
		config.write(file)
		file.close()
			
	@classmethod
	def from_ini(cls, base_path, section):
		obj = cls()
		path = os.path.join(base_path, cls.config_name)
		
		if os.path.exists(path):
			config = ConfigParser()
			config.read(path)
			setattr(obj, 'name', section)
		
			for option in cls.options:
				try:
					value = config.get(section, cls.options[option])
					setattr(obj, option, value)
				except (NoSectionError, NoOptionError), e:
						continue
		return obj

	
class Environment(ConfigSection):
	url=None
	key_id=None
	key=None
	ldap_username=None
	ldap_password=None
	env_id = None
	api_version = None	
	
	config_name = 'config.ini'
	
	options = dict(
			url = 'scalr_url',
			key_id = 'scalr_key_id',
			key = 'scalr_api_key',
			ldap_username = 'ldap_username',
			ldap_password = 'ldap_password',
			env_id = 'env_id',
			api_version = 'version')
	
	def write(self, base_path, section='api'):
		super(Environment, self).write(base_path, section)
			
	@classmethod
	def from_ini(cls, base_path, section='api'):
		return super(Environment, cls).from_ini(base_path, section)
	
	def __repr__(self):
		column_names = ('setting','value')
		table = PrettyTable(column_names)
		#prettytable 0.5/0.6 support
		if hasattr(table, 'align'):
			table.align = 'l'
		else:
			for field in column_names:
				table.set_field_align(field, 'l')		
		
		visible_length = 26
		
		table.add_row(('url', self.url))
		table.add_row(('access key', self.key[:visible_length]+'...' if len(self.key)>40 else self.key))
		table.add_row(('key id', self.key_id))
		table.add_row(('ldap username', self.ldap_username))
		table.add_row(('ldap password', "****" if self.ldap_password is not None else "not-set"))
		table.add_row(('environment id', self.env_id))
		table.add_row(('version', self.api_version))
		
		res = str(table)
		print 'b'
		return res
	

class Configuration(object):
	logger = None
	base_path = None
	
	environment = None
	application = None
	repository = None
	scripts = None
	
	def __init__(self, base_path=None, logger=None):
		self.base_path = base_path or os.path.expanduser("~/.scalr/")
		self.logger = logger


	def get_auth(self):
		if self.environment.key_id is not None and self.environment.key_id != "None":
			# Config loader returns a "None" string.
			return KeyAuth(self.environment.key_id, self.environment.key)

		if self.environment.ldap_username is not None:
			return LDAPAuth(self.environment.ldap_username, self.environment.ldap_password)

		self.raise_invalid_environment("auth")

	def set_logger(self, logger):
		self.logger = logger

	def raise_invalid_environment(self, k):
		raise ScalrEnvError('Environment not set, missing: {0}'.format(k))

	def set_environment(self, **options):
		# Options:
		# url
		# key_id
		# key
		# ldap_username
		# ldap_password
		# env_id

		self.environment = Environment.from_ini(self.base_path)

		for k, v in options.items():
			if v is not None:
				setattr(self.environment, k, v)

		if not self.environment.url:
			self.raise_invalid_environment("api_url")

		if not self.environment.api_version:
			self.raise_invalid_environment("api_version")