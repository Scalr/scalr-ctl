__author__ = 'shaitanich'


import pytest

import os
import json
import xml.etree.ElementTree as ET


def test_images_group_help(runner):
    help_output = runner.invoke("images", "--help")[0]
    assert "get" in help_output
    assert "list" in help_output


def test_images_list_help(runner):
    help_output = runner.invoke("images", "list", "--help")[0]
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
    assert "architecture" in help_output
    assert "cloudImageId" in help_output
    assert "cloudInitInstalled" in help_output
    assert "cloudLocation" in help_output
    assert "cloudPlatform" in help_output
    assert "deprecated" in help_output
    assert "id" in help_output
    assert "name" in help_output
    assert "os" in help_output
    assert "scalrAgentInstalled" in help_output
    assert "scope" in help_output
    assert "source" in help_output
    assert "status" in help_output
    # --columns
    assert "lastUsed" in help_output
    assert "size" in help_output
    assert "statusError" in help_output
    assert "type" in help_output
    assert "--columns" in help_output
    assert "added" in help_output


def test_os_get_help(runner):
    help_output = runner.invoke("images", "get", "--help")[0]
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

    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "image.json")
    image_object = open(json_path, "r").read()
    print image_object

    #POST
    register_output = runner.invoke_with_input(image_object, "images", "register", "--stdin")[0]
    print register_output
    new_image = json.loads(register_output)["data"]
    new_image["name"] = "pecha_image_test"
    
    #UPDATE
    update_output = runner.invoke_with_input(image_object, "images", "update", "--stdin")[0]
    updated_image = json.loads(update_output)["data"]
    assert updated_image["name"] == "pecha_image_test"

    #DELETE
    delete_output = runner.invoke(image_object, "images", "delete", imageId=new_image["id"])[0]
    assert "deleted" in delete_output

def _test_os_list(runner):

    list_output = runner.invoke("images", "list")[0]
    assert "cloudImageId" in list_output
    assert "cloudLocation" in list_output

    limited_json_output = runner.invoke("images", "list", "--json", max_results=1)[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 1

    paginated_json_output = runner.invoke("images", "list", "--json", max_results=1, page_number=2)[0]
    json_data = json.loads(paginated_json_output)
    assert json_data
    assert "pagination" in json_data
    assert len(json_data["data"]) == 1
    assert "next" in paginated_json_output and "?maxResults=1&pageNum=3" in paginated_json_output

    xml_list_output = runner.invoke("images", "list", "--xml")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def _test_os_get(runner):

    get_output = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    assert "946ba629-a2f0-912f-59db-ba5506e230f4" in get_output
    assert "base64-windows2008-18-07-2013" in get_output

    limited_json_output = runner.invoke("images", "get", "--json", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 18
    assert "id" in json_data["data"]
    assert "946ba629-a2f0-912f-59db-ba5506e230f4" == json_data["data"]["id"]

    xml_list_output = runner.invoke("images", "get", "--xml", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag

    result = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-ba5506e230f5")
    assert "Requested Image either does not exist or is not owned by environment scope." in result[1]
    assert result[2] > 0

    result = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-FAKE")
    assert "Invalid value for imageId" in result[1]
    assert result[2] > 0

