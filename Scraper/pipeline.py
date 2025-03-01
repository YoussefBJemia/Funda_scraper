import asyncio
import os
import json
import time
from random import randint
from curl_cffi.requests import AsyncSession
from Scraper.url_builder import UrlBuilder
from Scraper.collector import Collector
from Scraper.scraper import Scraper
from Scraper.utils import QueryUtils, CleanerUtils
from Scraper.config import Config

class FundaScraperPipeline:
    def __init__(self, base_dir=None):
        self.config = Config(base_dir=base_dir)
        self.url_builder = UrlBuilder()
        self.collector = Collector()
        self.scraper = Scraper()

        self.scraped_data_dir = self.config.scraped_data_dir
        self.search_query = self.config.load_search_query()
        self.available_location_queries = self.config.load_location_queries()
        self.scraped_ids = self.config.get_scraped_ids()
        self.scraped_neighborhoods = self.config.get_scraped_neighborhoods()

        self.search_queries = QueryUtils.create_queries_for_selected_areas(
            self.search_query, self.available_location_queries
        )

    def save_house_data(self, house_info, output_dir=None):
        if not output_dir:
            output_dir = self.scraped_data_dir
        house_id = int(house_info["link"].strip("/").split("/")[-1])
        with open(f'{output_dir}/{house_id}.json', 'w') as outfile:
            json.dump(house_info, outfile)

    async def process_and_save(self, url, session):
        result = await self.collector.fetch_house_links_from_multiple_pages_async(url, session)
        unscraped_links = list(result)

        scraped_data = await self.scraper.process_multiple_houses(unscraped_links, session, batch_size=10)

        houses_to_save = [house for house in scraped_data if house["ID"] not in self.scraped_ids]

        for new_house in houses_to_save:
            self.save_house_data(new_house)
            self.scraped_ids.add(new_house["ID"])

        return len(houses_to_save), len(unscraped_links)

    async def run(self):
        print(f"search queries is {self.search_queries}")
        total_start_time = time.time()
        print("🏠 Starting Funda housing data collection...")

        async with AsyncSession() as session:
            await session.get("https://www.funda.nl/")
            print("✓ Connected to Funda")

            params = {k: v for k, v in self.search_query.items() if k != 'selected_area'}
            total_houses_saved = 0
            areas_processed = 0
            print(f"search query is {self.search_query}\nparams is {params}")

            for area in self.search_queries:
                area_start_time = time.time()
                url = self.url_builder.build_url(selected_area=area, **params)
                print(f"url is {url}")
                number_observations = self.url_builder.get_number_results(url)
                print(f"\n📍 Area: {area} - {number_observations} listings found")

                if number_observations < 9900:
                    houses_saved, houses_processed = await self.process_and_save(url, session)
                    total_houses_saved += houses_saved
                    areas_processed += 1

                    area_time = time.time() - area_start_time
                    print(f"✓ {area}: Processed {houses_processed} listings, saved {houses_saved} new properties ({area_time:.2f} seconds)")
                else:
                    print(f"⚠️ {area} has too many listings, processing by neighborhood...")
                    neighborhoods_processed = 0
                    neighborhood_houses_saved = 0
                    neighborhoods_total = len(self.search_queries[area])

                    for neighborhood in self.search_queries[area]:
                        neighborhood_start_time = time.time()
                        if neighborhood in self.scraped_neighborhoods:
                            print(f"  ↷ Skipping {neighborhood} (already scraped)")
                            continue

                        try:
                            neighborhood_url = self.url_builder.build_url(selected_area=neighborhood, **params)
                            houses_saved, houses_processed = await self.process_and_save(neighborhood_url, session)
                            neighborhood_houses_saved += houses_saved
                            neighborhoods_processed += 1

                            neighborhood_time = time.time() - neighborhood_start_time
                            print(f"  ✓ {neighborhood}: Saved {houses_saved} new properties ({neighborhood_time:.2f} seconds)")
                        except Exception as e:
                            print(f"  ✗ Error in {neighborhood}: {str(e)[:50]}...")

                    total_houses_saved += neighborhood_houses_saved
                    areas_processed += 1
                    area_time = time.time() - area_start_time
                    print(f"✓ {area}: Processed {neighborhoods_processed}/{neighborhoods_total} neighborhoods, saved {neighborhood_houses_saved} properties ({area_time:.2f} seconds)")

            total_time = time.time() - total_start_time
            print(f"\n✨ Collection complete! Processed {areas_processed} areas, saved {total_houses_saved} new properties to {self.scraped_data_dir}")
            print(f"⏱️ Total execution time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")

# Entry point for execution
if __name__ == "__main__":
    scraper = FundaScraperPipeline()
    asyncio.run(scraper.run())