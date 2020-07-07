import pytest
from server.data_collector.feec import (
    get_cims_basic_information,
    create_cims_list,
    CimsList,
)
from server.tasks import wikiloc_collect
from server.data_collector.utils import setup_browser


@pytest.mark.skip
def test_get_cims_basic_information():
    cims = get_cims_basic_information()
    cims_group = "essential repte".split(" ")
    expected_keys = "nombre lat lang url".split(" ")

    assert isinstance(cims, dict)
    assert isinstance(cims["essential"], list)
    assert list(cims["essential"][0].keys()) == expected_keys
    assert list(cims.keys()) == cims_group
    assert len(cims["essential"]) == 150
    assert len(cims["repte"]) == 158


@pytest.mark.skip
@pytest.mark.vcr()
def test_create_cims_list():
    """Test all scraped functionality.

    Most top level cims scrape interface.
    """
    cim_params = ["nombre", "lat", "lang", "url", "comarca", "alt", "img_url"]
    all_cims = create_cims_list(True)
    assert list(all_cims.keys()) == ["essential", "repte"]
    assert list(all_cims["essential"][0].keys()) == cim_params


@pytest.mark.skip
def test_wikiloc_collect():
    cims_list = CimsList.get_all()[:3]
    url = "https://es.wikiloc.com/"
    driver = setup_browser(headless=True)
    breakpoint()
    wikiloc_collect(driver, url, cims_list)
