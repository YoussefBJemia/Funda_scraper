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
import sys

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

    def print_progress_bar(self, current, total, prefix='', suffix='', length=50, fill='█'):
        percent = ("{0:.1f}").format(100 * (current / float(total)))
        filled_length = int(length * current // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
        sys.stdout.flush()
        if current == total:
            sys.stdout.write('\n')

    async def process_and_save(self, url, session):
        # First, collect all the links
        print("📋 Collecting house listings...")
        result = await self.collector.fetch_house_links_from_multiple_pages_async(url, session)
        unscraped_links = list(result)
        print(f"🔍 Found {len(unscraped_links)} listings to process")
        
        # Setup for progress tracking
        houses_saved = 0
        total_links = len(unscraped_links)
        
        # Process houses in batches, with progress updates
        batch_size = 10
        scraped_data = []
        
        for i in range(0, total_links, batch_size):
            batch = unscraped_links[i:i+batch_size]
            batch_results = await self.scraper.process_multiple_houses(batch, session, batch_size)
            scraped_data.extend(batch_results)
            
            # Update progress
            progress = min(i + batch_size, total_links)
            self.print_progress_bar(progress, total_links, 
                                    prefix=f'Progress:', 
                                    suffix=f'({progress}/{total_links})')
        
        # Save the new houses
        houses_to_save = [house for house in scraped_data if house["ID"] not in self.scraped_ids]
        
        print(f"\n💾 Saving {len(houses_to_save)} new properties...")
        for i, new_house in enumerate(houses_to_save):
            self.save_house_data(new_house)
            self.scraped_ids.add(new_house["ID"])
            houses_saved += 1
            
            # Update save progress
            self.print_progress_bar(i + 1, len(houses_to_save), 
                                   prefix='Saving:', 
                                   suffix=f'({i+1}/{len(houses_to_save)})')

        return houses_saved, len(unscraped_links)

    async def run(self):
        total_start_time = time.time()
        print("🏠 Starting Funda housing data collection...")

        async with AsyncSession() as session:
            await session.get("https://www.funda.nl/")
            print("✓ Connected to Funda")

            params = {k: v for k, v in self.search_query.items() if k != 'selected_area'}
            total_houses_saved = 0
            areas_processed = 0

            for area in self.search_queries:
                area_start_time = time.time()
                url = self.url_builder.build_url(selected_area=area, **params)
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