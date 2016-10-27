__author__ = 'Dmitriy Korsakov'

import yaml

import os
import json
import xml.etree.ElementTree as ET


def test_images_group_help(runner):
    help_output = runner.invoke("images", "--help")[0]
    for item in ("copy", "delete", "get", "list", "register", "update"):
        assert item in help_output


def test_images_list_help(runner):
    help_output = runner.invoke("images", "list", "--help")[0]
    for item in ("--envId", "--max-results", "--page-number", "--tree",
                 "--nocolor", "--json", "--xml", "--table", "--debug"):
        assert item in help_output


def test_images_list_help_filters(runner):
    # --filters
    help_output = runner.invoke("images", "list", "--help")[0]
    for item in ("--filters", "architecture", "cloudImageId", "cloudInitInstalled", "cloudLocation", "cloudPlatform",
                 "deprecated", "id", "name", "os", "scalrAgentInstalled", "scope", "source", "status"):
        assert item in help_output


def test_images_list_help_columns(runner):
    # --columns
    help_output = runner.invoke("images", "list", "--help")[0]
    for item in ("lastUsed", "size", "statusError", "type", "--columns", "added"):
        assert item in help_output


def test_images_get_help(runner):
    help_output = runner.invoke("images", "get", "--help")[0]
    for item in ("--envId", "--tree", "--nocolor", "--json", "--xml", "--debug", "--imageId"):
        assert item in help_output
    assert "--table" not in help_output


def test_images_list(runner):
    list_output = runner.invoke("images", "list")[0]
    for item in ("cloudImageId", "cloudLocation"):
        assert item in list_output


def test_images_list_json(runner):
    limited_json_output = runner.invoke("images", "list", "--json", max_results=1)[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 1


def test_images_list_pagination(runner):
    paginated_json_output = runner.invoke("images", "list", "--json", max_results=1, page_number=2)[0]
    json_data = json.loads(paginated_json_output)
    assert json_data
    assert "pagination" in json_data
    assert len(json_data["data"]) == 1
    assert "next" in paginated_json_output and "?maxResults=1&pageNum=3" in paginated_json_output


def test_images_list_xml(runner):
    xml_list_output = runner.invoke("images", "list", "--xml")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_images_get(runner):
    get_output = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    assert "946ba629-a2f0-912f-59db-ba5506e230f4" in get_output
    assert "base64-windows2008-18-07-2013" in get_output


def test_images_get_json(runner):
    limited_json_output = runner.invoke("images", "get", "--json", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    json_data = json.loads(limited_json_output)
    assert json_data
    assert "data" in json_data
    assert len(json_data["data"]) == 18
    assert "id" in json_data["data"]
    assert "946ba629-a2f0-912f-59db-ba5506e230f4" == json_data["data"]["id"]


def test_images_get_xml(runner):
    xml_list_output = runner.invoke("images", "get", "--xml", imageId="946ba629-a2f0-912f-59db-ba5506e230f4")[0]
    root = ET.fromstring(xml_list_output)
    assert "root" == root.tag


def test_images_get_notfound(runner):
    result = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-ba5506e230f5")
    assert "Requested Image either does not exist or is not owned by environment scope." in result[1]
    assert result[2] > 0


def test_images_get_misformed(runner):
    result = runner.invoke("images", "get", imageId="946ba629-a2f0-912f-59db-FAKE")
    assert "Invalid value for imageId" in result[1]
    assert result[2] > 0


def _test_images_create_delete(runner):
    #
    # Does not work due to SCALRCORE-4627
    # ('', 'Error: Missed property cloudLocation.\n', 1)
    #
    image_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.json")
    image_object = open(image_json_path, "r").read()

    #POST
    out, err, retcode = runner.invoke_with_input(image_object, "images", "register", "--stdin")
    print "register:", (out, err, retcode)
    register_output = out
    new_image = yaml.safe_load(register_output)["data"]

    #UPDATE
    updated_image_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_updated.json")
    updated_image_object = open(updated_image_json_path, "r").read()

    update_output = runner.invoke_with_input(updated_image_object, "images", "update", "--stdin")[0]
    updated_image = yaml.safe_load(update_output)["data"]
    assert updated_image["name"] == "pecha_image_test"

    #DELETE
    delete_output = runner.invoke(image_object, "images", "delete", imageId=new_image["id"])[0]
    assert "deleted" in delete_output
