"""Test suite of wikiloc data collection."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import pytest  # type: ignore

from server.data_collector.feec import CimsList

# from server.tasks import wikiloc_collect
from server.data_collector.utils import (
    _filter_by_html_tag,
    accept_cookie,
    create_queue,
    download_missing_cims,
    get_cim_routes_list,
    get_cims_list,
    run_multiple,
    search_cim,
    select_routes_from_list,
    setup_browser,
)


@lru_cache
def open_file(path, type_="plain_text"):
    with open(path) as f:
        if type_ == "json":
            return json.load(f)
        return f.read()


TEST_PAGE = open_file("./tests/testing_html_pages/wikiloc_search_cim.html")
ROUTES_TAG = "div.main__results:nth-child(2)"
TITLE_TAG = open_file("./tests/testing_html_pages/title_tag.html")
CIM_UUID = "7611e6e3960f455b9e0055ec371f2953"
BASE_URL = "https://es.wikiloc.com/"


def test_select_routes_from_list():
    """Failing because test page isn't the same as the real page."""
    routes_list = _filter_by_html_tag(TEST_PAGE, ROUTES_TAG)
    lst = select_routes_from_list(routes_list)
    assert isinstance(lst, list)


def test_get_cims_list():
    cims_list = get_cims_list()
    assert isinstance(cims_list, list)
    assert isinstance(cims_list[0], dict)


def test_get_cim_routes_list():
    """Failing because test page isn't the same as the real page."""
    cim_route_list = get_cim_routes_list(CIM_UUID, TEST_PAGE, ROUTES_TAG)
    assert isinstance(cim_route_list, dict)
    assert isinstance(cim_route_list[CIM_UUID], dict)
    assert len(cim_route_list[CIM_UUID]["trekking"]) == 10


@pytest.mark.skip
def test_search_cim():
    """Test search cim by name."""
    cim_name = "Puig de Tretzevents"
    url = BASE_URL
    driver = setup_browser()
    # Open browser
    driver.get(url)
    accept_cookie(driver)
    # Search cim
    search_succeed = search_cim(driver, cim_name)
    # get page content
    page = driver.page_source
    assert search_succeed is True
    assert isinstance(page, str)
    # assert len(page) == 170099


@pytest.mark.skip
def test_multiple_browsers():
    workers = 4
    cims_per_task = 5
    loop = asyncio.get_event_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=workers))
    loop.set_debug(True)
    cims_list = CimsList.get_all()
    queue = create_queue(cims_list, cims_per_task)

    loop.run_until_complete(run_multiple(BASE_URL, queue))


@pytest.mark.asyncio
async def test_create_queue():
    """Test creation of task queue of cims to be scrapped."""
    cims_per_task = 4
    cims_list = CimsList.get_all()[:10]
    q = create_queue(cims_list, cims_per_task)
    assert q.qsize() == 4


@pytest.mark.skip
def test_add_key_to_cims_list():
    """Add uuid to cims list and dumps to json file."""
    lst = CimsList.get_all()
    key_cims = {}
    with open("key_cims.json", "w") as f:
        for el in lst:
            uuid = el["uuid"]
            key_cims[uuid] = el
        json.dump(key_cims, f)


@pytest.mark.asyncio
async def test_download_missing_cims():
    """Check if there is missing routes urls for cims."""
    base_path = "/home/somnium/Desktop/CODE/Projects/CV/100cims/server/data_collector"
    cims_with_routes: dict = open_file(f"{base_path}/routes_cims.json", "json")
    cims_list: dict = open_file(f"{base_path}/key_cims.json", "json")
    cims_info = open_file("./tests/testing_html_pages/cims_info.json", "json")
    await download_missing_cims(BASE_URL, cims_with_routes, cims_list, cims_info)
    assert len(cims_with_routes) == len(cims_list)
