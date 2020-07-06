import json

import pytest
import bs4
from feec_cim_data import (
    cims,
    get_essential_cim_list,
    list_to_dict,
    complementary_info,
    create_cims_list,
    merge_information,
)


def open_file(path):
    with open(path) as f:
        return f.read()


TAG_SCRIPT_TEST = open_file("./tests/testing_html_pages/tag.txt")
HTML_CIM_PAGE = open_file("./tests/testing_html_pages/cim_page.html")
ESSENTIAL_PATTERN = r"var cims_essencials = \[(.*?)\]"


@pytest.mark.vcr()
def test_scrape_cims_main_page():
    """Test scrape main page."""
    res = cims("https://www.feec.cat/activitats/100-cims/")
    assert isinstance(res, bs4.Tag)


def test_scrape_cims():
    """Test filter essential scripts from cims main page."""
    lst = get_essential_cim_list(ESSENTIAL_PATTERN, TAG_SCRIPT_TEST)
    assert isinstance(lst, list)


def test_dict_from_list():
    """Test convert a list of dictionary in string format to python native dict."""
    lst = [
        'nombre: "El Cogulló de Cabra",lat: "41.4290355033", lang: "1.30575794888", url: "https://www.feec.cat/activitats/100-cims/cim/el-cogullo-de-cabra/"',
        'nombre: "Puig de Tretzevents",lat: "42.492101894", lang: "2.4683643295", url: "https://www.feec.cat/activitats/100-cims/cim/puig-de-tretzevents/"',
        'nombre: "Torre de Madeloc",lat: "42.4904284262", lang: "3.07511682009", url: "https://www.feec.cat/activitats/100-cims/cim/torre-de-madeloc/"',
    ]
    dic = list_to_dict(lst)
    expected = {
        "nombre": "El Cogulló de Cabra",
        "lat": 41.4290355033,
        "lang": 1.30575794888,
        "url": "https://www.feec.cat/activitats/100-cims/cim/el-cogullo-de-cabra/",
    }
    assert expected == dic[0]
    assert isinstance(dic, list)
    assert isinstance(dic[0], dict)


@pytest.mark.vcr()
def test_complementary_info():
    cim_info = complementary_info(
        "https://www.feec.cat/activitats/100-cims/cim/la-mola/"
    )
    assert isinstance(cim_info, dict)
    cim_info["uuid"] = "e96c8b97f6ff4766ab7dd996843cb226"
    expected = {
        "uuid": "e96c8b97f6ff4766ab7dd996843cb226",
        "region": "Baix Penedès, Tarragonès",
        "alt": 317,
        "img_url": "https://www.feec.cat/wp-content/uploads/2019/04/La-Mola-Bonastre-scaled.jpg",
        "essential": False,
        "routes": [],
    }
    assert cim_info == expected


@pytest.mark.vcr()
def test_merge_information():
    test_cims = [
        {
            "nombre": "El Cogulló de Cabra",
            "lat": 41.4290355033,
            "lang": 1.30575794888,
            "url": "https://www.feec.cat/activitats/100-cims/cim/el-cogullo-de-cabra/",
        },
        {
            "nombre": "Puig de Tretzevents",
            "lat": 42.492101894,
            "lang": 2.4683643295,
            "url": "https://www.feec.cat/activitats/100-cims/cim/puig-de-tretzevents/",
        },
        {
            "nombre": "Torre de Madeloc",
            "lat": 42.4904284262,
            "lang": 3.07511682009,
            "url": "https://www.feec.cat/activitats/100-cims/cim/torre-de-madeloc/",
        },
    ]
    test_complete_cim_info = {
        "nombre": "El Cogulló de Cabra",
        "lat": 41.4290355033,
        "lang": 1.30575794888,
        "url": "https://www.feec.cat/activitats/100-cims/cim/el-cogullo-de-cabra/",
        "uuid": "73d99e98e43d427ab6d66471d379c0ab",
        "region": "Alt Camp",
        "alt": 881,
        "img_url": "https://www.feec.cat/wp-content/uploads/2019/04/El-Cogulló-de-Cabra-scaled.jpg",
        "essential": True,
        "routes": [],
    }

    test_essential = test_cims

    all_cims = {"essential": test_essential, "repte": ""}

    essential = [
        cim for cim in merge_information(all_cims["essential"], essential=True)
    ]

    cims_list = {"essential": essential, "repte": ""}

    cim_params = [
        "nombre",
        "lat",
        "lang",
        "url",
        "uuid",
        "region",
        "alt",
        "img_url",
        "essential",
        "routes",
    ]
    _mock_cim = cims_list["essential"][0]
    _mock_cim["uuid"] = "73d99e98e43d427ab6d66471d379c0ab"
    assert list(cims_list.keys()) == ["essential", "repte"]
    assert list(cims_list["essential"][0].keys()) == cim_params
    assert _mock_cim == test_complete_cim_info
