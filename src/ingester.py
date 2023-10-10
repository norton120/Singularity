import re
import os
from datetime import date, datetime, timedelta
from abc import ABC
from typing import Optional, TYPE_CHECKING
from imap_tools import MailBox, A
from imaplib import IMAP4

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

    ALL_MAILBOX = "All Mail"

    def __init__(self):
        self.conn = self.Conn()

    class Conn:
        def __init__(self):
            self.credentials = Credentials()
            self._refresh_mailbox()

        def _refresh_mailbox(self):
            self.mailbox = MailBox(self.credentials.host)

        def _login(self):
            self.mailbox.login(self.credentials.username, self.credentials.password)
            return self.mailbox

        def __enter__(self):
            try:
                return self._login()
            except IMAP4.error:
                self._refresh_mailbox()
                return self._login()

        def __exit__(self, exc_type, exc_value, traceback):
            self.mailbox.logout()


    def get_mailboxes(self) -> list:
        """get all mailboxes"""
        with self.conn as mailbox:
            box_list = mailbox.folder.list()
            return [f.name for f in list(filter(lambda x: "\\Noselect" not in x.flags, box_list))]

    def get_emails_headers_since(self, since: int|None = 1) -> list:
        """get all emails since n days, do not mark them read (yet)"""
        with self.conn as mailbox:
            mailbox.folder.set(self.ALL_MAILBOX)
            return [m for m in mailbox.fetch(A(date_gte=date.today() - timedelta(days=since)),
                                             headers_only=True,
                                             bulk=True,
                                             mark_seen=False)]


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
    ALL_MAILBOX = "[Gmail]/All Mail"


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
            title,
            start=start,
            end=end,
            description=body,
            location=location)
        client.add_event(event)

