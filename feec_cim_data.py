import re
from typing import Dict, Union, List
import requests
import bs4
import json
from uuid import uuid4
from schemas import Cim

ESSENTIAL_PATTERN = r"var cims_essencials = \[(.*?)\]"
REPTE_PATTERN = r"var cims_repte = \[(.*?)\]"


def _get_uuid() -> str:
    """Generate a hex uuid4 str."""
    return uuid4().hex


def tuples_from_list(lst):
    """Create a list of tuples from a list of strings.

    TODO: Rename function name and create better doc string
    """
    return dict([tuple(el.split(": ")) for el in lst])


def clean_cim_dict(d: Dict[str, str]) -> Dict[str, Union[str, float]]:
    """Remove unnecessary characters from dictionary.

    Removes whitespaces from dict keys,
    Convert coordinates from str to floats

    TODO: Resolve mypy type conflicts
    """
    new_dict = {}
    # v: Union[str, float]
    for k, v in d.items():
        v = v.replace('"', "")
        k = k.strip(" ")  # type: ignore
        try:
            v = float(v)  # type: ignore
        except ValueError:
            pass
        new_dict[k] = v
    return new_dict  # type: ignore


def list_to_dict(lst: list) -> List[dict]:
    """Generate a dictionary of cims from cims_list.

    TODO: Convert to generator
    """
    dic_list = []
    for el in lst:
        dic = tuples_from_list(el.split(","))
        dic_list.append(clean_cim_dict(dic))
    return dic_list


def get_essential_cim_list(pattern: str, tag: str = None) -> list:
    """Grab information of essential cims using regex."""
    pts_lst = re.findall(pattern, tag)
    pts = pts_lst[0].replace("\\", "")
    pts = pts.replace("'", '"')
    pattern_dict = r"\{(.*?)\}"
    cims_list = re.findall(pattern_dict, pts)
    return cims_list


def cims(url: str) -> bs4.element.Tag:
    """Scrape script tag with inmformation from all cims.

    Information is filtered from scraping the FEEC "100 cims" main page.
    """
    body = requests.get(url)
    soup = bs4.BeautifulSoup(body.text, features="html.parser")
    tag = soup.select("script")[11]
    return tag


def _get_basic_info(pattern, tag):
    cims_list = get_essential_cim_list(pattern, tag)
    return list_to_dict(cims_list)


def get_cims_basic_information() -> Dict[str, list]:
    """Build dictionary information of essenital cims."""
    # Grab all cims page info
    url = "https://www.feec.cat/activitats/100-cims/"
    cims_tag: bs4.element.Tag = cims(url)

    essential_cims = _get_basic_info(ESSENTIAL_PATTERN, cims_tag.contents[0])
    repte_cims = _get_basic_info(REPTE_PATTERN, cims_tag.contents[0])
    return {"essential": essential_cims, "repte": repte_cims}


#########################
# Single cim scraper
#########################


def _get_coordinates(cim_info_tag: bs4.Tag) -> tuple:
    """Get coordinate data from cim page."""
    lat_info = cim_info_tag.select("div.fw-bold:nth-child(6)")[0].text
    lat = float(lat_info[:-1])
    lng_info = cim_info_tag.select("div.col-6:nth-child(8)")[0].text
    lng = float(lng_info[:-1])
    return lat, lng


def complementary_info(url=None):
    """Scrape cim detailed information from cim page.

    We get the url and visit each page to take extra information about each cim.
    Also we add the id, the UUID,
    """
    if url.startswith("https"):
        page = requests.get(url).text
    else:
        # use html file for testing. Remove later
        with open(url) as f:
            page = f.read()

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(page, features="html.parser")
    cim_info_tag: bs4.Tag = soup.select("div.bg-primari:nth-child(3)")[0]
    # region info
    region: str = cim_info_tag.select("div.fw-bold:nth-child(2)")[0].text
    region = region.strip()
    # altitude
    alt: str = cim_info_tag.select("div.fw-bold:nth-child(4)")[0].text
    altitude: int = int(alt[:-2])
    # img
    img_tag = soup.select(".attachment-post-thumbnail")[0]
    img_url = img_tag.attrs["src"]
    uuid = _get_uuid()
    return {
        "uuid": uuid,
        "region": region,
        "alt": altitude,
        "img_url": img_url,
        "essential": False,
        "routes": [],
    }


#########################
# Merge complementary data with basic info
#########################
def merge_information(cims_list: List[dict], essential=False):
    """Build final cim information."""
    # new_list = []
    for cim in cims_list:
        extra_info = complementary_info(cim["url"])
        cim.update(extra_info)
        if essential:
            cim["essential"] = True
        yield cim
    # return new_list


def create_cims_list(save: bool = False) -> Dict[str, list]:
    """Most top level cims scrape interface."""
    cims_basic_info: Dict[str, list] = get_cims_basic_information()
    cims = {
        "essential": [
            cim for cim in merge_information(cims_basic_info["essential"], True)
        ],
        "repte": [cim for cim in merge_information(cims_basic_info["repte"])],
    }
    if save:
        with open("cims.json", "w") as f:
            json.dump(cims, f)

    return cims


class CimsList:
    @staticmethod
    def get_all() -> list:
        """Return all cims from database."""
        with open("cims.json") as f:
            cims = json.load(f)
        return [*cims["essential"], *cims["repte"]]
