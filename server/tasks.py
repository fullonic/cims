from typing import List

from selenium import webdriver

from server.schemas import Cim
from .data_collector.wikiloc import WikiLoc


def wikiloc_collect(driver: webdriver, url: str, cims_list: List[Cim]):
    """Top level call for wikiloc browser data collect."""
    wikiloc = WikiLoc(url)
    wikiloc.collect(driver, cims_list)
    wikiloc.save()
    driver.close()
    print("Browser closed")