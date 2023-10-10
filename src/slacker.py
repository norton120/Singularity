from pydantic import BaseModel
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .settings import Settings

class Status(BaseModel):
    status_text: str | None = None
    status_emoji: str | None = None
    status_expiration: int | None = None
    dnd: bool | None = None
    dnd_expiration: int | None = None
    away: bool | None = None

    def profile(self):
        return {
            "status_text": self.status_text,
            "status_emoji": self.status_emoji,
            "status_expiration": self.status_expiration,
        }

class Slacker:
    """A slack manager for the Sinularity project."""

    def __init__(self):
        try:
            self.settings = Settings()
            self.client = WebClient(token=self.settings.slack_api_token)
        except KeyError:
            raise ValueError("SLACK_API_TOKEN environment variable not set.")

    def get_status(self):
        """Get the status of the target user."""
        try:
            profile = self.client.users_profile_get(user=self.settings.slack_user_id)
            dnd = self.client.dnd_info(user=self.settings.slack_user_id).data
            away = self.client.users_getPresence(user=self.settings.slack_user_id).data

            return Status(**profile["profile"],
                          dnd=dnd["snooze_enabled"],
                          dnd_expiration=dnd.get("snooze_endtime"),
                          away=away["manual_away"])
        except SlackApiError as e:
            raise ValueError(f"Error fetching status: {e}")

    def set_status(self, status: "Status"):
        """Set the status and DND for the target user."""
        try:
            self.client.users_profile_set(user=self.settings.slack_user_id,
                                          profile=status.profile())
            if status.dnd:
                self.client.dnd_setSnooze(num_minutes=status.dnd_expiration)
            else:
                self.client.dnd_endSnooze()
            away_status = "away" if status.away else "auto"
            self.client.users_setPresence(presence=away_status)
        except SlackApiError as e:
            raise ValueError(f"Error setting status: {e}")

