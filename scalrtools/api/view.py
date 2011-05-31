'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from prettytable import PrettyTable

class TableViewer:
	
	data = None
	
	def __str__(self):
		return '\n'.join(['%s\n%s\n' % (text,table if isinstance(table, PrettyTable) else '') for table,text in self.data.items()])
	
	def __init__(self, response):
		self.data = {}
		
		if response:
				
			if isinstance(response, list):
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
		
		for field in column_names:
			pt.set_field_align(field, 'l')
		
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