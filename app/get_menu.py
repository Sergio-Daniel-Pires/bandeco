import asyncio
import dataclasses as dc
import datetime
import logging
import traceback
from typing import Any

import pytz
from playwright.async_api import async_playwright
from playwright.async_api._generated import Browser, BrowserContext, Page

URL_DEFAULT = "https://sistemas.prefeitura.unicamp.br/apps/cardapio/index.php"

logger = logging.getLogger(__name__)
timezone = pytz.timezone("America/Sao_Paulo")

@dc.dataclass
class BotBase:
    # Playwright things
    browser: Browser = dc.field(default=None)
    context: BrowserContext = dc.field(default=None)
    headless: bool = dc.field(default=True)

    url: str = dc.field(default=URL_DEFAULT)
    extra_date: str = dc.field(default="")

    user_agent: str = dc.field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        )
    )

    # Menu things
    run_all: bool = dc.field(default=False)

    year = str(datetime.datetime.now(tz=timezone).year)

    def __post_init__ (self):
        if self.extra_date:
            self.url = f"{self.url}?d={self.extra_date}"

    async def get_menu (self) -> list[dict[str, Any]]:
        results = {}

        try:
            async with async_playwright() as playwright:
                self.browser = await playwright.chromium.launch(headless=self.headless)
                self.context = await self.browser.new_context(user_agent=self.user_agent)

                page = await self.context.new_page()

                await page.route(
                    "**/*", lambda route: route.abort()
                    if route.request.resource_type == "image" else route.continue_()
                )

                await page.goto(self.url)

                active_page = await page.query_selector("li.active")
                active_page = (await active_page.inner_text()) if active_page is not None else None

                if (active_page is not None and active_page.lower() == "segunda") or self.run_all:
                    page = await self.get_multiple_days(page, results)

                else:
                    page = await self.get_one_day(page, results)

        except Exception as exc:
            logger.error(f"Error: {traceback.format_exc()}")
        
        finally:
            await self.browser.close()

        return results

    async def get_one_day (self, page: Page, results: dict[str, Any]) -> Page:
        await page.wait_for_selector(".row")

        # Get date like "06/08" and converts to "2024-08-06"
        date = (await (await page.query_selector("a.navbar-brand")).inner_text()) or ""
        date = date.split(" ")[-1].split("/")
        date = f"{self.year}-{date[1]}-{date[0]}"

        sections = await page.query_selector_all(".menu-section")

        results[date] = {}
        for section in sections:
            title = await (await section.query_selector("h2")).inner_text()

            protein = await (await section.query_selector(".menu-item-name")).inner_text()

            description = await (
                await section.query_selector(".menu-item-description")
            ).inner_text()

            description = description.split(" \n")[0]

            results[date][title] = { "protein": protein, "description": description }

        return page

    async def get_multiple_days (self, page: Page, results: dict[str, Any]) -> Page:
        days = await page.query_selector_all("li > a")

        for num_day in range(1, len(days) + 1):
            page = await self.get_one_day(page, results)

            if len(days) <= num_day:
                break
            
            day = (await page.query_selector_all("li > a"))[num_day]
            await day.click()

        return page

if __name__ == "__main__":
    bot = BotBase(run_all=True)
    asyncio.run(bot.get_menu())
