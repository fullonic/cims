"""Ram database."""

from dataclasses import dataclass, field
from functools import lru_cache
from server.data_collector.feec import CimsList
import json


@lru_cache
def get_cims() -> dict:
    return CimsList.as_dict()


CIMS = get_cims()


@dataclass
class DataBase:
    """In memory database."""

    routes: list = field(default_factory=list)
    search_urls: list = field(default_factory=list)
    updated_cims: dict = field(default_factory=dict)

    def add(self, data):
        """Commit data into memory session."""
        print("Adding to in memory database")

        if data.get("routes", False):
            print("Here")
            # search cim by UUID
            for el in data["routes"]:
                uuid = list(el.keys())[0]
                print(f"Saving {uuid}")
                # search for cims uuid on list
                try:
                    cim = CIMS.get(uuid, None)
                    routes = el[uuid]["trekking"]
                    # add routes to route el
                    cim["routes"] = routes
                    self.updated_cims[uuid] = cim
                    self.routes.append(routes)
                except KeyError:
                    print(f"UUID not found: {uuid}")
        return self.updated_cims

    def commit(self):
        """Commit data into file."""
        with open("routes_cims.json", "w") as f:
            json.dump(self.updated_cims, f)
        print(f"Commit {len(self.updated_cims)} cims into json file")


RAMDB = DataBase()
