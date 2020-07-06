import pytest

from wikiloc_cim_data import (
    select_routes_from_list,
    get_cims_list,
    _filter_by_html_tag,
    get_cim_routes_list,
    is_trekking_route,
)

from bs4.element import Tag, ResultSet


def open_file(path):
    with open(path) as f:
        return f.read()


TEST_PAGE = open_file("./tests/testing_html_pages/wikiloc.html")
ROUTES_TAG = "div.main__results:nth-child(2)"
TITLE_TAG = open_file("./tests/testing_html_pages/title_tag.html")
CIM_UUID = "7611e6e3960f455b9e0055ec371f2953"


# @pytest.mark.skip
# def test_get_routes_list():
#     """Test scrape route list from wikiloc cim search.

#     WHEN: Wikiloc page is scraped
#     THEN: Return only the list div
#     """
#     routes_list = get_routes_list(TEST_PAGE, ROUTES_TAG)

#     assert isinstance(routes_list, list)
#     assert isinstance(routes_list[0], dict)


def test_select_routes_from_list():
    routes_list = _filter_by_html_tag(TEST_PAGE, ROUTES_TAG)
    lst = select_routes_from_list(routes_list)
    assert isinstance(lst, list)


def test_get_cims_list():
    cims_list = get_cims_list()
    assert isinstance(cims_list, list)
    assert isinstance(cims_list[0], dict)


def test_is_trekking_route():
    test_url = "/rutas-senderismo/col-de-la-regine-pic-des-sept-hommes-puig-de-roja-puig-de-tretzevents-8216501"
    routes_list = is_trekking_route(test_url)
    assert routes_list is True


def test_get_cim_routes_list():
    """Test cim routes list."""
    cim_route_list = get_cim_routes_list(CIM_UUID, TEST_PAGE, ROUTES_TAG)
    assert isinstance(cim_route_list, dict)
    assert isinstance(cim_route_list[CIM_UUID], dict)
    assert len(cim_route_list[CIM_UUID]["trekking"]) == 10
