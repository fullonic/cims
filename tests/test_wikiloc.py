import asyncio
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import pytest
from bs4.element import Tag, ResultSet

from server.data_collector.utils import (
    select_routes_from_list,
    get_cims_list,
    _filter_by_html_tag,
    get_cim_routes_list,
    search_cim,
    accept_cookie
)

from server.data_collector.feec import CimsList
from server.tasks import wikiloc_collect
from server.data_collector.utils import setup_browser


def open_file(path):
    with open(path) as f:
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


def _collect(url, cims):
    driver = setup_browser()
    user_agent = driver.execute_script("return navigator.userAgent;")
    print(user_agent)
    wikiloc_collect(driver, url, cims)


async def run_multiple(url: str, queue: Queue, cims_list=None):
    # for cims in cims_list:
    while True:
        cims = queue.get()
        if cims is None:
            break
        await asyncio.sleep(0.5)
        asyncio.get_event_loop().run_in_executor(None, _collect, url, cims)


def split_cims(queue, n_cims=20):
    """Divide list of cims in equal parts."""
    cims_list = CimsList.get_all()[:10]
    for i in range(0, len(cims_list) + 1, n_cims):
        yield cims_list[i : i + n_cims]


@pytest.mark.skip
def test_multiple_browsers():
    workers = 4
    cims_per_task = 2
    loop = asyncio.get_event_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=workers))
    loop.set_debug(True)
    queue = Queue()

    for cims in split_cims(queue, n_cims=cims_per_task):
        queue.put(cims)
    queue.put(None)
    # cims = [lst[:4], lst[4:8], lst[8:12], lst[8:16]]

    loop.run_until_complete(run_multiple(BASE_URL, queue))


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
