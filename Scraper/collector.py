import asyncio
import os
import csv
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
import json
import time
from random import randint
import re
from Scraper.utils import CommonFunctions

class Collector:
    """Handles collecting property listings from search results pages"""
    
    @staticmethod
    def extract_house_links_from_soup(soup):
        """Extract links to individual property listings from search results page"""
        if not soup:
            return None
        
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag:
            try:
                data = json.loads(script_tag.string)
                house_links = set()
                for url_link in data['itemListElement']:
                    house_links.add(url_link['url'])
                return house_links
            except Exception as e:
                print(f"Failed to extract script from soup: {e}")
        return None
    
    @staticmethod
    async def fetch_house_links_page(url, session):
        """Fetch a search results page and extract property links"""
        soup = await CommonFunctions.fetch_html_from_url(url, session)
        if soup:
            return Collector.extract_house_links_from_soup(soup)
        return None
    
    @staticmethod
    async def fetch_house_links_from_multiple_pages_async(url, session, batch_size=10):
        """Fetch property links from multiple search result pages"""
        all_house_links = set()
        page_number = 1
        found_last_page = False

        while not found_last_page and page_number < 700:
            try:
                # Process pages by batch
                await asyncio.sleep(2 + randint(0, 3))
                current_batch_urls = [f"{url}&search_result={page_number + i}" 
                                     for i in range(batch_size)]
                current_batch_tasks = [Collector.fetch_house_links_page(batch_url, session) 
                                      for batch_url in current_batch_urls]

                current_batch_results = await asyncio.gather(*current_batch_tasks)

                valid_results = []
                for result in current_batch_results:
                    if result is None:  # Found last page or error
                        found_last_page = True
                        break
                    valid_results.append(result)

                if not valid_results:
                    break

                for links in valid_results:
                    all_house_links.update(links)

                print(f"Collected url links up to page {page_number + len(valid_results) - 1}")
                page_number += batch_size

            except Exception as e:
                print(f"Error while processing page {page_number}: {e}")
                found_last_page = True

        return all_house_links

async def main():
    start_time = time.time()

    async with AsyncSession() as session:
        # Define the URL to scrape
        url = "https://www.funda.nl/zoeken/koop?selected_area=[%22provincie-noord-holland%22]"
        
        # Fetch house links from multiple pages
        house_links = await Collector.fetch_house_links_from_multiple_pages_async(url, session, batch_size=10)
        
        # Print the results
        print(f"Found {len(house_links)} house links:")
        for link in house_links:
            print(link)

    end_time = time.time()
    print(f"\nTotal time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())