import datetime
from atlassian import Confluence
import markdownify

from .settings import Settings

class Confluencer:

    def __init__(self):
        settings = Settings()
        self.client = Confluence(
            settings.atlassian_host,
            settings.atlassian_email,
            settings.atlassian_token,
            cloud=True)

    def get_updated_pages_since(self,
            since_date:datetime.date | None = (datetime.date.today() - datetime.timedelta(days=1))) -> list:
        for space in self._get_all_space_names():
            updated = self.client.cql(
                f"space={space} and lastmodified >= '{since_date}'",
                limit=1000,
                expand='body.storage')

    def _get_all_space_names(self) -> list[int]:
        return [s['name'] for s in self.client.get_all_spaces()['results']]

    def _convert_page_to_markdown(self,
                                  page:dict)-> str:
        return markdownify.markdownify(page['body']['storage']['value'])

