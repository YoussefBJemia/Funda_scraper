# config.py - Configuration management
import os
import json
import csv
import re
from Scraper.utils import CleanerUtils

clean_name = CleanerUtils.clean_name

class Config:
    def __init__(self, base_dir=None):
        # Set up directory paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = base_dir or os.path.dirname(script_dir)
        self.scraper_dir = os.path.join(self.base_dir, "Scraper/")
        self.data_dir = os.path.join(self.base_dir, "data/")
        self.scraped_data_dir = os.path.join(self.base_dir, "data/scraped/")
        
        # Ensure directories exist
        os.makedirs(self.scraped_data_dir, exist_ok=True)
        
        # Set up file paths
        self.available_location_queries_file = os.path.join(self.data_dir, 'plaats_provinc_nl.csv')
        self.search_query_file = os.path.join(self.data_dir, 'search_query.json')
        
    def load_search_query(self):
        """Load search query configuration from file"""
        try:
            with open(self.search_query_file, mode='r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading search query: {e}")
            return {}
    
    def load_location_queries(self):
        """Load available location queries from CSV file"""
        try:
            with open(self.available_location_queries_file, mode='r', encoding='utf-8') as file:
                return list(csv.DictReader(file))
        except Exception as e:
            print(f"Error loading location queries: {e}")
            return []
    
    def get_scraped_ids(self):
        """Get set of already scraped property IDs"""
        try:
            return {int(re.findall(r'\d+', x)[0]) for x in os.listdir(self.scraped_data_dir) 
                   if re.findall(r'\d+', x)}
        except Exception as e:
            print(f"Error getting scraped IDs: {e}")
            return set()
    
    def get_scraped_neighborhoods(self):
        """Get set of already scraped neighborhoods"""
        scraped_neighborhoods = set()
        for filename in os.listdir(self.scraped_data_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.scraped_data_dir, filename)
                try:
                    with open(file_path, mode='r', encoding='utf-8') as file:
                        data = json.load(file)
                        city, neighborhood = data.get("city"), data.get("neighborhood")
                        if city and neighborhood:
                            scraped_neighborhoods.add(f'{city}/{neighborhood}')
                except (json.JSONDecodeError, Exception) as e:
                    continue
        
        return {CleanerUtils.clean_name(element) for element in scraped_neighborhoods}

if __name__ == "__main__":
    config = Config(base_dir=None)
    location_queries = config.load_location_queries()
    #print(location_queries)
    scraped_neighborhoods = config.get_scraped_neighborhoods()
    print(scraped_neighborhoods)
    print(f"query file in {config.search_query_file} \nbase dir is {config.base_dir}")