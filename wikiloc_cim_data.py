import random
from typing import List
from time import sleep

import bs4
from bs4.element import Tag, ResultSet
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.firefox.options import Options

from feec_cim_data import CimsList

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
    btn = driver.find_element_by_id("acept-cookies")
    btn.click()


#########################
# Scrape information
#########################

# Get list route tag
# Get url from each listed route


def is_trekking_route(route_url: str):
    """Check if is a trekking route or not."""
    if route_url.startswith("/rutas-senderismo"):
        return True
    return False


def _get_treks(routes_list: List[str]) -> List[str]:
    lst = []
    for route in routes_list:
        if is_trekking_route(route):
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
    # breakpoint()
    route_url = route_url_tag[0]["href"]
    return route_url

def select_routes_from_list(routes_list: bs4.Tag):
    # route_html_card = routes_list.select("div.trail")
    routes_cards_tag = routes_list.select("div.trail")
    return [_get_url_from_card(idx +1, card) for idx, card in enumerate(routes_cards_tag)]


def setup_browser():
    """Set up browser driver before start navigation.

    TODO:
    Export user list from outside
    Posible export configration from outside

    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
        "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1",
    ]  # noqa

    user_agent = random.choice(user_agents)
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", user_agent)
    opts = Options()
    # opts.headless = True
    driver: webdriver = webdriver.Firefox(firefox_profile=profile, options=opts)
    return driver


def get_cims_list():
    return CimsList.get_all()


def main():
    cim_url = "https://es.wikiloc.com/"
    driver = setup_browser()
    # open wikiloc main page and accept cookies
    driver.get(cim_url)
    accept_cookie(driver)

    # get list of cims
    cims_list = CimsList.get_all()
    for cim in cims_list[:4]:
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
        cim["routes"] = get_cim_routes_list(cim["uuid"], page, ROUTES_TAG)
        # breakpoint()
        cim["url_search"] = driver.current_url
        print(cim)

if __name__ == "__main__":
    main()
