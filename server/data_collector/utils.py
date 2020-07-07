import random
import json
from pathlib import Path
from typing import List
from time import sleep
from dataclasses import dataclass
import bs4
from bs4.element import Tag, ResultSet
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent

from server.schemas import Cim
from server.data_collector.feec import CimsList

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
    """Get cim route list from wikiloc page."""
    routes_list_tag = _filter_by_html_tag(page, tag)
    routes_list = select_routes_from_list(routes_list_tag)
    trekking_routes = _get_treks(routes_list)
    return {cim_uuid: {"trekking": trekking_routes}}


def _get_url_from_card(idx: int, card: bs4.Tag) -> str:
    """Stripe url from route html card element."""
    # card_header = card.select("div.trail-card__header")[0]
    route_url_tag = card.select(
        f"div.trail:nth-child({idx}) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > a:nth-child(1)"  # noqa
    )
    route_url = route_url_tag[0]["href"]
    return route_url


def select_routes_from_list(routes_list: bs4.Tag):
    # route_html_card = routes_list.select("div.trail")
    routes_cards_tag = routes_list.select("div.trail")
    return [
        _get_url_from_card(idx + 1, card) for idx, card in enumerate(routes_cards_tag)
    ]


def setup_browser(headless: bool = False):
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


def _save(new_update, name, mode="w"):
    # open file
    # fname = Path(__file__).parent / f"{name}.json"
    with open(name, mode) as f:
        f.write(new_update + "\n")
    # save new data into file
    # with open(fname, mode) as f:
    #     current[name].append(new_update)
    #     json.dump(current, f)


def _collect_wikiloc_data(driver, cims_list):
    search_urls = []
    routes_list = []
    for cim in cims_list:
        search_cim(driver, cim["nombre"])
        try:
            btn_select_first = driver.find_element_by_class_name(
                "search-box-item__first"
            )
        except ElementClickInterceptedException:
            # TODO: handle possible error here
            print("ERROR")
        btn_select_first.click()

        page = driver.page_source

        # scrape list of routes
        routes_list.append(get_cim_routes_list(cim["uuid"], page, ROUTES_TAG))
        # breakpoint()
        search_urls.append({cim["uuid"]: driver.current_url})

    # save new data into files
    _save(routes_list, "routes_list.txt")
    _save(search_urls, "search_urls.txt")
