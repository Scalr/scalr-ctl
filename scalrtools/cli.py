'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

import sys
import inspect
import logging
from optparse import OptionParser

import commands
from config import Configuration, ScalrCfgError, ScalrEnvError
from api.client import ScalrAPIError


def split_options(args):
	'''
	@return ([options], subcommand, [args])
	'''
	for arg in args[1:]:
		index = args.index(arg)
		prev = args[args.index(arg)-1]		
		if not arg.startswith('-') and (prev.startswith('--') or not prev.startswith('-') or index == 1):
			return (args[1:index], arg, args[index+1:])			
	return (args[1:], None, [])

def get_commands():
	hs = []
	for name, obj in inspect.getmembers(commands):
		if inspect.isclass(obj) and hasattr(obj, 'name') and getattr(obj, 'name'):
			hs.append(obj)
	return hs

def main():
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)
	fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
	handler.setFormatter(fmt)
	logger.addHandler(handler)

	usage='Usage: %s [options] subcommand [args]' % commands.progname
	
	parser = OptionParser(usage=usage, add_help_option=False)
	parser.add_option("--debug", dest="debug", action="store_true", help="Enable debug output")
	parser.add_option("-c", "--config-path", dest="base_path", default=None, help="Path to configuration files")
	parser.add_option("-i", "--key-id", dest="key_id", default=None, help="Scalr API key ID")
	parser.add_option("-a", "--access-key", dest="key", default=None, help="Scalr API access key")
	parser.add_option("-u", "--api-url", dest="api_url", default=None, help="Scalr API URL (IF you use open source Scalr installation)")
	parser.add_option("-e", "--env-id", dest="env_id", default=None, help="Scalr Environment ID")
	parser.add_option("-h", "--help", dest="help", action="store_true", help="Help")
	
	args, cmd, subargs = split_options(sys.argv)

	subcommands = sorted([command.name for command in get_commands() if not command.name.startswith('_')])
	help = parser.format_help() + \
			'\nAvailable subcommands:\n\n' + '\n'.join(subcommands) + \
			"\n\nFor more information try '%s help <subcommand>'" % commands.progname
			
	options = parser.parse_args(args)[0]		
			
	if not cmd or options.help:
		print help
		sys.exit()

	try:
		c = Configuration(options.base_path)
		c.set_environment(options.key, options.key_id, options.api_url, options.env_id)
		
		if options.debug:
			c.set_logger(logger)
			
	except ScalrEnvError, e:
		if not cmd.startswith('configure') and cmd != 'help':
			print "\nNo login information found."
			print "Please specify options -a -u and -s, or run '%s help configure' to find out how to set login information permanently.\n" % commands.progname
			#print help
			sys.exit()
		
	except ScalrCfgError, e:
		print e 
		sys.exit()

			
	for command in get_commands():
		if cmd == 'help' and len(subargs) == 1 and subargs[0] == command.name:
			print command.usage()
			sys.exit()
			
		if command.name == cmd:
			try:
				obj = command(c, *subargs)
				obj.run()
			except (commands.ScalrError, ScalrAPIError), e:
				print e
			finally:
				sys.exit()
	else:
		print help

if __name__ == '__main__':
	main()