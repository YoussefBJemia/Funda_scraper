from enum import Enum
from typing import Union, List, Optional, Dict, Any, Callable
from dataclasses import dataclass

class FilterType(Enum):
    """Enum representing filter types."""
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"

@dataclass
class Filter:
    name: str
    display_name: str
    filter_type: FilterType
    priority: int
    format_func: Callable
    
    def format(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return self.format_func(value)


class FilterUtils:
    @staticmethod
    def format_categorical_filter(filter_values: Union[str, List[str]]) -> Optional[str]:
        """
        Convert a list or a single value to a string representation for categorical filters.

        Args:
            filter_values: Single string or list of strings representing filter options.

        Returns:
            String representation for URL parameter or None if empty.
        """
        if not isinstance(filter_values, list):
            filter_values = [filter_values]

        if not filter_values:
            return None

        return f'["' + '","'.join(str(element) for element in filter_values) + '"]'


    @staticmethod
    def format_numerical_filter(value: Dict[str, Optional[Union[int, float]]]) -> Optional[str]:
        """
        Create a string range for numerical filters.

        Args:
            value: Dictionary with 'min' and 'max' keys.

        Returns:
            String representation for URL parameter or None if both min and max are None.
        """
        min_value = value.get("min")
        max_value = value.get("max")

        # If both min and max are None, return None
        if min_value is None and max_value is None:
            return None

        # Handle cases where only one value is provided
        if min_value is None:
            min_value = 0  # Default to 0 if min is not provided
        if max_value is None:
            max_value = ""  # Default to empty string if max is not provided

        # Validate min and max values
        if max_value != "" and min_value > max_value:
            raise ValueError(f"Min value {min_value} should be smaller than max value {max_value}.")

        return f'"{min_value}-{max_value}"'

    @staticmethod
    def format_transaction_type(transaction_type: str) -> Optional[str]:
        """
        Set transaction category (buy or rent)
        
        Args:
            transaction_type: 'buy' or 'rent' string
            
        Returns:
            URL parameter for the transaction type or None if invalid
        """
        if transaction_type == "buy":
            return "koop?"
        elif transaction_type == "rent":
            return "huur?"
        else:
            return None


# Define all available filters with priorities
FILTERS = {
    # Transaction type filter
    "transaction_type": Filter(
        name="transaction_type",
        display_name="Transaction Type",
        filter_type=FilterType.CATEGORICAL,
        priority=1,
        format_func=FilterUtils.format_transaction_type
    ),
    
    # Location filter
    "selected_area": Filter(
        name="selected_area",
        display_name="Location",
        filter_type=FilterType.CATEGORICAL,
        priority=2,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Price filter
    "price": Filter(
        name="price",
        display_name="Price",
        filter_type=FilterType.NUMERICAL,
        priority=3,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Property type filter
    "object_type": Filter(
        name="object_type",
        display_name="Property Type",
        filter_type=FilterType.CATEGORICAL,
        priority=4,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Availability filter
    "availability": Filter(
        name="availability",
        display_name="Availability",
        filter_type=FilterType.CATEGORICAL,
        priority=5,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Floor area filter
    "floor_area": Filter(
        name="floor_area",
        display_name="Floor Area (m²)",
        filter_type=FilterType.NUMERICAL,
        priority=6,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Plot area filter
    "plot_area": Filter(
        name="plot_area",
        display_name="Plot Area (m²)",
        filter_type=FilterType.NUMERICAL,
        priority=7,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Rooms filter
    "rooms": Filter(
        name="rooms",
        display_name="Rooms",
        filter_type=FilterType.NUMERICAL,
        priority=8,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Bedrooms filter
    "bedrooms": Filter(
        name="bedrooms",
        display_name="Bedrooms",
        filter_type=FilterType.NUMERICAL,
        priority=9,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Bathrooms filter
    "bathrooms": Filter(
        name="bathrooms",
        display_name="Bathrooms",
        filter_type=FilterType.NUMERICAL,
        priority=10,
        format_func=FilterUtils.format_numerical_filter
    ),
    
    # Construction type filter
    "construction_type": Filter(
        name="construction_type",
        display_name="Construction Type",
        filter_type=FilterType.CATEGORICAL,
        priority=11,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Construction period filter
    "construction_period": Filter(
        name="construction_period",
        display_name="Construction Period",
        filter_type=FilterType.CATEGORICAL,
        priority=12,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Parking facility filter
    "parking_facility": Filter(
        name="parking_facility",
        display_name="Parking Facility",
        filter_type=FilterType.CATEGORICAL,
        priority=13,
        format_func=FilterUtils.format_categorical_filter
    ),
    
    # Garage type filter
    "garage_type": Filter(
        name="garage_type",
        display_name="Garage Type",
        filter_type=FilterType.CATEGORICAL,
        priority=14,
        format_func=FilterUtils.format_categorical_filter
    ),
}

def generate_filters(**kwargs) -> Dict[str, Any]:
    """
    Generate a dictionary of filters based on input parameters, sorted by filter priority.
    """
    unsorted_filters = {}
    
    # First, format all the filter values
    for filter_name, filter_value in kwargs.items():
        if filter_name in FILTERS:
            filter_obj = FILTERS[filter_name]
            formatted_value = filter_obj.format(filter_value)
            if formatted_value is not None:  # Only include non-None values
                unsorted_filters[filter_name] = {
                    'value': formatted_value,
                    'priority': filter_obj.priority
                }
    
    # Then, create a new ordered dictionary based on priority
    ordered_filters = {}
    for name, data in sorted(unsorted_filters.items(), key=lambda x: unsorted_filters[x[0]]['priority']):
        ordered_filters[name] = data['value']
    
    return ordered_filters


def get_filters_display() -> Dict[str, str]:
    """
    Get a dictionary of filter names and their corresponding display names.
    """
    filters_display = {}
    # Get the filters sorted by priority
    sorted_filters = sorted(FILTERS.values(), key=lambda f: f.priority)
    
    for filter_obj in sorted_filters:
        filters_display[filter_obj.name] = filter_obj.display_name
    
    return filters_display

if __name__ == "__main__":
    filters = generate_filters(
        transaction_type="buy",
        selected_area="amsterdam",
        price={"min": None, "max": 650000},
        object_type=["house", "apartment"],
        availability=["available", "negotiations"],
        floor_area={"min": 50, "max": None},
        rooms={"min": 2, "max": None},
        construction_type=["newly_built"],
    )
    print(filters)
    print(get_filters_display())