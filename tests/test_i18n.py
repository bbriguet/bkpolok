from datetime import date, datetime

from django.conf import settings
from django.utils import formats, translation
from django.utils.dateformat import format as date_format


def test_site_language_is_english():
    assert settings.LANGUAGE_CODE == "en"
    assert settings.TIME_ZONE == "Europe/Zurich"


def test_dates_use_the_swiss_format():
    with translation.override("en"):
        assert formats.date_format(date(2008, 5, 19)) == "19.05.2008"
        assert formats.date_format(date(2008, 5, 19), "SHORT_DATE_FORMAT") == "19.05.2008"
        assert formats.time_format(datetime(2008, 5, 19, 14, 30)) == "14:30"
        assert date_format(datetime(2008, 5, 19, 14, 30), "d.m.Y H:i") == "19.05.2008 14:30"


def test_swiss_date_input_is_accepted():
    with translation.override("en"):
        assert "%d.%m.%Y" in formats.get_format("DATE_INPUT_FORMATS")


def test_numbers_use_the_swiss_separators():
    with translation.override("en"):
        assert (
            formats.number_format(1234567.5, decimal_pos=2, force_grouping=True) == "1’234’567.50"
        )
        assert formats.get_format("FIRST_DAY_OF_WEEK") == 1
