import yaml
from pathlib import Path

def load_field_mapping(content_type: str = "movies") -> dict:
    """
    Load field mapping for a given content type from the YAML config.

    Parameters:
    - content_type (str): e.g. "movies", "games"

    Returns:
    - dict: The field-to-label mapping dictionary for that type
    """
    # Path to the YAML file (relative to this file's location)
    path = Path(__file__).parent.parent / "resources" / "field_mapping.yaml"

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    all_mappings = config.get("content_types", {})
    if content_type not in all_mappings:
        raise ValueError(f"Unknown content_type '{content_type}'. Available types: {list(all_mappings.keys())}")

    return all_mappings[content_type]
