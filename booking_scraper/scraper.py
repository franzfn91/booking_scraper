from __future__ import annotations

import asyncio
import collections
import collections.abc
import dataclasses
import json
import logging
import pathlib
import re
import typing as ty
from urllib.parse import urljoin

import aiohttp
import bs4

_logger = logging.getLogger(__name__.split(".", 1)[0])

T = ty.TypeVar("T")


async def achain(*iterables: ty.AsyncIterable[T]) -> ty.AsyncIterator[T]:
    """Async chaining of iterables"""
    for iterable in iterables:
        async for item in iterable:
            yield item


class DataclassesJSONEncoder(json.JSONEncoder):
    """JSON encoder with support for dataclasses"""

    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


@dataclasses.dataclass(frozen=True)
class HotelItem:
    """Definition of an Ad item"""

    url: str
    title: str
    price: str


@dataclasses.dataclass(frozen=True)
class SearchConfig:
    """Configuration of a search"""

    name: str
    url: str
    recursive: bool = True


@dataclasses.dataclass(frozen=True)
class FilterConfig:
    """Configuration of filters"""

    exclude_patterns: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Config:
    """Overall configuration object"""

    filter: FilterConfig = dataclasses.field(default_factory=FilterConfig)
    notifications: dict[str, dict[str, ty.Any]] = dataclasses.field(default_factory=dict)
    searches: list[SearchConfig] = dataclasses.field(default_factory=list)


class DataStore(collections.UserDict[str, HotelItem]):
    """Dict-like object backed by a JSON file"""

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        super().__init__()

    def __enter__(self) -> DataStore:
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        try:
            with open(self.path) as f:
                self.data = {key: HotelItem(**value) for key, value in json.load(f).items()}
        except FileNotFoundError:
            _logger.warning("Data store does not exist at '%s', will be created when closing", self.path)

    def close(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, cls=DataclassesJSONEncoder, indent=2)


@dataclasses.dataclass
class Result:
    """Results of search config"""

    search_config: SearchConfig
    num_already_in_datastore: int = 0
    num_excluded: int = 0
    hotelitems: list[HotelItem] = dataclasses.field(default_factory=list)


async def get_soup(session: aiohttp.ClientSession, url: str) -> bs4.BeautifulSoup:
    """Get the website and parse its markup using BeautifulSoup"""
    _logger.info("Getting soup for '%s'", url)
    # Tell the website we are a Chrome browser
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"
    async with session.get(url, headers={"User-Agent": user_agent}) as response:
        content = await response.text()
        return bs4.BeautifulSoup(content, features="lxml")


def get_all_page_urls(soup: bs4.BeautifulSoup, url: str) -> list[str]:
    """Get the URL of all anchor elements with class pagination-page

    :param soup: BeautifulSoup object to get the pagination URLS from
    :type soup: bs4.BeautifulSoup
    :param url: URL of the `soup` object to build absolute URLs
    :type url: str
    :return: List of URLs
    :rtype: list[str]
    """
    anchors = soup.select("a.pagination-page")
    return [urljoin(url, href) for link_element in anchors if isinstance(href := link_element.get("href"), str)]


async def get_hotelitems_from_soup(soup: bs4.BeautifulSoup, url: str) -> ty.AsyncGenerator[HotelItem, None]:
    """Get all ad items in a list of BeatifulSoup objects"""
    _logger.debug("Find all ad items in '%s'", url)
    for soup_hotelitem in soup.find_all("div", attrs={"data-testid": "property-card"}):
        hotelitem = HotelItem(
            url=soup_hotelitem.find("h3").find("a")["href"],
            title=soup_hotelitem.find("h3").find("div").text.strip(),
            price=soup_hotelitem.select('span[data-testid="price-and-discounted-price"]')[0]
            .text.replace("\xa0", " ")
            .strip(),
        )
        yield hotelitem


async def get_new_hotelitems(search_config: SearchConfig, filter_config: FilterConfig, data_store: DataStore) -> Result:
    """
    Return a result for a search configuration

    The result will only contain all new HotelItems which are not yet in the data store and not excluded by the filters

    :param search_config: Search configuration to get the HotelItems from
    :type search_config: SearchConfig
    :param filter_config: Filter configuration for the HotelItems
    :type filter_config: FilterConfig
    :param data_store: Data store object to check if hotelitem is new
    :type data_store: DataStore
    :return: Result for this search configuration
    :rtype: Result
    """
    result = Result(search_config)
    exclude_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in filter_config.exclude_patterns]

    async with aiohttp.ClientSession() as session:
        soup_map = {search_config.url: (await get_soup(session, search_config.url))}

        async for hotelitem in achain(*[get_hotelitems_from_soup(soup, url) for url, soup in soup_map.items()]):
            if hotelitem.title in data_store:
                _logger.debug("Ad item '%s' in data store", hotelitem.title)
                result.num_already_in_datastore += 1
                continue

            exclude_hotelitem = False

            _logger.debug("Ad item '%s' added to data store", hotelitem.title)
            data_store[hotelitem.title] = hotelitem

            if not exclude_hotelitem:
                for pattern in exclude_patterns:
                    if pattern.search(hotelitem.title):
                        _logger.info(
                            "Title of ad '%s' matches exclude pattern '%s'",
                            hotelitem.title,
                            pattern.pattern,
                        )
                        exclude_hotelitem = True
                        break

            if exclude_hotelitem:
                result.num_excluded += 1
                continue

            result.hotelitems.append(hotelitem)

        return result


def load_config(config_file: pathlib.Path) -> Config:
    """Load the configuration from the config path"""
    with open(config_file) as f:
        config_dict = json.load(f)

    filter_config = FilterConfig(**config_dict.get("filter", dict()))
    searches = [SearchConfig(**s) for s in config_dict.get("searches", list())]

    if not searches:
        _logger.warning("No searches configured in '%s'", config_file)

    notifications = config_dict.get("notifications", dict())
    if not notifications:
        _logger.warning("No notifications configured in '%s'", config_file)
    return Config(filter=filter_config, notifications=notifications, searches=searches)
