__author__ = 'shaitanich'


import pytest

import json
import xml.etree.ElementTree as ET


def test_os_group_help(runner):
    help_output = runner.invoke("os", "--help")[0]
    assert "get" in help_output
    assert "list" in help_output


def test_os_list_help(runner):
    help_output = runner.invoke("os", "list", "--help")[0]
    assert "--envId" in help_output
    assert "--max-results" in help_output
    assert "--page-number" in help_output
    assert "--tree" in help_output
    assert "--nocolor" in help_output
    assert "--json" in help_output
    assert "--xml" in help_output
    assert "--table" in help_output
    assert "--debug" in help_output
    # --filters
    assert "--filters" in help_output
    assert "family" in help_output
    assert "generation" in help_output
    assert "id" in help_output
    assert "name" in help_output
    assert "version" in help_output
    assert "--columns" in help_output
    # --columns
    assert "version" in help_output


def test_os_get_help(runner):
    help_output = runner.invoke("os", "get", "--help")[0]
    assert "--envId" in help_output
    assert "--tree" in help_output
    assert "--nocolor" in help_output
    assert "--json" in help_output
    assert "--xml" in help_output
    assert "--debug" in help_output
    assert "--table" not in help_output


def test_crud(runner):
    _test_os_list(runner)
    _test_os_get(runner)


def _test_os_list(runner):
    list_output = runner.invoke("os", "list")[0]
    assert "centos" in list_output
    assert "ubuntu" in list_output

    limited_json_output = runner.invoke("os", "list", "--json", max_results=1)[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 1

    paginated_json_output = runner.invoke("os", "list", "--json", max_results=1, page_number=2)[0]
    json_data = json.loads(paginated_json_output)
    assert json_data
    assert "pagination" in json_data
    assert len(json_data["data"]) == 1
    assert "next" in paginated_json_output and "?maxResults=1&pageNum=3" in paginated_json_output

    xml_list_output = runner.invoke("os", "list", "--xml")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def _test_os_get(runner):
    get_output = runner.invoke("os", "get", osId="ubuntu-14-04")[0]
    assert "ubuntu-14-04" in get_output
    assert "Trusty" in get_output

    limited_json_output = runner.invoke("os", "get", "--json", osId="ubuntu-14-04")[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 5
    assert "id" in json_data["data"]
    assert "ubuntu-14-04" == json_data["data"]["id"]

    xml_list_output = runner.invoke("os", "get", "--xml", osId="ubuntu-14-04")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag

    result = runner.invoke("os", "get", osId="ubuntu-14-05")
    assert "Unable to find requested OS" in result[1]
    assert result[2] > 0