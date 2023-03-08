import pytest
import pathlib

from booking_scraper.cli import run


@pytest.mark.asyncio
async def test_run():
    data_store_file = pathlib.Path("tests/datastore.json")
    config_file = pathlib.Path("config.json")
    send_notifications = True
    kwargs = {}

    # Call the run function with the test arguments
    await run(data_store_file, config_file, send_notifications, **kwargs)
