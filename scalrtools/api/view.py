'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

from prettytable import PrettyTable
from types_ import DynamicScalrObject, Page
class TableViewer:
	
	data = None
	
	def __str__(self):
		lines = []
		for table,text in self.data.items():
			line = ''
			
			if text:
				line += '%s\n' % text
				
			if isinstance(table, PrettyTable):
				line += '%s\n' % table
				
			lines.append(line)
		return '\n'.join(lines)
	
	
	def __init__(self, response):
		
		'''
		data = @dict(table=title)
		'''
		self.data = {}
		
		if response:
				
			if isinstance(response, list):
				self.data[self.prepare_table(response)] = None
				
			#for dynamic key-value objects
			elif isinstance(response, DynamicScalrObject):
				pt = PrettyTable([response.__title__, 'Value'])
				for k,v in response.data:
					pt.add_row([k,v])
				self.data[pt] = None
			
			#for paginated objects	
			elif isinstance(response, Page):
				objects = response.scalr_objects
				plain_text = 'Total records: %s\nStart:%s\nLimit:%s\n' % (
						response.total_records, 
						response.start_from, 
						response.records_limit)
				self.data[self.prepare_table(objects) if objects else response.total_records] = plain_text
				

	def apply_aliases(self, column_names, aliases):
		if aliases: 
			
			for key in aliases:
				if key in column_names:
					column_names[column_names.index(key)] = aliases[key]
				
		return column_names
	
	
	def get_column_names(self, objects):
		column_names = []

		if objects:
			object = objects[0]
			column_names = object.__titles__.values()
			aliases = object.__aliases__
		
			return self.apply_aliases(column_names, aliases)
			
		
	def prepare_table(self, objects):		
		column_names = self.get_column_names(objects)
		
		pt = PrettyTable(column_names, caching=False)
		
		#set left allign to all columns
		#prettytable 0.5/0.6 support
		if hasattr(pt, 'align'):
			pt.align = 'l'
		else:
			for field in column_names:
				pt.set_field_align(field, 'l')
		
		#filling the table 
		for scalr_obj in objects:
			row = []
			for attribute in scalr_obj.__titles__.keys():
				cell = getattr(scalr_obj, attribute)
				
				#packing list into cell 
				if isinstance(cell, list):
					cell = ';'.join(cell)
					
				#packing dict into cell	
				elif isinstance(cell, dict):
					cell = ';'.join(['%s=%s'%(k,v) for k,v in cell.items()])
					
				row.append(cell)
			pt.add_row(row)
			
		return pt