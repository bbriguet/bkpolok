"""Formats suisses pour un site en anglais : 31.12.2026, 14:30, 1’234.50.

Django donne la priorité au module de formats de la locale sur les réglages DATE_FORMAT & co.
(USE_L10N est toujours actif depuis Django 5.0) : c'est ce module qui force les formats suisses
pour la locale « en ».
"""

DATE_FORMAT = "d.m.Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = "d.m.Y H:i"
YEAR_MONTH_FORMAT = "F Y"
MONTH_DAY_FORMAT = "j F"
SHORT_DATE_FORMAT = "d.m.Y"
SHORT_DATETIME_FORMAT = "d.m.Y H:i"
FIRST_DAY_OF_WEEK = 1  # lundi

DATE_INPUT_FORMATS = ["%d.%m.%Y", "%Y-%m-%d"]
TIME_INPUT_FORMATS = ["%H:%M:%S", "%H:%M"]
DATETIME_INPUT_FORMATS = [
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
]

DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = "’"
NUMBER_GROUPING = 3
