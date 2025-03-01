""" url_builder.py - Constructs search URLs for the Funda housing website. """
from typing import Dict, Any, Optional, Union, List
from urllib.parse import quote_plus
from curl_cffi import requests
from lxml import html
import re

from filters import generate_filters, FILTERS

class UrlBuilder:
    """Handles building and parsing URLs for property searches on Funda"""
    
    # Define class-level constants
    BASE_URL = "https://www.funda.nl/zoeken/"
    
    @staticmethod
    def build_url(
        transaction_type="buy",
        selected_area="amsterdam",
        price_min=None, price_max=None,
        object_type=None,
        availability=None,
        floor_area_min=None, floor_area_max=None,
        plot_area_min=None, plot_area_max=None,
        rooms_min=None, rooms_max=None,
        bedrooms_min=None, bedrooms_max=None,
        bathrooms_min=None, bathrooms_max=None,
        construction_type=None,
        construction_period=None, 
        parking_facility=None, 
        garage_type=None
    ) -> str:
        """
        Build a search URL for Funda based on the provided parameters.
        """
        # Create filter dictionary using the filters structure
        filters = generate_filters(
            transaction_type=transaction_type,
            selected_area=selected_area,
            price={"min": price_min, "max": price_max},
            object_type=object_type,
            availability=availability,
            floor_area={"min": floor_area_min, "max": floor_area_max},
            plot_area={"min": plot_area_min, "max": plot_area_max},
            rooms={"min": rooms_min, "max": rooms_max},
            bedrooms={"min": bedrooms_min, "max": bedrooms_max},
            bathrooms={"min": bathrooms_min, "max": bathrooms_max},
            construction_type=construction_type,
            construction_period=construction_period,
            parking_facility=parking_facility,
            garage_type=garage_type
        )
        
        # Start building the URL - filters should now be ordered by priority
        if 'transaction_type' not in filters:
            raise ValueError("Transaction type is required")
            
        url = UrlBuilder.BASE_URL + filters.pop('transaction_type')  # Add transaction type and remove from dict
        
        # Add all remaining filters to the URL
        for filter_name, filter_value in filters.items():
            url += f'&{filter_name}={quote_plus(filter_value)}'
            
        return url
    
    @staticmethod
    def get_number_results(search_url, timeout=10) -> Optional[int]:
        """
        Extract the number of search results from a Funda search page.
        
        Args:
            search_url: The URL to fetch results from
            timeout: Request timeout in seconds
            
        Returns:
            Number of search results or None if not found
        """
        try:
            response = requests.get(
                search_url,
                impersonate="chrome",
                timeout=timeout
            )
            response.raise_for_status()
            
            tree = html.fromstring(response.text)
            element = tree.xpath('//*[@id="PageListings"]/div[5]/div[2]/div[1]/div/h1/div[1]')
            
            if element:
                return int("".join(re.findall(r'\d+', element[0].text_content().strip())))
            else:
                return None
                
        except requests.RequestException as e:
            print(f"Error fetching search results: {e}")
            return None
        except Exception as e:
            print(f"Error parsing search results: {e}")
            return None

if __name__ == "__main__":

    url = UrlBuilder.build_url(
        transaction_type="buy",
        selected_area="amsterdam",
        price_min=0,
        price_max=650000,
        object_type=["house", "apartment"],
        availability=["available", "negotiations"],
        floor_area_min=None,
        floor_area_max=None,
        rooms_min=2,
        rooms_max=None,
        construction_type = None
    )
    print(url)
    print(f"Found {UrlBuilder.get_number_results(url)} ads for this search query")