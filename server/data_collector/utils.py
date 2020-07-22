"""General scrapers utility set."""

import asyncio
from queue import Queue
from typing import List, Dict, Union
from time import sleep
import bs4
from bs4.element import ResultSet, Tag
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.firefox.options import Options

from server.data_collector.feec import CimsList

from server.schemas import Cim
from server.app import db

#########################
# Configurations
#########################
ROUTES_TAG = "div.main__results:nth-child(2)"
LIMIT_ROUTES = 10

#########################
# Helper functions
#########################
def _filter_by_html_tag(page: str, tag: str) -> bs4.element.Tag:
    soup = bs4.BeautifulSoup(page, features="html.parser")
    return soup.select(tag)[0]


def search_cim(driver: webdriver, keyword: str) -> None:
    """Wikiloc search box input."""
    cim_name = keyword
    search = driver.find_element_by_class_name("search-box__input")
    search.send_keys(cim_name)
    search.click()
    try:
        btn_select_first = driver.find_element_by_class_name("search-box-item__first")
        btn_select_first.click()
        return True
    except ElementClickInterceptedException:
        # TODO: handle possible error here and logging
        print("ERROR")
        return False


def accept_cookie(driver: webdriver) -> None:
    """Wikiloc accept cookie policy."""
    try:
        btn = driver.find_element_by_id("acept-cookies")
        btn.click()
    except NoSuchElementException:
        pass


def get_cims_list():
    return CimsList.get_all()


#########################
# Scrape information
#########################


def _get_treks(routes_list: List[str], type_: str = "/rutas-senderismo") -> List[str]:
    lst = []
    for route in routes_list:
        if route.startswith(type_):
            lst.append(route)
            if len(lst) == LIMIT_ROUTES:
                return lst

    return lst


def get_cim_routes_list(cim_uuid, page, tag):
    """Get cim route list from wikiloc html page tag."""
    routes_list_tag = _filter_by_html_tag(page, tag)
    routes_list = select_routes_from_list(routes_list_tag)
    trekking_routes = _get_treks(routes_list)
    return {cim_uuid: {"trekking": trekking_routes}}


def _retry_get_url(*args, times=3):
    for _ in range(times):
        url = _get_url_from_card(*args)
        if url:
            return url
        else:
            sleep(0.3)
    return None


def _get_url_from_card(idx: int, card: bs4.Tag) -> str:
    """Stripe url from route html card element."""
    # card_header = card.select("div.trail-card__header")[0]
    route_url_tag = card.select(
        f"div.trail:nth-child({idx}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)"  # noqa
    )
    try:
        route_url = route_url_tag[0]["href"]
    except IndexError:
        try:
            route_url = card.select("div")[0].select("a")[0].attrs["href"]
        except Exception as e:
            print(e)
    return route_url


def select_routes_from_list(routes_list: bs4.Tag):
    # route_html_card = routes_list.select("div.trail")
    routes_cards_tag = routes_list.select("div.trail")
    routes_urls = []
    for idx, card in enumerate(routes_cards_tag, start=1):
        url = _get_url_from_card(idx, card)
        if url is not None:
            routes_urls.append(url)
    return routes_urls
    # return [
    #     _get_url_from_card(idx, card)
    #     for idx, card in enumerate(routes_cards_tag, start=1)
    # ]


def setup_browser(headless: bool = False) -> webdriver:
    """Set up browser driver before start navigation.

    TODO:
    Export user list from outside
    Posible export configration from outside

    """

    user_agent = UserAgent()
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent.random)
    opts = Options()
    if headless:
        opts.headless = True
    driver: webdriver = webdriver.Firefox(firefox_profile=profile, options=opts)
    return driver


def _list_cims(cims_list, n_cims=20):
    """Divide list of cims in equal parts."""
    for i in range(0, len(cims_list) + 1, n_cims):
        yield cims_list[i : i + n_cims]


def create_queue(cims_list: List[Cim], cims_per_task: int = 20):
    queue = Queue()
    for cims in _list_cims(cims_list, n_cims=cims_per_task):
        queue.put(cims)
    queue.put(None)
    return queue


async def wikiloc_browser(url, cims):
    from server.data_collector.wikiloc import WikiLoc

    driver = setup_browser()  # blocking
    wikiloc = WikiLoc(url)  # blocking
    await asyncio.sleep(0.5)
    cims_info = wikiloc.collect(driver, cims)  # blocking
    db.add(cims_info)
    driver.close()
    print(f"Browser <{driver.session_id}> closed ")
    return cims_info


async def run_multiple(url: str, queue: Queue, cims_list=None):
    # for cims in cims_list:
    tasks = set()
    task_ref = 1
    while True:
        cims = queue.get()
        if cims is None:
            break
        await asyncio.sleep(0.5)
        # asyncio.get_event_loop().run_in_executor(None, wikiloc_browser, url, cims)
        task = asyncio.create_task(wikiloc_browser(url, cims), name=task_ref)
        tasks.add(task)
        task_ref += 1
        # wikiloc_browser(url, cims)
    while len(tasks):
        done, _pending = await asyncio.wait(tasks, timeout=1)
        tasks.difference_update(done)
        urls = (t.get_name() for t in tasks)
        print(f"Missing urls to be processed {' '.join(urls)}")

    db.commit()
    print("Everything commited into db")


async def download_missing_cims(
    BASE_URL, cims_with_routes, cims_list, missing_cims_info: list
):
    """TODO: Missing implementation."""
    if len(cims_with_routes) != len(cims_list):
        cim_routes = set(cims_with_routes.keys())
        cims = set(cims_list)
        missing = cims.difference(cim_routes)
        download_cims = [cims_list[cim] for cim in missing]
        if missing_cims_info is None:
            missing_cims_info = await wikiloc_browser(BASE_URL, download_cims)
        cims = db.add(missing_cims_info)
        for k, v in cims.items():
            # breakpoint()
            cims_with_routes[k] = v
        return cims_with_routes
    return False


def to_geojson(data: Union[List[Cim], Dict[str, List[Cim]]]):
    """Convert a list of cims to a geojson data format."""

    def _generate(cim_type):
        cim: Cim

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "uuid": cim.uuid,
                        "name": cim.nombre,
                        "region": cim.region,
                        "lat": cim.lat,
                        "lng": cim.lang,
                        "alt": cim.alt,
                        "essential": cim.essential,
                        "url": cim.url,
                        "img_url": cim.img_url,
                        "routes": cim.routes,
                    },
                    "geometry": {"type": "Point", "coordinates": [cim.lang, cim.lat]},
                }
                for cim in data[cim_type]
            ],
        }

    if isinstance(data, dict):
        return {"essentials": _generate("essentials"), "repte": _generate("repte")}
    cim: Cim
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "uuid": cim.uuid,
                    "nombre": cim.nombre,
                    "region": cim.region,
                    "lat": cim.lat,
                    "lang": cim.lang,
                    "alt": cim.alt,
                    "essential": cim.essential,
                    "url": cim.url,
                    "img_url": cim.img_url,
                    "routes": cim.routes,
                },
                "geometry": {"type": "Point", "coordinates": [cim.lang, cim.lat]},
            }
            for cim in data
        ],
    }
