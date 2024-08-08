from app.utils import verify_this_week_and_get_fish
import pytest
import asyncio

def test_verify_this_week_and_get_fish ():
    assert asyncio.run(verify_this_week_and_get_fish()) == ( True, "Fish: " )
