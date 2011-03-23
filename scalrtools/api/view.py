'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from prettytable import PrettyTable
from types_ import FarmRole

class TableViewer:
	
	data = None
	
	def __str__(self):
		return '\n'.join(['%s\n%s\n' % (text,table if isinstance(table, PrettyTable) else '') for table,text in self.data.items()])
	
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
								if isinstance(val, dict):
									value = ';'.join(['%s=%s'%(k,v) for k,v in val.items()])
								else:
									value = val
								plain_text += '\n%s = %s' % (property, value)
						self.data[self.prepare_table(objects)if objects else entry.id] = plain_text
				
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
				self.data[self.prepare_table(objects) if objects else response.total_records] = plain_text
				
	
	def prepare_table(self, objects):		
		column_names = objects[0].__titles__.values()
		pt = PrettyTable(column_names, caching=False)
		
		for scalr_obj in objects:
			row = []
			for attribute in scalr_obj.__titles__.keys():
				cell = getattr(scalr_obj, attribute)
				if isinstance(cell, list):
					cell = ';'.join(cell)
				elif isinstance(cell, dict):
					cell = ';'.join(['%s=%s'%(k,v) for k,v in cell.items()])
				row.append(cell)
			pt.add_row(row)
		return pt