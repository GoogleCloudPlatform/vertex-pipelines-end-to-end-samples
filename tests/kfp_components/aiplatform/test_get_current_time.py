import pytest
from datetime import datetime, timezone


FAKE_TIME = datetime(2022, 1, 18, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    """Fixture to patch datetime.now() to a fixed date.

    Date used is 2022-01-18 00:00:00 (UTC).

    """

    class MyDatetime:
        def now(self):
            return FAKE_TIME

    monkeypatch.setattr("datetime.datetime", MyDatetime)


@pytest.mark.usefixtures("patch_datetime_now")
def test_get_current_time():
    """
    Test get_current_time where timestamp is a empty string
    """
    from pipelines.kfp_components.aiplatform import get_current_time

    test_time = get_current_time(timestamp="")

    assert test_time == FAKE_TIME.isoformat()


@pytest.mark.parametrize(
    "timestamp, expect",
    [
        ("2022-01-18T16:07:04.824411+00:00", "2022-01-18T16:07:04.824411+00:00"),
        ("2022-01-18T16:07:04.824411", "2022-01-18T16:07:04.824411"),
        ("2022-01-18T16:07:04", "2022-01-18T16:07:04"),
        ("2022-01-18T16:07", "2022-01-18T16:07:00"),
        ("2022-01-18T16", "2022-01-18T16:00:00"),
        ("2022-01-18", "2022-01-18T00:00:00"),
    ],
)
def test_get_input_time(timestamp: str, expect: str):
    """
    Test get_current_time with specific timestamps

    Args:
        timestamp (str): Specific timestamps in ISO 8601 format
            with or missing time part
        expect (str): expected output
    """
    from pipelines.kfp_components.aiplatform import get_current_time

    assert get_current_time(timestamp) == expect


@pytest.mark.parametrize(
    "timestamp",
    [
        (" "),
        ("18-01-2022"),
        ("18/01/2022"),
        ("01-18-2022"),
    ],
)
def test_input_time_format_error(timestamp: str):
    """[summary]

    Args:
        timestamp (str): Wrong input strings
    """
    from pipelines.kfp_components.aiplatform import get_current_time

    with pytest.raises(ValueError):
        get_current_time(timestamp)
