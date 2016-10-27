__author__ = 'Dmitriy Korsakov'

import yaml

import os
import json
import xml.etree.ElementTree as ET


def test_scripts_group_help(runner):
    help_output = runner.invoke("scripts", "--help")[0]
    for item in ("create", "delete", "get", "list", "get-orchestration-log", "update", "status"):
        assert item in help_output


def test_scripts_list_help(runner):
    help_output = runner.invoke("scripts", "list", "--help")[0]
    for item in ("--envId", "--max-results", "--page-number", "--tree",
                 "--nocolor", "--json", "--xml", "--table", "--debug"):
        assert item in help_output


def test_scripts_list_help_filters(runner):
    # --filters
    help_output = runner.invoke("scripts", "list", "--help")[0]
    for item in ("--filters", "blockingDefault", "id", "name", "osType", "scope"):
        assert item in help_output


def test_scripts_list_help_columns(runner):
    # --columns
    help_output = runner.invoke("scripts", "list", "--help")[0]
    for item in ("added", "blockingDefault", "description", "id", "--columns",
                 "lastChanged", "name", "osType", "scope", "timeoutDefault"):
        assert item in help_output


def test_scripts_get_help(runner):
    help_output = runner.invoke("scripts", "get", "--help")[0]
    for item in ("--envId", "--tree", "--nocolor", "--json", "--xml", "--debug", "--scriptId"):
        assert item in help_output
    assert "--table" not in help_output


def test_scripts_list(runner):
    list_output = runner.invoke("scripts", "list")[0]
    for item in ("blockingDefault", "timeoutDefault"):
        assert item in list_output


def test_scripts_list_json(runner):
    limited_json_output = runner.invoke("scripts", "list", "--json", max_results=1)[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 1


def test_scripts_list_pagination(runner):
    paginated_json_output = runner.invoke("scripts", "list", "--json", max_results=1, page_number=2)[0]
    json_data = json.loads(paginated_json_output)
    assert json_data
    assert "pagination" in json_data
    assert len(json_data["data"]) == 1
    assert "next" in paginated_json_output and "?maxResults=1&pageNum=3" in paginated_json_output


def test_scripts_list_xml(runner):
    xml_list_output = runner.invoke("scripts", "list", "--xml")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_scripts_get(runner):
    get_output = runner.invoke("scripts", "get", scriptId="2")[0]
    assert "echo hello world" in get_output


def test_scripts_get_json(runner):
    limited_json_output = runner.invoke("scripts", "get", "--json", scriptId="2")[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 9
    assert "id" in json_data["data"]
    assert 2 == json_data["data"]["id"]


def test_scripts_get_xml(runner):
    xml_list_output = runner.invoke("scripts", "get", "--xml", scriptId="2")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_scripts_get_notfound(runner):
    result = runner.invoke("scripts", "get", scriptId="20000")
    assert "Requested Script either does not exist or is not owned by your environment." in result[1]
    assert result[2] > 0


def test_scripts_get_misformed(runner):
    result = runner.invoke("scripts", "get", scriptId="22-22")
    assert "The endpoint you are trying to access does not exist." in result[1]
    assert result[2] > 0


def test_scripts_create_delete(runner):
    script_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.json")
    script_object = open(script_json_path, "r").read()

    #POST
    create_output, err, retcode = runner.invoke_with_input(script_object, "scripts", "create", "--stdin")
    new_script = yaml.load(create_output)

    #UPDATE
    updated_script_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script_updated.json")
    updated_script_object = open(updated_script_json_path, "r").read()

    update_output, e, r = runner.invoke_with_input(updated_script_object, "scripts", "update", "--stdin", scriptId=new_script["id"])
    updated_script = yaml.load(update_output)
    assert updated_script["name"] == "pecha_scripting_test"

    #DELETE
    delete_output = runner.invoke(script_object, "scripts", "delete", scriptId="2")[0]
    assert delete_output and "id" in delete_output and delete_output["id" == new_script["id"]]
