import pytest

from wikiloc_cim_data import (
    select_routes_from_list,
    get_cims_list,
    _filter_by_html_tag,
    get_cim_routes_list,
)

from bs4.element import Tag, ResultSet


def open_file(path):
    with open(path) as f:
        return f.read()


TEST_PAGE = open_file("./tests/testing_html_pages/wikiloc.html")
ROUTES_TAG = "div.main__results:nth-child(2)"
TITLE_TAG = open_file("./tests/testing_html_pages/title_tag.html")
CIM_UUID = "7611e6e3960f455b9e0055ec371f2953"


@pytest.mark.xfail
def test_select_routes_from_list():
    """Failing because test page isn't the same as the real page."""
    routes_list = _filter_by_html_tag(TEST_PAGE, ROUTES_TAG)
    lst = select_routes_from_list(routes_list)
    assert isinstance(lst, list)


def test_get_cims_list():
    cims_list = get_cims_list()
    assert isinstance(cims_list, list)
    assert isinstance(cims_list[0], dict)


@pytest.mark.xfail
def test_get_cim_routes_list():
    """Failing because test page isn't the same as the real page."""
    cim_route_list = get_cim_routes_list(CIM_UUID, TEST_PAGE, ROUTES_TAG)
    assert isinstance(cim_route_list, dict)
    assert isinstance(cim_route_list[CIM_UUID], dict)
    assert len(cim_route_list[CIM_UUID]["trekking"]) == 10
