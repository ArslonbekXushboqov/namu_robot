import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

def create_json_file(data: Dict[str, Any], 
                    filename: str, 
                    directory: Optional[str] = None,
                    indent: int = 4,
                    ensure_ascii: bool = False,
                    overwrite: bool = True) -> bool:
    """
    Create a JSON file from dictionary data
    
    Parameters:
    - data: Dictionary to convert to JSON
    - filename: Name of the JSON file (with or without .json extension)
    - directory: Optional directory path (creates if doesn't exist)
    - indent: JSON indentation (default: 4, None for compact)
    - ensure_ascii: If True, non-ASCII characters are escaped (default: False)
    - overwrite: If False, won't overwrite existing files (default: True)
    
    Returns:
    - bool: True if successful, False if failed
    
    Usage Examples:
    create_json_file({"name": "John", "age": 30}, "user.json")
    create_json_file(data, "config.json", "data/configs", indent=2)
    """
    
    try:
        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Create full path
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
            filepath = Path(directory) / filename
        else:
            filepath = Path(filename)
        
        # Check if file exists and overwrite setting
        if filepath.exists() and not overwrite:
            print(f"File {filepath} already exists and overwrite is False")
            return False
        
        # Write JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, 
                     indent=indent, 
                     ensure_ascii=ensure_ascii,
                     separators=(',', ': ') if indent else (',', ':'))
        
        print(f"✅ JSON file created successfully: {filepath}")
        return True
        
    except TypeError as e:
        print(f"❌ Data serialization error: {e}")
        return False
    except PermissionError as e:
        print(f"❌ Permission error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_pretty_json(data: Dict[str, Any], filename: str) -> bool:
    """
    Quick function for pretty formatted JSON files
    """
    return create_json_file(data, filename, indent=4, ensure_ascii=False)

def create_compact_json(data: Dict[str, Any], filename: str) -> bool:
    """
    Quick function for compact JSON files (no indentation)
    """
    return create_json_file(data, filename, indent=None)

