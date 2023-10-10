import re
import os
from datetime import date, datetime, timedelta
from abc import ABC
from typing import Optional, TYPE_CHECKING
from imaplib import IMAP4_SSL
from email import message_from_bytes
from email.header import decode_header

from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

if TYPE_CHECKING:
    from gcsa.free_busy import TimeRange


class Credentials:
    host: str
    port: int
    username: str
    password: str

    def __init__(self):
        for prop in ("host", "port", "username", "password"):
            envar = f"IMAP_{prop.upper()}"
            try:
                setattr(self, prop, os.environ[envar])
            except KeyError:
                raise Exception(f"Missing {envar} environment variable")

class EmailIngester(ABC):

    def __init__(self):
        credentials = Credentials()
        self.imap = IMAP4_SSL(credentials.host, credentials.port)
        self.imap.login(credentials.username, credentials.password)

    def get_folders(self) -> list[str]:
        """get all available folders"""
        _, folders = self.imap.list()
        return [self.parse_folder_name(f) for f in folders]

    def get_emails_for_folder(self, folder:str) -> list:
        """get all emails for a given folder"""
        self.imap.select(folder)
        _, data = self.imap.search(None, "ALL")
        for uid in data[0].split():
            _, data = self.imap.fetch(uid, "(RFC822)")
            yield data

    @classmethod
    def parse_folder_name(self, list_string:str) -> str:
        raise NotImplementedError

class CalendarIngester(ABC):
    """get and set calendar events from a calendar service"""

    def get_busy_for_date(self,
                          date:date,
                          after: Optional[datetime] = None,
                          before: Optional[datetime] = None,
                         ) -> list:
        """get all busy windows for a given date, optionally in a time window"""
        raise NotImplementedError

    def set_event(self,
                  start: datetime,
                  end: datetime,
                  title: str,
                  body: Optional[str] = None,
                  location: Optional[str] = None) -> None:
        """add an event to a calendar"""
        raise NotImplementedError


class GmailIngester(EmailIngester):

    @classmethod
    def parse_folder_name(cls, list_string:str) -> str:
        """gmail uses a special string pattern for folder names.
        We decode it to the exposed folder here.

        Args:
            list_string (str): the binary string returned by the IMAP LIST command
        """
        pattern = r'\(.+\)\s"/"\s"(.+)"'
        try:
            list_string = list_string.decode('utf-8')
        except AttributeError:
            pass
        try:
            return re.search(pattern, list_string).group(1)
        except IndexError:
            raise ValueError(f"Folder string from Gmail does not follow normal pattern: {list_string}")

class GoogleCalendarIngester(CalendarIngester):
    """get and set calendar events from Google Calendar"""

    def get_busy_for_date(self,
                          date: date,
                          after: datetime | None = None,
                          before: datetime | None = None) -> list["TimeRange"]:

        client = GoogleCalendar()
        busy_times = client.get_free_busy(
            [c.id for c in client.get_calendar_list()],
            time_min=date,
            time_max=date + timedelta(days=1))
        busy_ranges = [event for cal in list(busy_times.calendars.values()) for event in cal]
        return busy_ranges

    def set_event(self,
                  start: datetime,
                  end: datetime,
                  title: str,
                  body: Optional[str] = None,
                  location: Optional[str] = None) -> None:

        client = GoogleCalendar()
        event = Event(
            title=title,
            start=start,
            end=end,
            description=body,
            location=location)
        client.add_event(event)

