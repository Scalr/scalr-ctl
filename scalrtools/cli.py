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
	
	subcommands = '\nAvailable subcommands:\n\n' + '\n'.join(sorted([command.name for command in get_commands()]))
	usage='''Usage: scalrtools [options] subcommand [args]'''
	
	parser = OptionParser(usage=usage)
	parser.add_option("--debug", dest="debug", action="store_true", help="Enable debug output")
	parser.add_option("-c", "--config-path", dest="base_path", default=None, help="Path to configuration files")
	parser.add_option("-a", "--access-key", dest="key_id", default=None, help="Access key")
	parser.add_option("-s", "--secret-key", dest="key", default=None, help="Secret key")
	parser.add_option("-u", "--api-url", dest="api_url", default=None, help="API URL")
	
	args, cmd, subargs = split_options(sys.argv)

	options = parser.parse_args(args)[0]
	help = parser.format_help() + subcommands + "\n\nFor more information try 'scalrtools help <subcommand>'"
	if not cmd:
		print help
		sys.exit()

	try:
		c = Configuration(options.base_path)
		c.set_environment(options.key, options.key_id, options.api_url)
		
		if options.debug:
			c.set_logger(logger)
			
	except ScalrEnvError, e:
		if not cmd.startswith('configure-'):
			print "\nNo login information found."
			print "Please specity options -a -u and -s, or run 'scalrtools configure-env help' to find out how to set login information permanently.\n"
			print help
			sys.exit()
		
	except ScalrCfgError, e:
		print e 
		sys.exit()

			
	for command in get_commands():
		if cmd == 'help' and len(subargs) == 1 and subargs[0] == command.name:
			print command.usage()
			sys.exit()
			
		if command.name == cmd:
			obj = command(c, *subargs)
			obj.run()
			sys.exit()
	else:
		print help

if __name__ == '__main__':
	main()