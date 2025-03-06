from typing import Dict, Tuple, Optional, Literal, List, Any, Set
import dateparser
import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_component_group(
    component: str,
) -> Literal["year", "month", "day", "hour", "minute", "second", "ampm", "unknown"]:
    """
    Returns the group a component belongs to.

    Args:
        component (str): The date/time component to categorize.

    Returns:
        Literal["year", "month", "day", "hour", "minute", "second", "ampm", "unknown"]: The group the component belongs to.
    """
    if component in ["YYYY", "YY"]:
        return "year"
    elif component in ["MMMM", "MMM", "MM", "M"]:
        return "month"
    elif component in ["DDDD", "DDD", "DD", "D", "Do"]:
        return "day"
    elif component in ["HH", "H", "hh"]:
        return "hour"
    elif component == "mm":
        return "minute"
    elif component == "ss":
        return "second"
    elif component in ["a", "A"]:
        return "ampm"
    else:
        return "unknown"


def detect_date_format(date_string: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        date_string = str(date_string)

        # Parse the input date string
        parsed_date = dateparser.parse(date_string)
        if not parsed_date:
            return None, None

        # Define the order of components to check
        components = [
            "YYYY",
            "MMMM",
            "MMM",
            "MM",
            "M",
            "DDDD",
            "DDD",
            "DD",
            "D",
            "Do",
            "HH",
            "H",
            "hh",
            "mm",
            "ss",
            "a",
            "A",
            "YY",
        ]
        # Create a dictionary with all possible date components and their regex patterns
        date_components: Dict[str, Tuple[str, Optional[str]]] = {
            "YYYY": (r"\d{4}", "%Y"),
            "YY": (r"\d{2}", "%y"),
            "DDDD": (parsed_date.strftime("%A"), "%A"),
            "DDD": (parsed_date.strftime("%a"), "%a"),
            "DD": (r"(0[1-9]|[12]\d|3[01])", "%d"),
            "D": (r"(0?[1-9]|[12]\d|3[01])", "%-d"),
            "Do": (r"(0?[1-9]|[12]\d|3[01])(st|nd|rd|th)", None),
            "MMMM": (parsed_date.strftime("%B"), "%B"),
            "MMM": (parsed_date.strftime("%b"), "%b"),
            "MM": (r"(0[1-9]|1[0-2])", "%m"),
            "M": (r"\b[1-9]\b", "%-m"),
            "HH": (r"([01]\d|2[0-3])", "%H"),
            "H": (r"\b[1-9]\b", "%-H"),
            "hh": (r"(0[1-9]|1[0-2])", "%I"),
            "mm": (r"[0-5]\d", "%M"),
            "ss": (r"[0-5]\d", "%S"),
            "a": (r"(am|pm)", "%p"),
            "A": (r"(AM|PM)", "%p"),
        }

        format_string = date_string
        matched_groups = set()

        for component in components:
            group = get_component_group(component)

            # Skip if we've already matched a component from this group
            if group in matched_groups:
                continue

            regex, strftime_format = date_components[component]
            if strftime_format:
                value = parsed_date.strftime(strftime_format)
                if value in format_string:
                    regex_match = re.search(regex, format_string)
                    if regex_match:
                        format_string = re.sub(regex, component, format_string, count=1)
                        matched_groups.add(group)

        # Handle special case for 'Do' (ordinal day)
        if "day" not in matched_groups:
            do_regex = date_components["Do"][0]
            do_match = re.search(do_regex, format_string)
            if do_match:
                format_string = format_string.replace(do_match.group(), "Do")
                matched_groups.add("day")

        # Check for ambiguity between month and day
        skip_ambiguous = False
        for comp in ["DDDD", "DDD", "Do", "MMMM", "MMM"]:
            if comp in format_string:
                skip_ambiguous = True
                break

        if not skip_ambiguous:
            day_month_components = [
                comp for comp in ["DD", "D", "MM", "M"] if comp in format_string
            ]
            if len(day_month_components) >= 2:
                day = parsed_date.day
                month = parsed_date.month
                if day <= 12 and month <= 12:
                    return None, format_string

        # Check if the format includes day, month, and year components
        has_day = "day" in matched_groups
        has_month = "month" in matched_groups
        has_year = "year" in matched_groups

        if has_day and has_month and has_year:
            return format_string, format_string
        else:
            return None, format_string
    except Exception as e:
        logger.error(f"Error in detect_date_format: {str(e)}")
        return None, None


def excel_cell_to_index(cell):
    match = re.match(r"([A-Z]+)(\d+)", cell, re.I)
    if not match:
        raise ValueError(f"Invalid cell reference: {cell}")
    column_letters, row = match.groups()

    col = sum(
        (ord(letter.upper()) - 64) * (26**i)
        for i, letter in enumerate(reversed(column_letters))
    )
    return max(0, int(row) - 1), col - 1  # Convert to 0-based index


def extract_from_region(
    df: pd.DataFrame, mapped_columns: List[Dict[str, Any]], attribute_name: str
) -> bool:
    """
    Extract values from DataFrame based on mapped region using original values.
    Args:
        df (pd.DataFrame): DataFrame containing the data
        mapped_columns (List[Dict[str, Any]]): List of dictionaries containing mapping information
        attribute_name (str): Name of the mapped attribute to extract
        num_rows (int, optional): Number of rows to extract. Defaults to 5.
    Returns:
        bool: Indicating if the extracted values are valid dates
    """
    try:
        # Find the mapping for the requested attribute
        mapping = next(
            (
                item
                for item in mapped_columns
                if item["mapped_attribute"] == attribute_name
            ),
            None,
        )

        if not mapping:
            logger.warning(f"No mapping found for attribute: {attribute_name}")
            return False

        # Parse region (e.g., 'B14:B35')
        region = mapping["region"]
        start_cell, end_cell = region.split(":")

        # Extract row and column indices
        start_row, start_col = excel_cell_to_index(start_cell)
        end_row, _ = excel_cell_to_index(end_cell)

        # Calculate the number of rows to process
        start_row += 1  # Skip the header row
        row_diff = end_row - start_row + 1  # +1 because end_row is inclusive
        num_rows_to_process = row_diff if row_diff <= 5 else 5

        # Get the values from the DataFrame
        end_row = start_row + num_rows_to_process
        values = df.iloc[start_row:end_row, start_col].values

        valid_date = True
        for value in values:
            _, date_format = detect_date_format(value)

            has_day = "D" in date_format if date_format else False
            has_month = "M" in date_format if date_format else False
            has_year = "Y" in date_format if date_format else False

            if not (has_day and has_month and has_year):
                valid_date = False
                break

        return valid_date

    except Exception as e:
        logger.error(
            f"Error in extract_from_region for attribute {attribute_name}: {str(e)}"
        )
        return False


def handle_date_attributes(
    island_df: pd.DataFrame,
    mapped_columns: List[Dict[str, Any]],
    unmapped_attributes: List[str],
    mapped_attributes: Set[str],
) -> Tuple[List[Dict[str, Any]], List[str], Set[str]]:
    """
    Handle date attributes in the mapping process.

    Args:
        island_df (pd.DataFrame): The DataFrame containing the data.
        mapped_columns (List[Dict[str, Any]]): List of dictionaries containing mapping information.
        unmapped_attributes (List[str]): List of unmapped attributes.
        mapped_attributes (Set[str]): Set of mapped attributes.

    Returns:
        Tuple[List[Dict[str, Any]], List[str], Set[str]]: Updated mapped_columns, unmapped_attributes, and mapped_attributes.
    """
    try:
        if not isinstance(mapped_columns, list) or not all(
            isinstance(item, dict) for item in mapped_columns
        ):
            raise TypeError("mapped_columns must be a list of dictionaries")
        if not isinstance(unmapped_attributes, list) or not all(
            isinstance(item, str) for item in unmapped_attributes
        ):
            raise TypeError("unmapped_attributes must be a list of strings")
        if not isinstance(mapped_attributes, set) or not all(
            isinstance(item, str) for item in mapped_attributes
        ):
            raise TypeError("mapped_attributes must be a set of strings")

        date_attributes = [
            "initiated_date",
            "updated_date",
            "closing_balance_updated_date",
        ]

        for attribute in date_attributes:
            if attribute not in unmapped_attributes:
                valid_date = extract_from_region(island_df, mapped_columns, attribute)

                if not valid_date:
                    mapped_columns = [
                        column
                        for column in mapped_columns
                        if column["mapped_attribute"] != attribute
                    ]
                    unmapped_attributes.append(attribute)
                    mapped_attributes.discard(attribute)

        existing_date_attributes = [
            attr for attr in date_attributes if attr in mapped_attributes
        ]

        if len(existing_date_attributes) == 1:
            existing_date = next(
                (
                    column
                    for column in mapped_columns
                    if column["mapped_attribute"] in date_attributes
                ),
                None,
            )
            if existing_date:
                for attr in date_attributes:
                    if attr not in mapped_attributes:
                        new_column = existing_date.copy()
                        new_column["mapped_attribute"] = attr
                        mapped_columns.append(new_column)
                        mapped_attributes.add(attr)
                        unmapped_attributes.remove(attr)

        if (
            "updated_date" in existing_date_attributes
            and "closing_balance_updated_date" not in mapped_attributes
        ):
            updated_date = next(
                (
                    column
                    for column in mapped_columns
                    if column["mapped_attribute"] == "updated_date"
                ),
                None,
            )

            if updated_date:
                new_column = updated_date.copy()
                new_column["mapped_attribute"] = "closing_balance_updated_date"
                mapped_columns.append(new_column)
                mapped_attributes.add("closing_balance_updated_date")
                unmapped_attributes.remove("closing_balance_updated_date")

        return mapped_columns, unmapped_attributes, mapped_attributes

    except Exception as e:
        logger.error(f"Error in handle_date_attributes: {str(e)}")
        # Return the original inputs in case of an error
        return mapped_columns, unmapped_attributes, mapped_attributes
