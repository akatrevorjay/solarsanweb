
from django.utils import timezone
import datetime, time


"""
Exceptions
"""

class Error(Exception):
    """ Base Error """
    pass

class NotImplemented(Error):
    """ This function still needs to be written """
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



