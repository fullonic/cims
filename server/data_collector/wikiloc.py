from dataclasses import dataclass, field
from typing import List

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from .feec import CimsList
from .utils import (
    _collect_wikiloc_data,
    accept_cookie,
    setup_browser,
    search_cim,
    get_cim_routes_list,
    ROUTES_TAG,
    _save,
)


@dataclass
class WikiLoc:
    """Wikiloc data collector."""

    url: str
    search_urls: List = field(default_factory=list)
    routes_list: List = field(default_factory=list)

    def save(self):
        print(self.search_urls)
        print(self.routes_list)

    def collect(self, driver: webdriver, cims_list: List):
        """Run collector script by order."""
        driver.get(self.url)
        accept_cookie(driver)

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
            self.routes_list.append(get_cim_routes_list(cim["uuid"], page, ROUTES_TAG))
            # breakpoint()
            self.search_urls.append({cim["uuid"]: driver.current_url})

        # save new data into files


if __name__ == "__main__":
    """Run standallone wikiloc browser collector.

    Mainly for testing
    """
    driver = setup_browser()
    cims_lst = CimsList.get_all()[:3]
    url = "https://es.wikiloc.com/"
    wikiloc = WikiLoc(url)
    wikiloc.collect(driver, cims_lst)
