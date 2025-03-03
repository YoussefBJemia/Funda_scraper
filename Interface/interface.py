import tkinter as tk
import sys
from tkinter import ttk, messagebox
import pandas as pd
import json
import os
import pprint
import gc
from curl_cffi import requests
from lxml import html
import re
import unicodedata
import json

from Scraper.config import Config
from Scraper.utils import CleanerUtils, CommonFunctions
from Scraper.url_builder import UrlBuilder

clean_name = CleanerUtils.clean_name
# Initialize Config instance
config = Config()  # Using default base_dir, or pass one as an argument if needed

# Use Config's data directory paths
OUTPUT_DIR = config.data_dir  # From Config
SEARCH_QUERY_FILE = config.search_query_file  # From Config
AVAILABLE_LOCATIONS_FILE = config.available_location_queries_file

user_choice_continue = {"value": False}

# Initialize Config instance
config = Config()  # Using default base_dir, or pass one as an argument if needed

# Use Config's data directory paths
OUTPUT_DIR = config.data_dir  # From Config
SEARCH_QUERY_FILE = config.search_query_file  # From Config
AVAILABLE_LOCATIONS_FILE = config.available_location_queries_file

user_choice_continue = {"value": False}

def save_filters_to_json(filters, filename=None):
    """Save the filter dictionary to a JSON file."""
    # Use the default file path from Config if no filename is provided
    if filename is None:
        filename = SEARCH_QUERY_FILE
    
    try:
        with open(filename, 'w') as json_file:
            json.dump(filters, json_file, indent=4)
        print(f"Filters saved to {filename}")
    except Exception as e:
        print(f"Failed to save filters to JSON: {e}")

def load_filters_from_json(filename=None):
    """Load filters from a JSON file."""
    # Use the default file path from Config if no filename is provided
    if filename is None:
        filename = SEARCH_QUERY_FILE
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as json_file:
                return json.load(json_file)
        except Exception as e:
            print(f"Failed to load filters from JSON: {e}")
    return None



# Global state variables
filter_values = {}
custom_filters = {}
location_data = {
    'cities': [],
    'gemeentes': [],
    'provinces': []
}
ui_elements = {}

def load_location_data():
    """Load and process location data from CSV"""
    try:
        df = pd.read_csv(AVAILABLE_LOCATIONS_FILE)
        filtered_df = df[df['query'] != '[]']
        
        location_data['cities'] = sorted(filtered_df['plaats'].tolist())
        location_data['gemeentes'] = sorted(filtered_df['gemeente'].unique().tolist())
        location_data['provinces'] = sorted(filtered_df['provincie'].unique().tolist())
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load location data: {str(e)}")
        # Use empty lists as fallback

def create_buy_rent_filters(parent):
    """Create the Buy or Rent filter section"""
    buy_rent_frame = ttk.LabelFrame(parent, text="Buy or Rent")
    buy_rent_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(buy_rent_frame, text="Search for:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    
    buy_rent_var = tk.StringVar(value="Buy")  # Default to "Buy"
    ui_elements['buy_rent_var'] = buy_rent_var
    buy_rent_options = ["Buy", "Rent"]
    
    for i, option in enumerate(buy_rent_options):
        ttk.Radiobutton(buy_rent_frame, text=option, variable=buy_rent_var, value=option).grid(
            row=0, column=i+1, padx=5, pady=5, sticky=tk.W)

def update_location_list():
    """Update the location listbox based on the selected location type"""
    ui_elements['location_listbox'].delete(0, tk.END)
    
    location_type = ui_elements['location_type_var'].get()
    
    if location_type == "City":
        locations = location_data['cities']
    elif location_type == "Gemeente":
        locations = location_data['gemeentes']
    elif location_type == "Provincie":
        locations = location_data['provinces']
    
    for location in locations:
        ui_elements['location_listbox'].insert(tk.END, location)

def select_all_locations():
    """Select all items in the location listbox and set a special value to indicate all locations are selected"""
    ui_elements['location_listbox'].select_set(0, tk.END)
    # Set the special value to indicate all locations are selected
    ui_elements['selected_area'] = "ALL"



def clear_all_locations():
    """Clear all selections in the location listbox"""
    ui_elements['location_listbox'].selection_clear(0, tk.END)

def on_location_select(event):
    """Handle the selection event in the location listbox"""
    listbox = ui_elements['location_listbox']
    selected_indices = listbox.curselection()

    # Check if the number of selected items is less than the total number of items
    if len(selected_indices) < listbox.size():
        # If not all items are selected, clear the special value
        if 'selected_area' in ui_elements:
            del ui_elements['selected_area']
    else:
        # If all items are selected, set the special value
        ui_elements['selected_area'] = "ALL"

def create_location_filters(parent):
    """Create the location filter section with hierarchical selection"""
    location_frame = ttk.LabelFrame(parent, text="Location")
    location_frame.pack(fill=tk.X, pady=5)

    # Location type selection
    ttk.Label(location_frame, text="Search by:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    location_type_var = tk.StringVar(value="City")
    ui_elements['location_type_var'] = location_type_var
    location_types = ["City", "Gemeente", "Provincie"]

    for i, loc_type in enumerate(location_types):
        ttk.Radiobutton(location_frame, text=loc_type, variable=location_type_var,
                       value=loc_type, command=update_location_list).grid(
                       row=0, column=i+1, padx=5, pady=5, sticky=tk.W)

    # Frame for the location selection list
    location_list_frame = ttk.Frame(location_frame)
    location_list_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W+tk.E)

    # Scrollable listbox with multi-selection
    ttk.Label(location_list_frame, text="Select locations:").pack(anchor=tk.W, pady=(5,0))

    list_frame = ttk.Frame(location_list_frame)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    location_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=6,
                                 yscrollcommand=scrollbar.set, exportselection=False)
    ui_elements['location_listbox'] = location_listbox
    location_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=location_listbox.yview)

    # Bind the selection event to the handler
    location_listbox.bind('<<ListboxSelect>>', on_location_select)

    # Button frame for All/None buttons
    button_frame = ttk.Frame(location_list_frame)
    button_frame.pack(fill=tk.X, pady=(0, 5))

    ttk.Button(button_frame, text="Select All", command=select_all_locations, width=12).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Clear All", command=clear_all_locations, width=12).pack(side=tk.LEFT, padx=5)

    # Initialize the location list
    update_location_list()


def on_price_option_change():
    """Handle the change in the price range option."""
    if ui_elements['price_range_var'].get() == "Custom":
        # Enable the min and max price fields
        ui_elements['min_price_entry'].config(state=tk.NORMAL)
        ui_elements['max_price_entry'].config(state=tk.NORMAL)
    else:
        # Disable the min and max price fields (grayed out)
        ui_elements['min_price_entry'].config(state=tk.DISABLED)
        ui_elements['max_price_entry'].config(state=tk.DISABLED)

def create_price_filters(parent):
    price_frame = ttk.LabelFrame(parent, text="Price")
    price_frame.pack(fill=tk.X, pady=5)

    # Label for price range selection
    price_option_label = ttk.Label(price_frame, text="Price Range:")
    price_option_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

    # Variable to store the selected price range option
    price_range_var = tk.StringVar(value="Any")
    ui_elements['price_range_var'] = price_range_var

    # "Any" and "Custom" options using Radio Buttons
    ttk.Radiobutton(price_frame, text="Any", variable=price_range_var, value="Any", 
                   command=on_price_option_change).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    ttk.Radiobutton(price_frame, text="Custom", variable=price_range_var, value="Custom", 
                   command=on_price_option_change).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

    # Min price
    ttk.Label(price_frame, text="Min Price (€):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    min_price_var = tk.StringVar()
    ui_elements['min_price_var'] = min_price_var
    min_price_entry = ttk.Entry(price_frame, textvariable=min_price_var, width=15)
    ui_elements['min_price_entry'] = min_price_entry
    min_price_entry.grid(row=1, column=1, padx=5, pady=5)
    
    # Max price
    ttk.Label(price_frame, text="Max Price (€):").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
    max_price_var = tk.StringVar()
    ui_elements['max_price_var'] = max_price_var
    max_price_entry = ttk.Entry(price_frame, textvariable=max_price_var, width=15)
    ui_elements['max_price_entry'] = max_price_entry
    max_price_entry.grid(row=1, column=3, padx=5, pady=5)

    # Set initial state (grayed out for "Any")
    on_price_option_change()


def create_availability_filters(parent):
    """Create the Availability filter section"""
    availability_frame = ttk.LabelFrame(parent, text="Availability")
    availability_frame.pack(fill=tk.X, pady=5)

    # Availability options
    availability_options = ["Available", "Negotiations", "Unavailable"]
    ui_elements['availability_var'] = []

    for i, option in enumerate(availability_options):
        var = tk.BooleanVar()
        ui_elements['availability_var'].append(var)
        ttk.Checkbutton(availability_frame, text=option, variable=var).grid(
            row=0, column=i, padx=5, pady=5, sticky=tk.W)


def create_property_filters(parent):
    property_frame = ttk.LabelFrame(parent, text="Property Details")
    property_frame.pack(fill=tk.X, pady=5)

    # Property types multi-select
    ttk.Label(property_frame, text="Property Types:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W+tk.N)

    # Frame for property type selection list
    type_list_frame = ttk.Frame(property_frame)
    type_list_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

    # Scrollable listbox with multi-selection for property types
    list_frame = ttk.Frame(type_list_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    property_type_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=4,
                                      yscrollcommand=scrollbar.set, exportselection = False)
    ui_elements['property_type_listbox'] = property_type_listbox
    property_type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=property_type_listbox.yview)

    # Add property types
    property_types = ["House", "Apartment", "Land", "Parking"]
    for property_type in property_types:
        property_type_listbox.insert(tk.END, property_type)

    

def remove_custom_filter(frame, filter_type):
    """Remove a custom filter"""
    frame.destroy()
    if filter_type in custom_filters:
        del custom_filters[filter_type]

def add_filter_value(filter_type, filter_values_dict):
    """Add the filter type and its value to the filters dictionary"""
    custom_filters[filter_type] = filter_values_dict

def create_custom_filter(parent, filter_type, custom_filters_frame):
    """Create a new custom filter widget based on the selected type."""
    # Check if this filter already exists
    if filter_type in custom_filters:
        messagebox.showinfo("Info", f"A {filter_type} filter already exists.")
        return
    
    # Create filter frame within the custom filters section
    filter_frame = ttk.Frame(custom_filters_frame)
    filter_frame.pack(fill=tk.X, pady=5)
    
    # Add filter label
    ttk.Label(filter_frame, text=f"{filter_type}:", width=15, anchor="w", 
             font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    
    # Create appropriate widget based on filter type
    filter_var = None
    
    # Range filters (min/max entries)
    range_filters = [
        "Floor Area",
        "Plot Area",
        "Number of Rooms",
        "Number of Bedrooms",
        "Number of Bathrooms"
    ]
    
    # List filters (multiple choice with scrollable list)
    list_filters = [
        "Availability",
        "Construction Type",
        "Parking Facility",
        "Garage Type",
        "Construction Period"
    ]
    
    if filter_type in range_filters:
        min_var = tk.StringVar()
        max_var = tk.StringVar()
        
        min_frame = ttk.Frame(filter_frame)
        min_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(min_frame, text="Min:", font=("Arial", 9)).pack(side=tk.LEFT)
        ttk.Entry(min_frame, textvariable=min_var, width=10).pack(side=tk.LEFT, padx=2)
        
        max_frame = ttk.Frame(filter_frame)
        max_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(max_frame, text="Max:", font=("Arial", 9)).pack(side=tk.LEFT)
        ttk.Entry(max_frame, textvariable=max_var, width=10).pack(side=tk.LEFT, padx=2)
        
        # Function to save values when OK is clicked
        def save_range_values():
            min_val = min_var.get() or None
            max_val = max_var.get() or None
            
            # Store the values directly in the custom_filters dictionary
            custom_filters[filter_type] = {"min": min_val, "max": max_val}
            messagebox.showinfo("Success", f"{filter_type} filter values saved")
        
        # Add OK button to confirm the values
        ttk.Button(filter_frame, text="OK", width=5, command=save_range_values).pack(side=tk.LEFT, padx=5)
        
    elif filter_type in list_filters:
        # Define options based on filter type
        if filter_type == "Availability":
            options = ["Available", "Negotiations", "Unavailable"]
        elif filter_type == "Construction Type":
            options = ["Resale", "Newly Built"]
        elif filter_type == "Construction Period":
            options =['Unknown', 'Before 1906', '1906-1930', '1931-1944', '1945-1959', '1960-1970', '1971-1980', '1981-1990', '1991-2000', '2001-2010', '2011-2020', 'After 2020']
        elif filter_type == "Parking Facility":
            options = ["Private Property", "Enclosed Property", "Public Parking", "Paid Parking", 
                      "Parking Garage", "Parking Permits"]
        elif filter_type == "Garage Type":
            options = ["Lean-to", "Lock-up", "Garage & Carport", "Built-in", "Underground", "Basement", 
                      "Detached", "Garage Possible", "Carport", "Parking Space", "All Garages"]
        
        # Create a scrollable listbox for multiple selections
        list_frame = ttk.Frame(filter_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.X, padx=5)
        
        # Create the listbox
        listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=4, width=30, exportselection = False)
        listbox.pack(side=tk.LEFT)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Populate the listbox
        for option in options:
            listbox.insert(tk.END, option)
        
        # Function to save the selected values when OK is clicked
        def save_selected_options():
            selected = [listbox.get(i) for i in listbox.curselection()]
            if selected:
                # Store the selected values directly in the custom_filters dictionary
                custom_filters[filter_type] = selected
                messagebox.showinfo("Success", f"{filter_type} filter values saved")
            else:
                messagebox.showwarning("Warning", "Please select at least one option.")
        
        # Add OK button to confirm the selection
        ttk.Button(filter_frame, text="OK", width=5, command=save_selected_options).pack(side=tk.LEFT, padx=5)
    
    # Add remove button
    ttk.Button(filter_frame, text="X", width=3, 
              command=lambda f=filter_frame, t=filter_type: remove_custom_filter(f, t)).pack(side=tk.RIGHT, padx=5)

def add_custom_filter(parent, custom_filters_frame):
    """Add a custom filter field with additional filters."""
    filter_categories = [
        #"Availability",
        "Floor Area",
        "Plot Area",
        "Number of Rooms",
        "Number of Bedrooms",
        "Number of Bathrooms",
        "Construction Type",
        "Construction Period",
        "Parking Facility",
        "Garage Type"
    ]
    
    # Create a custom dialog for filter selection
    dialog = tk.Toplevel(parent)
    dialog.title("Select Filter")
    dialog.geometry("300x400")
    dialog.transient(parent)
    dialog.grab_set()
    
    ttk.Label(dialog, text="Select a filter to add:", padding=10).pack()
    
    # Variable to store selected filter
    selected_filter_var = tk.StringVar()
    
    # Create a listbox with single selection (not multiple as in original)
    list_frame = ttk.Frame(dialog)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Changed to SINGLE selectmode (key change from original)
    filter_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
    filter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=filter_listbox.yview)
    
    for category in filter_categories:
        filter_listbox.insert(tk.END, category)
    
    def on_ok():
        selection = filter_listbox.curselection()
        if selection:
            selected_filter = filter_listbox.get(selection[0])
            selected_filter_var.set(selected_filter)
            dialog.destroy()
            create_custom_filter(parent, selected_filter_var.get(), custom_filters_frame)
        else:
            messagebox.showwarning("Warning", "Please select a filter.")
    
    def on_cancel():
        dialog.destroy()
    
    button_frame = ttk.Frame(dialog)
    button_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
    ttk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=10)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    
    # Center the dialog on the parent window
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

def create_custom_filters_section(parent):
    # Frame for custom filters
    custom_filters_frame = ttk.LabelFrame(parent, text="Additional Filters")
    custom_filters_frame.pack(fill=tk.X, pady=5)
    
    # Button to add custom filters
    ttk.Button(custom_filters_frame, text="Add Filter", 
              command=lambda: add_custom_filter(parent, custom_filters_frame)).pack(pady=10)
    
    return custom_filters_frame

def get_selected_locations():
    """Get the list of selected locations from the listbox"""
    listbox = ui_elements['location_listbox']
    selected_indices = listbox.curselection()
    return [listbox.get(i) for i in selected_indices]

def get_selected_property_types():
    """Get the list of selected property types from the listbox"""
    listbox = ui_elements['property_type_listbox']
    selected_indices = listbox.curselection()
    return [listbox.get(i) for i in selected_indices]

def build_filter_dictionary():
    """Build the final filter dictionary with all selected values"""
    # Get location values
    selected_locations = get_selected_locations()
    location_type = ui_elements['location_type_var'].get()

    # Check if all locations are selected
    if 'selected_area' in ui_elements and ui_elements['selected_area'] == "ALL":
        selected_area = None
    else:
        selected_area = {
            "type": location_type,
            "values": selected_locations if selected_locations else None
        }

    # Get price values
    price_option = ui_elements['price_range_var'].get()
    min_price = ui_elements['min_price_var'].get() if price_option == "Custom" else None
    max_price = ui_elements['max_price_var'].get() if price_option == "Custom" else None

    # Get property values
    property_types = get_selected_property_types()

    # Define availability options within the function
    availability_options = ["Available", "Negotiations", "Unavailable"]

    # Get availability values
    availability = [availability_options[i] for i, var in enumerate(ui_elements['availability_var']) if var.get()]

    # Build the main filter dictionary
    filters = {
        "search_type": ui_elements['buy_rent_var'].get(),
        "locations": selected_area,
        "price": {
            "min": min_price,
            "max": max_price
        },
        "property": {
            "types": property_types if property_types else None
        },
        "availability": availability if availability else None
    }

    # Add custom filters directly to the main filters dictionary
    for filter_name, filter_data in custom_filters.items():
        if isinstance(filter_data, dict) and "min" in filter_data and "max" in filter_data:
            # It's a range filter
            filters[filter_name] = {
                "min": filter_data["min"],
                "max": filter_data["max"]
            }
        else:
            # It's a list filter
            filters[filter_name] = filter_data

    return filters


def map_dictionary(filters):
    """
    Maps the filter dictionary from the GUI format to parameters for the build_url function.
    """
    # Initialize mapped parameters with default values
    mapped_params = {
        "transaction_type": "buy",
        "selected_area": None,
        "price_min": None,
        "price_max": None,
        "object_type": None,
        "availability": None,
        "floor_area_min": None,
        "floor_area_max": None,
        "plot_area_min": None,
        "plot_area_max": None,
        "rooms_min": None,
        "rooms_max": None,
        "bedrooms_min": None,
        "bedrooms_max": None,
        "bathrooms_min": None,
        "bathrooms_max": None,
        "construction_type": None,
        "construction_period": None,
        "parking_facility": None,
        "garage_type": None
    }

    # Map transaction type (buy/rent)
    if filters.get("search_type"):
        mapped_params["transaction_type"] = filters["search_type"].lower()

    # Map location values
    if filters.get("locations") and filters["locations"].get("values"):
        if isinstance(filters["locations"]["values"], list):
            # Always store as a list, regardless of how many items
            if filters["locations"]["type"] in ["Gemeente", "Provincie"]:
                mapped_params["selected_area"] = [clean_name(filters["locations"]["type"] + "-" + value) for value in filters["locations"]["values"]]
            else:
                mapped_params["selected_area"] = [clean_name(value) for value in filters["locations"]["values"]]

    # Map price range
    if filters.get("price"):
        if filters["price"].get("min"):
            try:
                mapped_params["price_min"] = int(filters["price"]["min"])
            except ValueError:
                pass  # Skip if not a valid number
        if filters["price"].get("max"):
            try:
                mapped_params["price_max"] = int(filters["price"]["max"])
            except ValueError:
                pass  # Skip if not a valid number

    # Map property types
    if filters.get("property") and filters["property"].get("types"):
        # Convert GUI property types to build_url expected values
        property_type_mapping = {
            "House": "house",
            "Apartment": "apartment",
            "Land": "land",
            "Parking": "parking"
        }

        mapped_types = []
        for gui_type in filters["property"]["types"]:
            if gui_type in property_type_mapping:
                mapped_types.append(property_type_mapping[gui_type])

        if mapped_types:
            mapped_params["object_type"] = mapped_types

    # Map numeric range filters
    range_filters = {
        "Floor Area": ("floor_area_min", "floor_area_max"),
        "Plot Area": ("plot_area_min", "plot_area_max"),
        "Number of Rooms": ("rooms_min", "rooms_max"),
        "Number of Bedrooms": ("bedrooms_min", "bedrooms_max"),
        "Number of Bathrooms": ("bathrooms_min", "bathrooms_max")
    }

    for filter_name, param_names in range_filters.items():
        filter_key = filter_name.lower().replace(" ", "_")
        if filters.get(filter_name):
            if filters[filter_name].get("min"):
                try:
                    mapped_params[param_names[0]] = int(filters[filter_name]["min"])
                except ValueError:
                    pass
            if filters[filter_name].get("max"):
                try:
                    mapped_params[param_names[1]] = int(filters[filter_name]["max"])
                except ValueError:
                    pass

    # Map list filters
    # Availability
    if filters.get("availability"):
        availability_mapping = {
            "Available": "available",
            "Negotiations": "negotiations",
            "Unavailable": "unavailable"
        }
        mapped_values = [availability_mapping.get(val) for val in filters["availability"] if val in availability_mapping]
        if mapped_values:
            mapped_params["availability"] = mapped_values

    # Construction Type
    if filters.get("Construction Type"):
        construction_type_mapping = {
            "Resale": "resale",
            "Newly Built": "newly_built"
        }
        mapped_values = [construction_type_mapping.get(val) for val in filters["Construction Type"] if val in construction_type_mapping]
        if mapped_values:
            mapped_params["construction_type"] = mapped_values

    # Construction Period
    if filters.get("Construction Period"):
        period_mapping = {
            "Unknown": "unknown",
            "Before 1906": "before_1906",
            "1906-1930": "from_1906_to_1930",
            "1931-1944": "from_1931_to_1944",
            "1945-1959": "from_1945_to_1959",
            "1960-1970": "from_1960_to_1970",
            "1971-1980": "from_1971_to_1980",
            "1981-1990": "from_1981_to_1990",
            "1991-2000": "from_1991_to_2000",
            "2001-2010": "from_2001_to_2010",
            "2011-2020": "from_2011_to_2020",
            "After 2020": "after_2020"
        }
        mapped_values = [period_mapping.get(val) for val in filters["Construction Period"] if val in period_mapping]
        if mapped_values:
            mapped_params["construction_period"] = mapped_values

    # Parking Facility
    if filters.get("Parking Facility"):
        parking_mapping = {
            "Private Property": "private_property",
            "Enclosed Property": "enclosed_property",
            "Public Parking": "public_parking",
            "Paid Parking": "paid_parking",
            "Parking Garage": "parking_garage",
            "Parking Permits": "parking_permits"
        }
        mapped_values = [parking_mapping.get(val) for val in filters["Parking Facility"] if val in parking_mapping]
        if mapped_values:
            mapped_params["parking_facility"] = mapped_values

    # Garage Type
    if filters.get("Garage Type"):
        garage_mapping = {
            "Lean-to": "lean_to",
            "Lock-up": "lock_up",
            "Garage & Carport": "garage_and_carport",
            "Built-in": "built_in",
            "Underground": "underground",
            "Basement": "basement",
            "Detached": "detached",
            "Garage Possible": "garage_possible",
            "Carport": "carport",
            "Parking Space": "parking_space",
            "All Garages": "all_garages"
        }
        mapped_values = [garage_mapping.get(val) for val in filters["Garage Type"] if val in garage_mapping]
        if mapped_values:
            mapped_params["garage_type"] = mapped_values

    return mapped_params



def start_scraping(root_window, user_choice_continue):
    user_choice_continue["value"] = True
    filters = build_filter_dictionary()
    map_filters = map_dictionary(filters)
    save_filters_to_json(map_filters)
    messagebox.showinfo("Filters Saved", "Filters have been saved to search_query.json")
    root_window.destroy()

def close_and_cleanup(window):
    window.destroy()
    global ui_elements, custom_filters, location_data
    ui_elements.clear()
    custom_filters.clear()
    for key in location_data.keys():
        location_data[key].clear()
    gc.collect()

def process_filters(root_window):
    filters = build_filter_dictionary()
    mapped_params = map_dictionary(filters)
    url = UrlBuilder.build_url(**mapped_params)
    observation_count = UrlBuilder.get_number_results(url, timeout=10)
    
    result_window = tk.Toplevel(root_window)
    result_window.title("Processing Results")
    result_window.geometry("600x400")
    
    ttk.Label(result_window, text=f"{observation_count} observations found", font=("Helvetica", 14)).pack(pady=(20, 10))
    
    url_frame = ttk.LabelFrame(result_window, text="Generated URL")
    url_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    url_text = tk.Text(url_frame, wrap=tk.WORD, height=5)
    url_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    url_text.insert(tk.END, url)
    url_text.config(state=tk.DISABLED)
    
    filter_frame = ttk.LabelFrame(result_window, text="Filter Settings")
    filter_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    filter_text = tk.Text(filter_frame, wrap=tk.WORD)
    filter_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    filter_text.insert(tk.END, pprint.pformat(filters, indent=4))
    filter_text.config(state=tk.DISABLED)
    
    ttk.Button(result_window, text="Close", command=result_window.destroy).pack(pady=10)

def create_buttons(parent, root_window):
    button_frame = ttk.Frame(parent)
    button_frame.pack(fill=tk.X, pady=20)
    
    ttk.Button(button_frame, text="Process", command=lambda: process_filters(root_window), width=15).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Start Scraping", command=lambda: start_scraping(root_window, user_choice_continue), width=15).pack(side=tk.RIGHT, padx=5)

def setup_gui(root, user_choice_continue):
    root.title("Housing Website Scraper")
    root.geometry("600x800")
    load_location_data()
    root.protocol("WM_DELETE_WINDOW", lambda: close_and_cleanup(root))
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    ttk.Label(scrollable_frame, text="Housing Search Filters", font=("Helvetica", 16)).pack(pady=(0, 20))
    
    create_buy_rent_filters(scrollable_frame)
    create_location_filters(scrollable_frame)
    create_price_filters(scrollable_frame)
    create_availability_filters(scrollable_frame)
    create_property_filters(scrollable_frame)
    create_custom_filters_section(scrollable_frame)
    
    create_buttons(scrollable_frame, root)
    return root

def start_new_search(startup_window, user_choice_continue):
    startup_window.destroy()
    root = tk.Tk()
    setup_gui(root, user_choice_continue).mainloop()

def show_startup_screen():
    def continue_scraping():
        user_choice_continue["value"] = True
        startup_window.destroy()
    
    startup_window = tk.Tk()
    startup_window.title("Housing Website Scraper")
    startup_window.geometry("500x400")
    x, y = (startup_window.winfo_screenwidth() - 500) // 2, (startup_window.winfo_screenheight() - 400) // 2
    startup_window.geometry(f"500x400+{x}+{y}")
    
    existing_query = load_filters_from_json()
    main_frame = ttk.Frame(startup_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Housing Website Scraper", font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
    
    if existing_query:
        ttk.Label(main_frame, text="Found existing search query:", font=("Helvetica", 12)).pack(anchor="w", pady=(10, 5))
        
        query_frame = ttk.LabelFrame(main_frame, text="Search Query Details")
        query_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        query_text = tk.Text(query_frame, wrap=tk.WORD, height=10)
        query_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        query_text.insert(tk.END, pprint.pformat(existing_query, indent=2))
        query_text.config(state=tk.DISABLED)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(buttons_frame, text="Continue Scraping", command=continue_scraping, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Start New Search", command=lambda: start_new_search(startup_window, user_choice_continue), width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=startup_window.destroy, width=15).pack(side=tk.RIGHT, padx=5)
    else:
        ttk.Label(main_frame, text="No existing search query found.", font=("Helvetica", 12)).pack(pady=20)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(buttons_frame, text="Start New Search", command=lambda: start_new_search(startup_window, user_choice_continue), width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=sys.exit, width=15).pack(side=tk.RIGHT, padx=5)
    
    startup_window.mainloop()
    return user_choice_continue["value"]


if __name__ == "__main__":
    show_startup_screen()