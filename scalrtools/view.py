'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from prettytable import PrettyTable
from .types import FarmRole

#TODO: Refactoring 
class TableViewer:
	
	data = None
	
	def __str__(self):
		return '\n'.join(['%s\n%s\n' % (text,table) for table,text in self.data.items()])
	
	def __init__(self, response):
		
		self.data = {}
		
		if response:
				
			if isinstance(response, list):
				if isinstance(response[0], FarmRole):
					for entry in response:
						objects = entry.server_set
						plain_text = ''
						for property in entry.__titles__:
							val = getattr(entry, property)
							if property != 'server_set' and val:
								plain_text += '\n%s=%s' % (property, val)
						
						self.data[self.prepare_table(objects)] = plain_text
				
				else:
					objects = response
					plain_text = ''
					self.data[self.prepare_table(objects)] = plain_text
				
			else:
				objects = response.scalr_objects
				plain_text = 'Total records: %s\nStart:%s\nLimit:%s\n' % (
						response.total_records, 
						response.start_from, 
						response.records_limit)
				
				self.data[self.prepare_table(objects)] = plain_text
				
	
	def prepare_table(self, objects):			
			column_names = objects[0].__titles__.values()
			
			pt = PrettyTable(column_names, caching=False)
			
			for scalr_obj in objects:
				row = []
				for attribute in scalr_obj.__titles__.keys():
					cell = getattr(scalr_obj, attribute)
					row.append(';'.join(cell) if isinstance(cell, list) else cell)
				pt.add_row(row)
			return pt