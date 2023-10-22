from typing import Optional
import datetime
from atlassian import Confluence
from logging import getLogger
import os
from pathlib import Path
import markdownify
from pydantic import BaseModel

from .settings import Settings


logger = getLogger(__name__)

class ConfluencePage(BaseModel):
    title: str
    url: str
    html_content: str

    def as_markdown(self):
        url_header = f"from [Confluence]({self.url})"
        return "\n".join([url_header, markdownify.markdownify(self.html_content)])

class Confluencer:

    def __init__(self):
        self.settings = Settings()
        self.client = Confluence(
            self.settings.atlassian_host,
            self.settings.atlassian_email,
            self.settings.atlassian_token,
            cloud=True)

    def capture_the_days_confluence_pages_in_logseq(self) -> int:
        pages = self.get_updated_pages_since()
        return self.write_pages_to_logseq(pages)

    def get_updated_pages_since(self,
            since_date:datetime.date | None = (datetime.date.today() - datetime.timedelta(days=1))) -> list:
        page_summaries = []
        for space in self._get_all_space_keys(include_user_spaces=False): # for clarity
            page_summaries.extend(self._get_updated_page_summaries_for_space(space, since_date))
        pages = []
        for page in page_summaries:
            pages.append(self._build_confluence_page(page))
        return pages

    def write_pages_to_logseq(self,
                              pages:list[ConfluencePage],
                              logseq_path:Optional[Path]=Path("/logseq/pages")) -> int:
        """Writes pages to logseq locally.

        Returns:
            returns the number of pages written
        """
        if not logseq_path.exists():
            raise FileNotFoundError(f"Logseq path {logseq_path} does not exist")
        for page in pages:
            page_title_name = "Confluence%2F" + "".join(a for a in page.title if a.isalnum() or a.isspace())
            page_path = logseq_path / f"{page_title_name}.md"
            page_path.write_text(page.as_markdown())
            NON_ROOT_UID = 1000
            NON_ROOT_GID = 1000
            os.chown(page_path, NON_ROOT_UID, NON_ROOT_GID)
        return len(pages)

    def _get_all_space_keys(self,
                            include_user_spaces:Optional[bool] = False) -> list[int]:
        all_space_keys = [s['key'] for s in self.client.get_all_spaces()['results']]
        if include_user_spaces:
            return all_space_keys
        return [s for s in all_space_keys if not s.startswith('~')]

    def _get_updated_page_summaries_for_space(self,
                            space:str,
                            since_date:datetime.date | None = (datetime.date.today() - datetime.timedelta(days=1))
                            ) -> list[dict]:
        query = f"space={space} and lastmodified >= '{since_date}'"
        try:
            results = self.client.cql(
                query,
                limit=1000).get('results')
            pages = [p for p in results if p['content']['type'] == 'page']
            return pages
        except Exception as e:
            logger.error("failed to execute cql query '%s' : %s", query, e)
            raise e
    def _build_confluence_page(self, page_summary:dict) -> ConfluencePage:
        url = f"{self.settings.atlassian_host}/wiki/spaces/{page_summary['url']}"
        title = page_summary['title']
        full_page = self.client.get_page_by_id(page_summary['content']['id'], expand='body.storage')
        html = full_page['body']['storage']['value']
        return ConfluencePage(title=title, url=url, html_content=html)