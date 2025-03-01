import asyncio
import os
import csv
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
import json
import time
from random import randint
import re
from utils import CommonFunctions, CleanerUtils

clean_scraped_record = CleanerUtils.clean_scraped_record

class Scraper:
    """Handles scraping individual property listings"""

    # 1. Helper Methods (Utility functions)
    @staticmethod
    def collect_row_info(node):
        """Extract label and value from a data row"""
        if 'EnergyLabel' in node:
            value_idx = node['EnergyLabel']
        elif 'Value' in node:
            value_idx = node['Value']
        else:
            value_idx = None

        if 'Label' in node:
            id_index = node['Label']
        elif 'Id' in node:
            id_index = node['Id']
        else:
            id_index = None

        return id_index, value_idx

    @staticmethod
    def is_row(data, idx_node):
        """Check if section is a row or category in the table"""
        idx = data[idx_node]['KenmerkenList']
        return data[idx] == []

    # 2. Data Extraction Methods
    @staticmethod
    def extract_house_data_from_soup(soup):
        """Extract property data from an individual listing page"""
        if not soup:
            return None
        
        script_tag = soup.find('script', id="__NUXT_DATA__")
        if script_tag:
            try:
                data = json.loads(script_tag.string)
                return Scraper.collect_house_info(data)
            except Exception as e:
                print(f"Failed to extract house data: {e}")
        return None

    @staticmethod
    def collect_house_info(data):
        """Process raw JSON data into structured property information"""
        try:
            global_path = data[4]
            address_path = global_path['address']
            features_path = data[global_path['features']]
            category_path = global_path['objectType']
            saleshistory_path = global_path.get('salesHistory', -1)
            
            house_info = {}
            house_info['category'] = data[category_path]
            
            # Collect address information
            Scraper.collect_address(data, address_path, house_info)
            
            # Collect property features
            Scraper.collect_features(data, features_path, house_info)
            
            # Collect sales history if available
            Scraper.collect_saleshistory(data, saleshistory_path, house_info)
            
            return house_info
        except Exception as e:
            print(f"Error collecting house info: {e}")
            return None

    @staticmethod
    def collect_address(data, address_path, house_info):
        """Extract address information from property data"""
        try:
            address_section = data[address_path]
            title_path = address_section['addressTitle']
            neighborhood_section = data[address_section['neighborhood']]
            neighborhood_path = neighborhood_section['name']
            city_path = address_section['city']
            postcode_path = address_section['postcode']
            province_path = address_section['province']
            
            # Update house_info directly
            house_info['address'] = data[title_path]
            house_info['neighborhood'] = data[neighborhood_path]
            house_info['city'] = data[city_path]
            house_info['postcode'] = data[postcode_path]
            house_info['province'] = data[province_path]
        except Exception as e:
            print(f"Error collecting address: {e}")

    @staticmethod
    def collect_features(data, features_path, house_info):
        """Extract property features from data"""
        try:
            for first_node in features_path:  # Iterate over all elements in features_path
                stack = [first_node]  # Initialize stack for each new first_node
                while stack:
                    idx_node = stack.pop()
                    node = data[idx_node]
                    
                    if 'KenmerkenList' in node:
                        if Scraper.is_row(data, idx_node):
                            id_index, value_idx = Scraper.collect_row_info(node)
                            if id_index is not None and value_idx is not None:
                                house_info[data[id_index]] = data[value_idx]
                        else:
                            idx = node['KenmerkenList']
                            stack.extend(data[idx])
                    else:
                        id_index, value_idx = Scraper.collect_row_info(node)
                        if id_index is not None and value_idx is not None:
                            house_info[data[id_index]] = data[value_idx]
        except Exception as e:
            print(f"Error collecting features: {e}")

    @staticmethod
    def collect_saleshistory(data, saleshistory_path, house_info):
        """Extract sales history from property data"""
        if saleshistory_path == -1:
            return
            
        try:
            saleshistory_section = data[saleshistory_path]['rows']
            for idx_node in data[saleshistory_section]:
                node = data[idx_node]
                id_index, value_idx = Scraper.collect_row_info(node)
                house_info[data[id_index]] = data[value_idx]
        except Exception as e:
            print(f"Error collecting sales history: {e}")

    # 3. Main Processing Methods
    @staticmethod
    async def fetch_house_description_page(url, session):
        """Fetch an individual property listing page and extract data"""
        soup = await CommonFunctions.fetch_html_from_url(url, session)
        if soup:
            return Scraper.extract_house_data_from_soup(soup)
        return None

    @staticmethod
    async def process_single_house(url, session):
        """Fetch and clean a record for a single property listing"""
        house_info = await Scraper.fetch_house_description_page(url, session)
        if house_info:
            house_info["link"] = url
            house_info["ID"] = int(url.strip("/").split("/")[-1])
            #clean_scraped_record(house_info)  # This is imported directly from cleaner module
            return clean_scraped_record(house_info)
        return None

    # 4. Async Methods
    @staticmethod
    async def process_multiple_houses(unscraped_links, session=None, batch_size=10):
        """Process multiple house links in batches, optionally using an existing session"""
        all_house_data = []
        
        # If no session is provided, create a new one
        if session is None:
            async with AsyncSession() as new_session:
                await new_session.get("https://www.funda.nl/")  # Initial request to set up session
                return await Scraper._process_multiple_houses_internal(
                    unscraped_links, new_session, batch_size
                )
        else:
            # Use the provided session
            return await Scraper._process_multiple_houses_internal(
                unscraped_links, session, batch_size
            )

    @staticmethod
    async def _process_multiple_houses_internal(unscraped_links, session, batch_size):
        """Internal method to process multiple house links with a given session"""
        all_house_data = []
        
        # Process links in batches to control concurrency
        for i in range(0, len(unscraped_links), batch_size):
            await asyncio.sleep(1 + randint(0, 3))
            
            current_batch_urls = unscraped_links[i:i + batch_size]
            current_batch_tasks = [
                Scraper.process_single_house(link, session) 
                for link in current_batch_urls
            ]
            current_batch_results = await asyncio.gather(*current_batch_tasks)
            
            # Filter out None results and add valid ones to the list
            for result in current_batch_results:
                if result:
                    all_house_data.append(result)
        
        return all_house_data


async def main():
    # Initialize the session
    async with AsyncSession() as session:
        # Define the URL of the property listing
        url = "https://www.funda.nl/detail/koop/amsterdam/appartement-van-spilbergenstraat-77-h/43881691/"
        
        scraper = Scraper()
        
        # Fetch and extract property data
        house_info = await scraper.process_single_house(url, session)
        # Print the extracted data
        if house_info:
            print("Extracted Property Data:")
            for key, value in house_info.items():
                print(f"{key}: {value}")
        else:
            print("Failed to extract property data.")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
