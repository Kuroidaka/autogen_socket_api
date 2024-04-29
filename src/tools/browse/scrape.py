from src.tools.browse.summarize import summary
import asyncio
from pyppeteer.launcher import launch
from pydantic import BaseModel, Field
from typing import Type
from langchain.tools import BaseTool
# from asyncer import asyncify
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from multiprocessing import Process, Queue
import asyncio
import requests
import json
import os

class ScrapeWebsiteInput(BaseModel):
    """Inputs for scrape_website"""
    objective: str = Field(
        description="The goal of scraping the website, e.g. any specific type of information you are looking for")
    url: str = Field(description="The url of the website you want to scrape")


class ScrapeWebsiteTool(BaseTool):
    name = "scrape_website"
    description = "useful when you need to get data from a website url, passing both url and objective to the function; DO NOT make up any url, the url should only be from the search results"
    args_schema: Type[BaseModel] = ScrapeWebsiteInput

    async def _run(self, url: str, objective: str):
        # Ensure this method is properly awaited wherever it's called
        queue = Queue()
        p = Process(target=scrape, args=(queue, url, objective))
        p.start()
        p.join()
        
        text = queue.get() 
        return text


    async def _arun(self, url: str, objective: str):
        # Since _run is now async, _arun is unnecessary if it just calls _run
        # This method could be removed or used for a different synchronous adaptation if needed
        return await self._run(url, objective)
def scrape(queue, url: str, objective: str):
    async def async_scrape():
        browser = None
        try:
            print("Scraping website...")
            
            print("url", url)
            print("objective", objective)
            browser = await launch({
                'executablePath': "/opt/homebrew/bin/chromium",
                'args': ['--no-sandbox'],
                'headless': True
            })
            page = await browser.newPage()
            await page.goto(url, {
                'waitUntil': "load"
            })
            await page.waitForSelector('body')
            
            text = await page.plainText()

            if text is not None:
                if len(text) > 8000:
                    text = await summary(text, objective)
                print(text)
                return text
            else:
                return "No content found after scrape."

        except Exception as e:
            print("Error occurred:", str(e))
            return "An error occurred during scraping website."
            # raise InternalServerError(str(e))

        finally:
            if browser:
                await browser.close()
    
    async def serp_scrape(url, objective):
        try:
            serp_url = "https://scrape.serper.dev"
            serper_token = os.getenv("SERPER_API_KEY")

            payload = json.dumps({
                "url": url
            })
            headers = {
                'X-API-KEY': serper_token,
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", serp_url, headers=headers, data=payload)
            if response.status_code != 200:
                return f"error while scraping url: {url}"
            
            text = json.dumps(response.text)
            if text is not None:
                if len(text) > 8000:
                    print("Summarizing")
                    text = await summary(text, objective)
                return text
            else:
                return "No content found or content."

        except Exception as e:
            print("ERROR-SCRAPE:", str(e))
            raise InternalServerError(str(e))
    # result = asyncio.run(async_scrape())
    result = asyncio.run(serp_scrape(url, objective))
    queue.put(result)
# Example usage
# asyncio.run(scrape('https://www.binance.com/vi/price/bitcoin', 'Get the current price of Bitcoin'))
