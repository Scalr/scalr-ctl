'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

import os
import sys
import inspect
from optparse import OptionParser

import handlers
from scalr_config import Configuration, ScalrCfgError, ScalrEnvError


def split_options(args):
	'''
	@return ([options], subcommand, [args])
	'''
	for arg in args[1:]:
		index = args.index(arg)
		prev = args[args.index(arg)-1]		
		if not arg.startswith('-') and (prev.startswith('-') or index == 1):
			return (args[1:index], arg, args[index+1:])			
	return (args[1:], None, [])

def get_handlers():
	hs = []
	for name, obj in inspect.getmembers(handlers):
		if inspect.isclass(obj) and hasattr(obj, 'subcommand') and getattr(obj, 'subcommand'):
			hs.append(obj)
	return hs

def main():

	subcommands = 'Available subcommands:\n' + '\n'.join([action.subcommand for action in get_handlers()])
	usage='''Usage: scalrtools [options] subcommand [args]'''
	
	parser = OptionParser(usage=usage)
	parser.add_option("-c", "--config-path", dest="base_path", default=None, help="Path to configuration files")
	parser.add_option("-a", "--access-key", dest="key_id", default=None, help="Access key")
	parser.add_option("-s", "--secret-key", dest="key", default=None, help="Secret key")
	parser.add_option("-u", "--api-url", dest="api_url", default=None, help="API URL")
	
	args, cmd, subargs = split_options(sys.argv)

	options = parser.parse_args(args)[0]
	help = parser.format_help() + subcommands
	if not cmd:
		print help
		sys.exit()

	try:
		c = Configuration(options.base_path)
		c.set_environment(options.key, options.key_id, options.api_url)
	except ScalrEnvError, e:
		print "\nNo login information found."
		print "Please specity options -a -u and -s, or run 'scalrtools configure-env help' to find out how to set login information permanently.\n"
		print help
		sys.exit()
		
	except ScalrCfgError, e:
		print e 
		sys.exit()
		
	for action in get_handlers():
		if action.subcommand == cmd:
			obj = action(c, *subargs)
			obj.run()


if __name__ == '__main__':
	main()