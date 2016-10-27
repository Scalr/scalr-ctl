__author__ = 'Dmitriy Korsakov'

import json
import xml.etree.ElementTree as ET


def test_os_group_help(runner):
    help_output = runner.invoke("os", "--help")[0]
    for item in ("get", "list"):
        assert item in help_output


def test_os_list_help(runner):
    help_output = runner.invoke("os", "list", "--help")[0]
    for item in ("--envId", "--max-results", "--page-number", "--tree",
                 "--nocolor", "--json", "--xml", "--table", "--debug"):
        assert item in help_output


def test_os_list_help_filters(runner):
    # --filters
    help_output = runner.invoke("os", "list", "--help")[0]
    for item in ("--filters", "family", "generation", "id", "name", "version", "--columns"):
        assert item in help_output


def test_os_list_help_columns(runner):
    # --columns
    help_output = runner.invoke("os", "list", "--help")[0]
    assert "--columns" in help_output


def test_os_get_help(runner):
    help_output = runner.invoke("os", "get", "--help")[0]
    for item in ("--envId", "--tree", "--nocolor", "--json", "--xml", "--debug"):
        assert item in help_output
    assert "--table" not in help_output


def test_os_list(runner):
    list_output = runner.invoke("os", "list")[0]
    for item in ("centos", "ubuntu"):
        assert item in list_output


def test_os_list_json(runner):
    limited_json_output = runner.invoke("os", "list", "--json", max_results=1)[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 1


def test_os_list_pagination(runner):
    paginated_json_output = runner.invoke("os", "list", "--json", max_results=1, page_number=2)[0]
    json_data = json.loads(paginated_json_output)
    assert json_data
    assert "pagination" in json_data
    assert len(json_data["data"]) == 1
    assert "next" in paginated_json_output and "?maxResults=1&pageNum=3" in paginated_json_output


def test_os_list_xml(runner):
    xml_list_output = runner.invoke("os", "list", "--xml")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_os_get(runner):
    get_output = runner.invoke("os", "get", osId="ubuntu-14-04")[0]
    assert "ubuntu-14-04" in get_output
    assert "Trusty" in get_output


def test_os_get_json(runner):
    limited_json_output = runner.invoke("os", "get", "--json", osId="ubuntu-14-04")[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 5
    assert "id" in json_data["data"]
    assert "ubuntu-14-04" == json_data["data"]["id"]


def test_os_get_xml(runner):
    xml_list_output = runner.invoke("os", "get", "--xml", osId="ubuntu-14-04")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_os_get_notfound(runner):
    result = runner.invoke("os", "get", osId="ubuntu-14-05")
    assert "Unable to find requested OS" in result[1]
    assert result[2] > 0
