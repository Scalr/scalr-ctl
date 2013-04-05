__author__ = 'shaitanich'

import os
import sys

PARENTDIR = os.path.join(os.path.realpath(os.path.curdir))
sys.path.insert(0, PARENTDIR)

import unittest
import json
from prettytable import PrettyTable
from xml.etree import ElementTree as ET
from scalrtools.api.core import xml_to_dict


def get_xml_document_root(name):
    path = os.path.join(PARENTDIR, 'test/resources/%s.xml' % name)
    tree = ET.parse(path)
    root = tree.getroot()
    return root


def get_schema(name):
    template_dir = os.path.join(PARENTDIR, 'scalrtools/etc/templates')
    template_path = os.path.join(template_dir, name + '.json')
    json_obj = json.load(open(template_path))
    return json_obj

def get_data(root, schema):
    schema = get_schema(schema)
    root = get_xml_document_root(root)
    args = [root, schema['row_path'], schema['descr'], schema['format']]
    if 'dynamic' in schema and schema['dynamic']:
        args.append(schema['dynamic'])
    data = xml_to_dict(*args)
    return data

def get_table(root, schema):
    data = get_data(root,schema)
    return data['table']

def draw_pretty_table(table):
    column_names = table[0].keys()
    pt = PrettyTable(column_names, caching=False)
    for row in table:
        pt.add_row(row.values())
    print pt


def validate_pagination(data, tr, sf, rl):
    upper_level = data['upper_level']
    assert tr == upper_level['TotalRecords']
    assert sf == upper_level['StartFrom']
    assert rl == upper_level['RecordsLimit']


class TestScalrConnection(unittest.TestCase):


    def test__ApacheVhostListResponse(self):
        table = get_table('ApacheVhostsListResponse', 'Vhost')
        assert len(table) == 1
        assert table[0] == {u'IsSSLEnabled': '1', u'FarmRoleID': '809', u'LastModifiedAt': '2011-02-01 19:53:16', u'Name': None, u'FarmID': '74'}


    def test__ApacheVhostCreateResponse(self):
        table = get_table('ApacheVhostCreateResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__BundleTaskGetStatusResponse(self):
        table = get_table('BundleTaskGetStatusResponse', 'BTStatus')
        assert len(table) == 1
        assert table[0] == {u'BundleTaskStatus': 'failed', u'FailureReason': 'Received RebundleFailed event from server'}


    def test__DmApplicationCreateResponse(self):
        table = get_table('DmApplicationCreateResponse', 'DMCAResult')
        assert len(table) == 1
        assert table[0] == {u'AplicationID': '5'}


    def test__DmSourceCreateResponse(self):
        table = get_table('DmSourceCreateResponse', 'DMCSResult')
        assert len(table) == 1
        assert table[0] == {u'SourceID': '1'}


    def test__DmSourcesListResponse(self):
        table = get_table('DmSourcesListResponse', 'DMCSList')
        assert len(table) == 1
        assert table[0] == {u'URL': 'https://pics-hunter.googlecode.com/svn/trunk/', u'AuthType': 'password', u'Type': 'svn', u'ID': '1'}


    def test__DNSZoneCreateResponse(self):
        table = get_table('DNSZoneCreateResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__DNSZoneRecordAddResponse(self):
        table = get_table('DNSZoneRecordAddResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__DNSZoneRecordRemoveResponse(self):
        table = get_table('DNSZoneRecordRemoveResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__DNSZoneRecordsListResponse(self):
        table = get_table('DNSZoneRecordsListResponse', 'DNSZoneRecord')
        assert len(table) == 2
        assert table[0] == {u'Name': 'test', u'Weight': '0', u'Value': '10.100.10.1', u'Port': '0', u'Priority': '0', u'TTL': '14400', u'IsSystem': '0', u'Type': 'A', u'ID': '25'}


    def test__DNSZonesListResponse(self):
        table = get_table('DNSZonesListResponse', 'DNSZone')
        assert len(table) == 1
        assert table[0] == {u'Status': 'Pending update', u'FarmRoleID': '109', u'LastModifiedAt': '2011-02-09 18:13:33', u'FarmID': '30', u'ZoneName': 'sdfsdfdsfsdfsd.com'}


    def test__EnvironmentsListResponse(self):
        table = get_table('EnvironmentsListResponse', 'Environment')
        assert len(table) == 7
        assert table[0] == {u'ID': '240', u'Name': 'Production'}


    def test__Error(self):
        table = get_table('Error', 'Error')
        assert len(table) == 1
        assert table[0] == {u'Message': "Zone 'dfgdfg' not found in database"}


    def test__EventsListResponse(self):
        data = get_data('EventsListResponse', 'Envent')
        table = data['table']
        assert len(table) == 20
        assert table[0] == {u'Timestamp': '1296584370', u'Message': '8fc51347-8dae-403b-9c5f-f4c2ecedc947(50.16.3.147) Down', u'Type': 'HostDown', u'ID': 'e9034b49-abe0-473c-94fc-7babc0393ea3'}
        validate_pagination(data, '1088','0','20')


    def test__FarmGetStatsResponse(self):
        '''
        nested->base
        '''
        table = get_table('FarmGetStatsResponse', 'FarmStat')
        assert len(table) == 20
        assert table[0] == {u'Statistics/BandwidthOut': '0', u'Year': '2011', u'Statistics/BandwidthIn': '0', u'Statistics/BandwidthTotal': '0', u'Month': '2'}
        #draw_pretty_table(table)


    def test__FarmLaunchResponse(self):
        table = get_table('FarmLaunchResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__FarmsListResponse(self):
        table = get_table('FarmsListResponse', 'Farm')
        assert len(table) == 11
        assert table[0] == {u'Status': '0', u'Name': 'marat@us-west', u'Comments': None, u'ID': '29'}


    def test__FarmTerminateResponse(self):
        table = get_table('FarmTerminateResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__LogsListResponse(self):
        data = get_data('LogsListResponse', 'Log')
        table = data['table']
        assert len(table) == 8
        assert table[0] == {u'Source': 'scalarizr.messaging.p2p.consumer', u'Timestamp': '1297883718', u'ServerID': '0746ee9b-8ea0-4274-ae98-1996dcc971cc', u'Message': 'Build message consumer server on 0.0.0.0:8012', u'Severity': '2'}
        validate_pagination(data, '8','0','20')


    def test__RolesListResponse(self):
        table = get_table('RolesListResponse', 'Role')
        assert len(table) == 1
        assert table[0] == {u'Owner': 'Jake Merge', u'Name': 'euca2-base', u'Architecture': 'x86_64'}


    def test__ScriptExecuteResponse(self):
        table = get_table('ScriptExecuteResponse', 'Result')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__ScriptsListResponse(self):
        table = get_table('ScriptsListResponse', 'Script')
        assert len(table) == 12
        assert table[0] == {u'LatestRevision': '1', u'Description': 'Update a working copy from SVN repository', u'Name': 'SVN update', u'ID': '1'}


    def test__ServerGetExtendedInformationResponse(self):
        table = get_table('ServerGetExtendedInformationResponse', 'Server')
        assert len(table) == 1
        assert dict(table[0]['ServerInfo/']) == {'Status': 'Running', 'Index': '1', 'LocalIP': '10.202.214.200', 'AddedAt': '2011-06-09 12:57:52', 'Platform': 'ec2', 'RemoteIP': '50.19.174.63', 'ServerID': 'ef883132-69be-4643-a705-0d2df10b2edd'}

    def test__ServerImageCreateResponse(self):
        table = get_table('ServerImageCreateResponse', 'Image')
        assert len(table) == 1
        assert table[0] == {u'BundleTaskID': '6410'}


    def test__ServerLaunchResponse(self):
        table = get_table('ServerLaunchResponse', 'ServerLaunch')
        assert len(table) == 1
        assert table[0] == {u'ServerID': '890f1f45-13a8-4d69-9b9f-f5f6c42cd7a6'}


    def test__ServerRebootResponse(self):
        table = get_table('ServerRebootResponse', 'ServerReboot')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__ServerTerminateResponse(self):
        table = get_table('ServerTerminateResponse', 'ServerTerminate')
        assert len(table) == 1
        assert table[0] == {'Result' : '1'}


    def test__StatisticsGetGraphURLResponse(self):
        table = get_table('StatisticsGetGraphURLResponse', 'Statistics')
        assert len(table) == 1
        assert table[0] == {u'GraphURL': 'https://monitoring-graphs.scalr.net/1997/FARM_CPUSNMP.monthly.gif'}


    def test__DmApplicationsListResponse(self):
        table = get_table('DmApplicationsListResponse', 'Application')
        assert len(table) == 0


    def test__ScriptGetDetailsResponse(self):
        table = get_table('ScriptGetDetailsResponse', 'ScriptRevision')
        assert len(table) == 2
        assert table[0]['.//Name'] == [('Name', 'svn_repo_url'), ('Name', 'svn_user'), ('Name', 'svn_password'), ('Name', 'svn_revision'), ('Name', 'svn_co_dir')]


    def setUp(self):
        pass


    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()
