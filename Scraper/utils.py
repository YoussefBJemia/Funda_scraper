import unicodedata
import re
from curl_cffi import requests
from lxml import html
import asyncio
import os
import ast
import csv
import json
import time
from random import randint
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from datetime import datetime, timedelta
from typing import List, Union, Dict, Any
import pandas as pd
from dateutil.parser import parse


class CommonFunctions:
    @staticmethod
    async def fetch_html_from_url(url, session):
        """Fetch HTML from a URL with retry logic"""
        max_retries = 5
        backoff_factor = 3
        timeout = 10
        
        for attempt in range(max_retries):
            try:
                response = await session.get(
                    url, 
                    impersonate="chrome",
                    timeout=timeout
                )
                
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup
            
            except Exception as e:
                # Handle different types of errors
                wait_time = backoff_factor ** attempt
                
                if "timeout" in str(e).lower():
                    print(f"Timeout error for {url}: {e}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                if "403" in str(e):
                    print(f"Access Forbidden (403) for {url}: Possible anti-bot detection. Skipping.")
                    break
                    
                if "429" in str(e):
                    wait_time *= 2  # Double wait time for rate limits
                    print(f"Rate limited (429) for {url}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                if any(str(code) in str(e) for code in range(500, 600)):
                    print(f"Server error for {url}: {e}. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                print(f"Failed to process URL: {url}. Error: {e}")
                break
        
        print(f"Skipping URL after {max_retries} retries: {url}")
        return None

    @staticmethod
    def save_filters_to_json(filters, filename=None):
        """Save the filter dictionary to a JSON file."""
        if filename is None:
            print("Error: No filename provided")
            return

        try:
            with open(filename, 'w') as json_file:
                json.dump(filters, json_file, indent=4)
            print(f"Filters saved to {filename}")
        except Exception as e:
            print(f"Failed to save filters to JSON: {e}")

class QueryUtils:
    @staticmethod
    def create_queries_for_selected_areas(search_query, available_location_queries):
        """
        Create queries for selected areas based on search query and available location queries.
        
        Args:
            search_query (dict): The search query configuration
            available_location_queries (list): List of available location queries
            
        Returns:
            dict: Dictionary with area keys and corresponding query lists
        """
        selected_areas = search_query.get('selected_area', None)
        if selected_areas is None:
            # Initialize with "All" key
            stack_neighborhoods_queries = {}
            
            # Get all unique gemeente and add them as keys
            unique_gemeentes = set()
            for row in available_location_queries:
                gemeente = CleanerUtils.clean_name(row["gemeente"])
                unique_gemeentes.add(gemeente)
            
            # Add each gemeente as a key in the dictionary
            for gemeente in unique_gemeentes:
                stack_neighborhoods_queries[f"gemeente-{gemeente}"] = []
            
            # Populate the queries for each gemeente
            for row in available_location_queries:
                gemeente = CleanerUtils.clean_name(row["gemeente"])
                queries = eval(row["query"]) if isinstance(row["query"], str) and row["query"] != "[]" else row["query"]
                stack_neighborhoods_queries[f"gemeente-{gemeente}"].extend(queries)
        else:
            # Initialize with selected areas as keys
            stack_neighborhoods_queries = {area: [] for area in selected_areas}
            
            for search_term in selected_areas:
                # Determine the search type
                if search_term.startswith("gemeente-"):
                    search_type = "gemeente"
                    # Extract the actual gemeente name from the search term
                    search_value = search_term.replace("gemeente-", "")
                elif search_term.startswith("provincie-"):
                    search_type = "provincie"
                    # Extract the actual provincie name from the search term
                    search_value = search_term.replace("provincie-", "")
                else:
                    search_type = "plaats"
                    search_value = search_term
                
                # Loop through all available location queries
                for row in available_location_queries:
                    queries = eval(row["query"]) if isinstance(row["query"], str) and row["query"] != "[]" else row["query"]
                    
                    # Match based on search type
                    if search_type == "plaats" and CleanerUtils.clean_name(row["plaats"]) == search_value:
                        stack_neighborhoods_queries[search_term].extend(queries)
                    elif search_type == "gemeente" and CleanerUtils.clean_name(row["gemeente"]) == search_value:
                        stack_neighborhoods_queries[search_term].extend(queries)
                    elif search_type == "provincie" and CleanerUtils.clean_name(row["provincie"]) == search_value:
                        stack_neighborhoods_queries[search_term].extend(queries)
        return stack_neighborhoods_queries


class CleanerUtils:
    """Utility class for cleaning scraped records and data."""
    
    @staticmethod
    def clean_name(name: str) -> str:
        """
        Clean a location name by normalizing it.
        
        Args:
            name: String to be cleaned
            
        Returns:
            Cleaned and normalized string
        """
        # Remove single quotes
        name = name.replace("'", "")
        
        # Convert to lowercase
        name = name.lower()
        
        # Replace spaces with hyphens
        name = name.replace(" ", "-")
        
        # Remove parentheses
        name = re.sub(r"[()]", "", name)
        
        # Remove periods
        name = name.replace(".", "")
        
        # Normalize accented characters and replace specific ones
        name = unicodedata.normalize("NFKD", name)
        name = name.encode("ascii", "ignore").decode("utf-8")  # Remove diacritics
        
        return name
    
    @staticmethod
    def clean_price(x: str) -> float:
        """
        Clean the 'price' and transform from string to float.
        
        Args:
            x: Price string (e.g. "€ 350.000")
            
        Returns:
            Price as a float value
        """
        try:
            return float(str(x).split(" ")[1].replace(".", "").replace(",", "."))
        except ValueError:
            return 0
        except IndexError:
            return 0

    @staticmethod
    def clean_area(area_field: str) -> float:
        """
        Clean the area field and transform from string to float.
        
        Args:
            area_field: Area string (e.g. "120 m²")
            
        Returns:
            Area as a float value
        """
        try:
            return float(str(area_field).replace(",", ".").split(" m")[0])
        except ValueError:
            return 0
        except IndexError:
            return 0
    
    @staticmethod
    def find_keyword_from_regex(x: str, pattern: str) -> int:
        """
        Extract a numeric value from a string using regex.
        
        Args:
            x: String to search in
            pattern: Regex pattern to match
            
        Returns:
            Extracted numeric value as an integer
        """
        result = re.findall(pattern, x)
        if len(result) > 0:
            result = "".join(result[0])
            x = result.split(" ")[0]
        else:
            x = 0
        return int(x)

    @staticmethod
    def find_n_room(x: str) -> int:
        """
        Find the number of rooms from a string.
        
        Args:
            x: String containing room information
            
        Returns:
            Number of rooms as an integer
        """
        pattern = r"(\d{1,2}\s{1}kamers{0,1})|(\d{1,2}\s{1}rooms{0,1})"
        return CleanerUtils.find_keyword_from_regex(x, pattern)

    @staticmethod
    def find_n_bedroom(x: str) -> int:
        """
        Find the number of bedrooms from a string.
        
        Args:
            x: String containing bedroom information
            
        Returns:
            Number of bedrooms as an integer
        """
        pattern = r"(\d{1,2}\s{1}slaapkamers{0,1})|(\d{1,2}\s{1}bedrooms{0,1})"
        return CleanerUtils.find_keyword_from_regex(x, pattern)

    @staticmethod
    def find_n_bathroom(x: str) -> int:
        """
        Find the number of bathrooms from a string.
        
        Args:
            x: String containing bathroom information
            
        Returns:
            Number of bathrooms as an integer
        """
        pattern = r"(\d{1,2}\s{1}badkamers{0,1})|(\d{1,2}\s{1}bathrooms{0,1})"
        return CleanerUtils.find_keyword_from_regex(x, pattern)

    @staticmethod
    def map_dutch_month(x: str) -> str:
        """
        Map Dutch month names to English.
        
        Args:
            x: String containing Dutch month names
            
        Returns:
            String with Dutch month names replaced by English equivalents
        """
        month_mapping = {
            "januari": "January",
            "februari": "February",
            "maart": "March",
            "april": "April",
            "mei": "May",
            "juni": "June",
            "juli": "July",
            "augustus": "August",
            "september": "September",
            "oktober": "October",
            "november": "November",
            "december": "December",
        }
        for k, v in month_mapping.items():
            if x.find(k) != -1:
                x = x.replace(k, v)
        return x

    @staticmethod
    def clean_date_format(x: str) -> str:
        """
        Transform the date from string to a standardized format.
        
        Args:
            x: Date string in various formats
            
        Returns:
            Standardized date string in 'dd/mm/yyyy' format
        """
        x = x.replace("weken", "week")
        x = x.replace("maanden", "month")
        x = x.replace("Vandaag", "Today")
        x = x.replace("+", "")
        x = CleanerUtils.map_dutch_month(x)

        def delta_now(d: int):
            t = timedelta(days=d)
            return datetime.now() - t

        weekdays_dict = {
            "maandag": "Monday",
            "dinsdag": "Tuesday",
            "woensdag": "Wednesday",
            "donderdag": "Thursday",
            "vrijdag": "Friday",
            "zaterdag": "Saturday",
            "zondag": "Sunday",
        }

        try:
            if x.lower() in weekdays_dict.keys():
                date_string = weekdays_dict.get(x.lower())
                parsed_date = parse(date_string, fuzzy=True)
                delta = datetime.now().weekday() - parsed_date.weekday()
                x = delta_now(delta)

            elif x.find("month") != -1:
                x = delta_now(int(x.split("month")[0].strip()[0]) * 30)
            elif x.find("week") != -1:
                x = delta_now(int(x.split("week")[0].strip()[0]) * 7)
            elif x.find("Today") != -1:
                x = delta_now(1)
            elif x.find("day") != -1:
                x = delta_now(int(x.split("day")[0].strip()))
            else:
                x = datetime.strptime(x, "%d %B %Y")
            return x.strftime("%d/%m/%Y")

        except ValueError:
            return "na"

    @staticmethod
    def clean_energy_label(x: str) -> str:
        """
        Clean and standardize energy label format.
        
        Args:
            x: Energy label string
            
        Returns:
            Cleaned energy label string
        """
        try:
            x = x.split(" ")[0]
            if x.find("A+") != -1:
                x = ">A+"
            return x
        except IndexError:
            return x

    @staticmethod
    def clean_scraped_record(house_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a scraped house record by processing various fields.
        """
        # Create a copy to avoid modifying the original
        cleaned_info = house_info.copy()
        
        for key, value in cleaned_info.items():
            if isinstance(value, str):
                if '€' in value:
                    cleaned_info[key] = CleanerUtils.clean_price(value)
                elif 'm²' in value or 'm³' in value:
                    cleaned_info[key] = CleanerUtils.clean_area(value)

        # Handle specific fields safely
        try:
            cleaned_info['Bouwjaar'] = int(cleaned_info.get('Bouwjaar', 0))
        except ValueError:
            cleaned_info['Bouwjaar'] = 0

        cleaned_info['Energielabel'] = CleanerUtils.clean_energy_label(cleaned_info.get('Energielabel', ''))

        # Extract room counts safely
        if 'Aantal kamers' in cleaned_info:
            n_rooms = CleanerUtils.find_n_room(cleaned_info['Aantal kamers'])
            n_bedrooms = CleanerUtils.find_n_bedroom(cleaned_info['Aantal kamers'])
            cleaned_info['Kamers'] = n_rooms
            cleaned_info['Slaapkamers'] = n_bedrooms
            del cleaned_info['Aantal kamers']

        # Handle date fields safely
        for date_key in ['Aangeboden sinds', 'Verkoopdatum']:
            try:
                if date_key in cleaned_info:
                    cleaned_info[date_key] = CleanerUtils.clean_date_format(cleaned_info[date_key])
            except Exception as e:
                cleaned_info[date_key] = ''
                print(f"Error processing {date_key}: {e}")
                
        return cleaned_info
        
    @staticmethod
    def clean_string(value: str) -> str:
        """Cleans a string by removing specific characters and normalizing it."""
        value = value.replace("'", "").lower()
        value = value.replace(" ", "-").replace(".", "")
        value = re.sub(r"[()]", "", value)
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("utf-8")

if __name__ == "__main__":
    cleaner = CleanerUtils.clean_name("Gemeente Noord Holland")
    print(cleaner)