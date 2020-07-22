"""Test database call and data manipulation."""

import pytest  # type: ignore
import ujson

from server.app import db
from server.data_collector.utils import to_geojson
from server.schemas import CimsList


@pytest.fixture(scope="module")
def data():
    """Return all cim from in memory data."""
    return db.get_all(schema=True)


def test_serialize_cims_with_pydantic(data):
    """Get all cims from db based on cim schema."""
    cims_list = data
    isinstance(cims_list, list)
    isinstance(cims_list[0], dict)


def test_get_single_cim():
    """Returns a single cim by its id."""
    cim = db.get(id_=1)
    isinstance(cim, dict)
    cim.id == 1


def test_create_geojson(data):
    """Test converting list of cim (json) objects to geojson format object."""
    expected_base_keys = ["type", "features"]
    geojson = to_geojson(data)
    list(geojson.keys()) == expected_base_keys
    isinstance(geojson["features"], list)
    assert len(geojson["features"]) == 308


def test_create_geojso_file_for_dev(data):
    """Create a sample of cims to dev client front end map.

    Total of 30 cims, 15 essential, 15 from repte.
    """
    essentials = [cim for cim in data if cim.essential is True]
    repte = [cim for cim in data if cim.essential is False]
    cims = [*essentials[:15], *repte[:15]]
    assert len(cims) == 30
    geojson = to_geojson(cims)
    with open("cims_data/geojson_cims.geojson", "w") as f:
        ujson.dump(geojson, f)
