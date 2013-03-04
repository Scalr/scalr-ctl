__author__ = 'Dmytro Korsakov'


import unittest
import os

from scalrtools.api import ScalrConnection


class TestScalrConnection(unittest.TestCase):


	def setUp(self):
		scalr_url = os.environ['SCALR_URL']
		key_id = os.environ['SCALR_KEY_ID']
		api_key = os.environ['SCALR_API_KEY']
		self.conn = ScalrConnection(url=scalr_url, key_id=key_id, access_key=api_key, api_version='2.3.0')


	def tearDown(self):
		pass

def _test_fetch_from_local_v4(self):

	response = self.conn.fetch('ServerGetExtendedInformation', ServerID='ef883132-69be-4643-a705-0d2df10b2edd')
	print response.toprettyxml()
	file = open('test/resources/ServerGetExtendedInformationResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()


def _test_fetch_from_local_v3(self):

	response = self.conn.fetch('FarmGetDetails', FarmID='74')
	print response.toprettyxml()
	file = open('test/resources/FarmGetDetailsResponse_local.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DmApplicationCreate', Name='test_app_1', SourceID='4')
	print response.toprettyxml()
	file = open('test/resources/DmApplicationCreateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()


	response = self.conn.fetch('DmSourceCreate', Type='svn', URL='https://pics-hunter.googlecode.com/svn/trunk/', AuthLogin='shaitanich@gmail.com', AuthPassword='Gf2SN5wR9Fr8')
	print response.toprettyxml()
	file = open('test/resources/DmSourceCreateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()



def _test_fetch_from_scalr_test_v3(self):
	response = self.conn.fetch('DmSourcesList')
	print response.toprettyxml()
	file = open('test/resources/DmSourcesListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DmApplicationsList')
	print response.toprettyxml()
	file = open('test/resources/DmApplicationsListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DmSourceCreate', Type='svn', URL='https://pics-hunter.googlecode.com/svn/trunk/', AuthLogin='shaitanich@gmail.com', AuthPassword='Gf2SN5wR9Fr8')
	print response.toprettyxml()
	file = open('test/resources/DmSourceCreateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

def _test_fetch_from_local(self):

	response = self.conn.fetch('DNSZoneRecordRemove', ZoneName='dima-test.com', RecordID='110')
	print response.toprettyxml()
	file = open('test/resources/DNSZoneRecordRemoveResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DNSZoneRecordAdd', ZoneName='dima-test.com', Type='CNAME', TTL='14400', Name='www', Value='dima-test.com')
	print response.toprettyxml()
	file = open('test/resources/DNSZoneRecordAddResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DNSZoneCreate', DomainName='dima-test.com', FarmID='74', FarmRoleID='809')
	print response.toprettyxml()
	file = open('test/resources/DNSZoneCreateResponse.xml','w')
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

	response = self.conn.fetch('ApacheVhostsList')
	print response.toprettyxml()
	file = open('test/resources/ApacheVhostsListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ScriptGetDetails', ScriptID='46')
	print response.toprettyxml()
	file = open('test/resources/ScriptGetDetailsResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('BundleTaskGetStatus', BundleTaskID='578')
	print response.toprettyxml()
	file = open('test/resources/BundleTaskGetStatusResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('RolesList', Name='euca2-base')
	print response.toprettyxml()
	file = open('test/resources/RolesListResponse.xml','w')
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


def _test_fetch_from_scalr_test(self):

	response = self.conn.fetch('ServerTerminate', ServerID='1f72ece7-e732-4bfc-8d97-a9e0a4014946',DecreaseMinInstancesSetting='0')
	print response.toprettyxml()
	file = open('test/resources/ServerTerminateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ServerReboot', ServerID='1f72ece7-e732-4bfc-8d97-a9e0a4014946')
	print response.toprettyxml()
	file = open('test/resources/ServerRebootResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ServerLaunch', FarmRoleID='16353')
	print response.toprettyxml()
	file = open('test/resources/ServerlaunchResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ServerImageCreate', ServerID='1f72ece7-e732-4bfc-8d97-a9e0a4014946', RoleName='app-apache-ubuntu-ebs')
	print response.toprettyxml()
	file = open('test/resources/ServerImageCreateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ScriptExecute', FarmID='5365', ScriptID='348',Timeout='60',Async='0')
	print response.toprettyxml()
	file = open('test/resources/ScriptExecuteResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	ssl_private_key = open('test/resources/apache-cert/server.key').read()
	key = binascii.b2a_base64(ssl_private_key).strip()

	ssl_certificate = open('test/resources/apache-cert/server.crt').read()
	cert = binascii.b2a_base64(ssl_certificate).strip()

	response = self.conn.fetch('ApacheVhostCreate', DomainName='ssl.dima-test.com', FarmID='5365',
	                           FarmRoleID='16353',DocumentRootDir='/var/www',EnableSSL='1',
	                           SSLPrivateKey=key,SSLCertificate=cert)
	print response.toprettyxml()
	file = open('test/resources/ApacheVhostCreateResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()


def _test_fetch_from_scalr_test_v2(self):
	response = self.conn.fetch('EnvironmentsList')
	print response.toprettyxml()
	file = open('test/resources/EnvironmentsListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()


def _test_fetch_from_scalr_test_v3(self):
	response = self.conn.fetch('FarmRoleUpdateParameterValue', FarmRoleID='44049', ParamName='var1', ParamValue='val0001')
	print response.toprettyxml()
	file = open('test/resources/FarmRoleUpdateParameterValueResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('ScriptingLogsList', FarmID='5365')
	print response.toprettyxml()
	file = open('test/resources/ScriptingLogsListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('FarmRoleParametersList', FarmRoleID='44049')
	print response.toprettyxml()
	file = open('test/resources/FarmRoleParametersListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()


def _test_fetch_from_scalr_admin(self):
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

	response = self.conn.fetch('DNSZoneRecordsList', ZoneName='6ea60dba-a7a9-46cd-81ea-c62c74699951.scalr.ws')
	print response.toprettyxml()
	file = open('test/resources/DNSZoneRecordsListResponse.xml','w')
	file.write(response.toprettyxml())
	file.close()

	response = self.conn.fetch('DNSZonesList')
	print response.toprettyxml()
	file = open('test/resources/DNSZonesListResponse.xml','w')
	file.write(response.toprettyxml())

