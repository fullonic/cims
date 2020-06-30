"""Application schemas."""
from pydantic import BaseModel


class Cim(BaseModel):
    """Cim obj class."""

    name: str
    region: str
    lat: float
    lng: float
    alt: int
    url: str
    img_url: str
