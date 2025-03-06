import re
import yaml


def extract_yaml_from_response(response: str):
    """
    Extracts a YAML object from a string that might contain YAML formatted data embedded within.

    Args:
    response (str): The text response from a large language model that includes YAML data.

    Returns:
    dict or None: The parsed YAML object as a Python dictionary, or None if no valid YAML data is found.
    """
    # Regex to find YAML content enclosed in markers or as a block
    yaml_pattern = r"---(.*?)\.\.\."
    yaml_matches = re.findall(yaml_pattern, response, re.DOTALL)

    for yaml_content in yaml_matches:
        # Load YAML data into a Python dictionary
        try:
            yaml_data = yaml.safe_load(yaml_content)
            return yaml_data
        except yaml.YAMLError as exc:
            return exc
        except Exception as e:
            return e

    return None
