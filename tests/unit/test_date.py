from app.utils import transform_date, get_dates_until_next_sunday
import pytest
import datetime as dt

@pytest.mark.parametrize(
    ["match", "result"], [
        ("/dia 09-04", "2024-04-09"),
        ("/dia 9/4", "2024-04-09"),
        ("/dia 12-11", "2024-11-12"),
        ("/dia 7/3", "2024-03-07"),
        ("/dia12-04", "2024-04-12"),
    ]
)
def test_transform_date_ok (match: str, result: str):
    assert transform_date(match) == ( True, result )

@pytest.mark.parametrize(
    ["match", "result"], [
        ("/dia 32-01", "day is out of range for month"),
        ("/dia 12-13", "month must be in 1..12"),
        ("/dia 00-10", "day is out of range for month"),
        ("/dia 12/00", "month must be in 1..12"),
        ("dia 09-04", "Invalid format")
    ]
)
def test_transform_date_error (match: str, result: str):
    assert transform_date(match) == ( False, result )

@pytest.mark.parametrize(
    ["today_date", "expected_dates"], [
        ( dt.datetime(2024, 8, 5), [
            "2024-08-05", "2024-08-06", "2024-08-07",
            "2024-08-08", "2024-08-09", "2024-08-10", "2024-08-11"
        ] ),
        (
        dt.datetime(2024, 8, 6), [
            "2024-08-06", "2024-08-07", "2024-08-08", "2024-08-09", "2024-08-10", "2024-08-11"
        ] ),
        ( dt.datetime(2024, 8, 10), [ "2024-08-10", "2024-08-11" ] ),
        ( dt.datetime(2024, 8, 11), [ "2024-08-11" ] ),
    ]
)
def test_get_dates_until_next_sunday (today_date, expected_dates):
    assert get_dates_until_next_sunday(today_date) == expected_dates
