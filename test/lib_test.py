'''
Created on Feb 21th, 2011

@author: Dmytro Korsakov
'''

import unittest

from xml.dom.minidom import parseString

from lib import ScalrConnection, xml_strip, ScalrAPIError
from viewer import TableViewer

key_id = '2f8c90dd4cbd948f'
scalr_url='https://scalr-trunk.local.webta.net/api/api.php'
api_key = '+gxTjaN5b1jRcAsnc8vYZr3GObFM2b+tFE8Gx0rABntyhCTZhgW1oeVtAR350gmA8mUSLXQwinFnE+zjmb9P7usCAjZztWArWxIPymTbBg4Xv65ZxAYqebvZE73icQa40vmjI2U+X/DVPt531OpQfuoSxMT1Id6QkQJOhdgre0s='

#scalr.net
#key_id = '24cce3d24a4339d7'
#api_key = 'pLaNwKz4l4z9g5+SN3F7MQcy9IvzgxGF7pc03gUqaOwT91oJeTU0iU+af8k6eHVoi/Ykg5/5dCA5e8s0JRIQcsgte4eyryFxhO5Si4XNCHAntKy1VBYRn8wu79zvdZPV6S68ZAvl5B8MpWYRyg3yAzo8wgJZnH3MAozgWN+zVG4='
#scalr_url = 'https://scalr.net/api/api.php'


class TestScalrConnection(unittest.TestCase):


	def setUp(self):
		self.conn = ScalrConnection(url=scalr_url, key_id=key_id, access_key=api_key)


	def tearDown(self):
		pass


	def test_error_response(self):
		response = open('test/resources/Error.xml').read()
		xml = xml_strip(parseString(response))
		self.assertRaises(ScalrAPIError,self.conn._read_get_farm_stats_response,(xml))
		#print self.conn._read_get_farm_stats_response(xml)


	def test__read_get_farm_details_response(self):
		response = open('test/resources/FarmGetDetailsResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_get_farm_details_response(xml)
		
		farm_role = response[-1]
		
		self.assertEqual(len(response), 1)
		
		self.assertEquals(farm_role.id, '6150')
		self.assertEquals(farm_role.role_id, '7571')
		self.assertEquals(farm_role.name, 'scalr-wiki-20090717')
		self.assertEquals(farm_role.platform, 'ec2')
		self.assertEquals(farm_role.category, 'Application servers')
		self.assertEquals(farm_role.cloud_location, 'us-east-1')
		'''
		platform_properties = None
		mysql_properties = None
		scaling_properties = None
		'''
		
		server = farm_role.server_set[-1]
		
		self.assertEquals(server.server_id, 'caf1ab8f-e87c-47a5-be87-e090605362ab')
		self.assertEquals(server.external_ip, '174.129.1.171')
		self.assertEquals(server.internal_ip, '10.244.131.246')
		self.assertEquals(server.status, 'Running')
		self.assertEquals(server.scalarizr_version, '0.2-115')
		self.assertEquals(server.uptime, '853021.73')
		'''
		platform_properties = None
		'''
		self.assertEquals(self.conn.last_transaction_id, 'bfac9fb6-598f-413b-a870-ea1ff281d658')

		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		
		
	def test__read_get_statistic_graph_URL_response(self):
		response = open('test/resources/StatisticsGetGraphURLResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_get_statistic_graph_URL_response(xml)	
		
		self.assertEqual(len(response), 1)
		
		url = response[-1]
		
		self.assertEquals(url.graph_url, 'https://monitoring-graphs.scalr.net/1997/FARM_CPUSNMP.monthly.gif')
		self.assertEquals(self.conn.last_transaction_id, '3b810214-47a6-4b63-a5d8-c0fcbc624936')	
			
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)		
		

	def test__read_terminate_farm_response(self):
		response = open('test/resources/FarmTerminateResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_terminate_farm_response(xml)	
		
		self.assertEqual(len(response), 1)
		
		result = response[-1]
		
		self.assertEquals(result.result, '1')
		self.assertEquals(self.conn.last_transaction_id, 'c7a43c70-29b5-4aa4-be8d-0a2bcfc186b4')	
			
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)			
		
		
	def test__read_launch_farm_response(self):
		response = open('test/resources/FarmLaunchResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_launch_farm_response(xml)	
		
		self.assertEqual(len(response), 1)
		
		result = response[-1]
		
		self.assertEquals(result.result, '1')
		self.assertEquals(self.conn.last_transaction_id, '3228387f-c988-4b11-80fb-03b4bda2be0b')	
			
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)			
		
		
	def test__read_get_bundle_task_status_response(self):
		response = open('test/resources/BundleTaskGetStatusResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_get_bundle_task_status_response(xml)
		
		self.assertEqual(len(response), 1)
		
		bundle_task = response[-1]
		
		self.assertEquals(bundle_task.bundle_task_status, 'failed')
		self.assertEquals(bundle_task.failure_reason, 'Received RebundleFailed event from server')
		self.assertEquals(self.conn.last_transaction_id, 'e8dd0efe-7e6b-4199-82ab-69fd8f8f0e03')	
			
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		
				
	def test__read_get_script_details_response(self):
		response = open('test/resources/ScriptGetDetailsResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_get_script_details_response(xml)

		self.assertEqual(len(response), 2)
		
		script_revision = response[-1]
		
		self.assertEquals(script_revision.date, '2011-02-14 12:03:01')
		self.assertEquals(script_revision.revision, '2')
		vars = ['svn_repo_url', 'svn_user', 'svn_password', 'svn_revision', 'svn_co_dir']
		#self.assertEquals(script_revision.config_variables, vars)
		self.assertEquals(self.conn.last_transaction_id, '52a6032e-143e-47b2-aaf1-53a7d09e0c39')

		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)


	def test__read_get_farm_stats_response(self):
		response = open('test/resources/FarmGetStatsResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_get_farm_stats_response(xml)
		
		self.assertEqual(len(response), 20)
		
		farm_stat = response[-1]
		
		self.assertEquals(farm_stat.year, '2009')
		self.assertEquals(farm_stat.month, '6')
		self.assertEquals(farm_stat.bandwidth_in, '185.49')
		self.assertEquals(farm_stat.bandwidth_out, '389.34')
		self.assertEquals(farm_stat.bandwidth_total, '574')
		self.assertEquals(self.conn.last_transaction_id, '87ff0e00-20bb-4827-99f7-65e2952b187b')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)


	def test__read_logs_list_response(self):
		response = open('test/resources/LogsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_logs_list_response(xml)
		
		self.assertEqual(len(response.scalr_objects), 8)
		
		log_record = response.scalr_objects[-1]
		
		self.assertEquals(response.total_records, '8')
		self.assertEquals(response.start_from, '0')
		self.assertEquals(response.records_limit, '20')
		self.assertEquals(log_record.source, 'scalarizr')
		self.assertEquals(log_record.time_stamp, '02.16.2011 19:15:18')
		self.assertEquals(log_record.server_id, '0746ee9b-8ea0-4274-ae98-1996dcc971cc')
		self.assertEquals(log_record.message, '[pid: 1544] Starting scalarizr 0.7.11')
		self.assertEquals(log_record.severity, 'info')
		self.assertEquals(self.conn.last_transaction_id, '9e23447e-0e0d-4e9f-9a18-4dc7d2831269')

		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		

	def test__read_event_list_response(self):
		response = open('test/resources/EventsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_events_list_response(xml)
		
		self.assertEqual(len(response.scalr_objects), 20)
		
		event = response.scalr_objects[-1]
		
		self.assertEquals(response.total_records, '1088')
		self.assertEquals(response.start_from, '0')
		self.assertEquals(response.records_limit, '20')
		self.assertEquals(event.time_stamp, '01.31.2011 18:03:40')
		self.assertEquals(event.message, 'Farm launched')
		self.assertEquals(event.id, 'aab603a5-63c4-46b9-a9b0-52ea5d09a3fe')
		self.assertEquals(event.type, 'FarmLaunched')
		self.assertEquals(self.conn.last_transaction_id, 'cbda9e6a-cc0b-4c72-8f94-9fdda0b54667')
				
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
			
	
	def test__read_dns_zone_record_list_response(self):
		response = open('test/resources/DNSZoneRecordsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_dns_zone_record_list_response(xml)
		
		self.assertEqual(len(response), 2)
		
		dns_zone_record = response[-1]
	
		self.assertEquals(dns_zone_record.id, '24')
		self.assertEquals(dns_zone_record.type, 'A')
		self.assertEquals(dns_zone_record.ttl, '14400')
		self.assertEquals(dns_zone_record.priority, '0')
		self.assertEquals(dns_zone_record.name, 'sdfsd')
		self.assertEquals(dns_zone_record.value, '10.5.6.7')
		self.assertEquals(dns_zone_record.weight, '0')
		self.assertEquals(dns_zone_record.port, '0')
		self.assertEquals(dns_zone_record.is_system, '0')
		self.assertEquals(self.conn.last_transaction_id, 'dd44f028-9b32-4575-b0e9-4bb12f85cab2')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
				
				
	def test__read_roles_list_response(self):
		response = open('test/resources/RolesListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_roles_list_response(xml)
		
		self.assertEqual(len(response), 1)

		role_set = response[-1]
	
		self.assertEquals(role_set.owner, 'Jake Merge')
		self.assertEquals(role_set.name, 'euca2-base')
		self.assertEquals(role_set.architecture, 'x86_64')
		self.assertEquals(self.conn.last_transaction_id, '49b94cb7-1013-4c2e-bd6e-03aac07d0259')

		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)		
	
	
	def test__read_apache_virtual_host_list_response(self):
		response = open('test/resources/ApacheVhostsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_apache_virtual_host_list_response(xml)
		
		self.assertEqual(len(response), 1)

		virtual_host = response[-1]

		self.assertEquals(virtual_host.name, None)
		self.assertEquals(virtual_host.farm_id, '74')
		self.assertEquals(virtual_host.farm_role_id, '809')
		self.assertEquals(virtual_host.is_ssl_enabled, '1')
		self.assertEquals(virtual_host.last_modified_at, '2011-02-01 19:53:16')		
		self.assertEquals(self.conn.last_transaction_id, 'f963ce69-0833-40ca-98fc-f07ecd02dcc5')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		
		
	def test__read_dns_zones_list_response(self):
		response = open('test/resources/DNSZonesListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_dns_zones_list_response(xml)
		
		self.assertEqual(len(response), 1)

		dns_zone = response[-1]

		self.assertEquals(dns_zone.zone_name, 'sdfsdfdsfsdfsd.com')
		self.assertEquals(dns_zone.farm_id, '30')
		self.assertEquals(dns_zone.farm_role_id, '109')
		self.assertEquals(dns_zone.status, 'Pending update')
		self.assertEquals(dns_zone.last_modified_at, '2011-02-09 18:13:33')		
		self.assertEquals(dns_zone.ip_set, None)
		self.assertEquals(self.conn.last_transaction_id, '164fc460-3eb2-43a7-8c93-2812ccae3add')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)


	def test__read_scripts_list_response(self):
		response = open('test/resources/ScriptsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_scripts_list_response(xml)
		
		self.assertEqual(len(response), 12)
		
		script = response[-1]

		self.assertEquals(script.name, 'Custom artemScript')
		self.assertEquals(script.id, '48')
		self.assertEquals(script.latest_revision, '2')		
		self.assertEquals(script.description, 'Clone a git repository')
		self.assertEquals(self.conn.last_transaction_id, '72e2f745-9e9d-4d27-a750-a590c6dc6f1d')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		

	def test__read_farms_list_response(self):
		response = open('test/resources/FarmsListResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_farms_list_response(xml)
		
		self.assertEqual(len(response), 11)
		
		farm = response[-1]

		self.assertEquals(farm.name, 'Nimbula test farm')
		self.assertEquals(farm.id, '79')
		self.assertEquals(farm.comments, 'test')		
		self.assertEquals(farm.status, '1')
		self.assertEquals(self.conn.last_transaction_id, '48aef2cb-edf5-4101-ba1a-fbdb99f8543d')
		
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		
	
			
	def test_fetch(self):
		pass
	
		'''
		response = self.conn.fetch('FarmGetDetails', FarmID='1997')
		print response.toprettyxml()
		file = open('test/resources/FarmGetDetailsResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()		
		
		response = self.conn.fetch('StatisticsGetGraphURL', ObjectType='farm', ObjectID='1997', WatcherName='CPU',GraphType='monthly')
		print response.toprettyxml()
		file = open('test/resources/StatisticsGetGraphURLResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()	
	
		response = self.conn.fetch('FarmTerminate', FarmID='74',KeepEBS='0',KeepEIP='0',KeepDNSZone='0')
		print response.toprettyxml()
		file = open('test/resources/FarmTerminateResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()	
	
		response = self.conn.fetch('FarmLaunch', FarmID='74')
		print response.toprettyxml()
		file = open('test/resources/FarmLaunchResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
	
		response = self.conn.fetch('BundleTaskGetStatus', BundleTaskID='578')
		print response.toprettyxml()
		file = open('test/resources/BundleTaskGetStatusResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('ScriptGetDetails', ScriptID='46')
		print response.toprettyxml()
		file = open('test/resources/ScriptGetDetailsResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
			
		response = self.conn.fetch('LogsList', FarmID='2607')
		print response.toprettyxml()
		file = open('test/resources/LogsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()	

		response = self.conn.fetch('FarmGetStats', FarmID='1997')
		print response.toprettyxml()
		file = open('test/resources/FarmGetStatsResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
			
		response = self.conn.fetch('LogsList', FarmID='74', ServerID='d3963f4b-8f26-4d37-aefc-bcfe83fe998a')
		print response.toprettyxml()
		file = open('test/resources/LogsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
			
		response = self.conn.fetch('EventsList', FarmID='74')
		print response.toprettyxml()
		file = open('test/resources/EventsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
			
		response = self.conn.fetch('DNSZoneRecordsList', ZoneName='6ea60dba-a7a9-46cd-81ea-c62c74699951.scalr.ws')
		print response.toprettyxml()
		file = open('test/resources/DNSZoneRecordsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('RolesList', Name='euca2-base')
		print response.toprettyxml()
		file = open('test/resources/RolesListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('ApacheVhostsList')
		print response.toprettyxml()
		file = open('test/resources/ApacheVhostsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('DNSZonesList')
		print response.toprettyxml()
		file = open('test/resources/DNSZonesListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('ScriptsList')
		print response.toprettyxml()
		file = open('test/resources/ScriptsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		
		response = self.conn.fetch('FarmsList')
		print response.toprettyxml()
		file = open('test/resources/FarmsListResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		'''
		
		
		'''		
		response = self.conn.fetch('Serverlaunch',FarmRoleID='') #TODO:Add valid FarmRoleID
		print response.toprettyxml()
		file = open('test/resources/ServerlaunchResponse.xml','w')
		file.write(response.toprettyxml())
		file.close()
		'''
	
	
	'''	
	def __test__read_launch_server_response(self):
		response = open('test/resources/ServerlaunchResponse.xml').read()
		xml = xml_strip(parseString(response))
		response = self.conn._read_launch_server_response(xml)
		print '\nLast TransactionID: %s' % self.conn.last_transaction_id
		print TableViewer(response)
		#self.assertEquals()
	'''			
				
				
if __name__ == "__main__":
	unittest.main()


'''
<?xml version="1.0" ?>
<BundleTaskGetStatusResponse>
	<TransactionID>
		7a65bcad-d182-4531-be21-f63a334ec1d1
	</TransactionID>
	<BundleTaskStatus>
		success
	</BundleTaskStatus>
</BundleTaskGetStatusResponse>
'''

'''
<?xml version="1.0" ?>
<BundleTaskGetStatusResponse>
	<TransactionID>
		e8dd0efe-7e6b-4199-82ab-69fd8f8f0e03
	</TransactionID>
	<BundleTaskStatus>
		failed
	</BundleTaskStatus>
	<FailureReason>
		Received RebundleFailed event from server
	</FailureReason>
</BundleTaskGetStatusResponse>
'''