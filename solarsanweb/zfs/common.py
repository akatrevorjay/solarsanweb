
from django.utils import timezone
import datetime, time


"""
Exceptions
"""

class Error(Exception):
    """ Base Error """
    pass


"""
Common Funcs
"""

def parse_zfs_date(date):
    time_format = "%a %b %d %H:%M %Y"
    return timezone.make_aware(
            datetime.datetime.fromtimestamp(
                time.mktime(
                    time.strptime(date, time_format) )))



