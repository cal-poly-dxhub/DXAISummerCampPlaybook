import json
import os
from typing import Dict, List
from datetime import datetime
from data_loader import load_all_data

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "candidate_data.json")

def ensure_cache_dir():
    """Ensure cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def save_to_cache(data: List[Dict]):
    """Save aggregated data to cache file."""
    ensure_cache_dir()
    with open(CACHE_FILE, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, f, indent=2)

def load_from_cache() -> List[Dict]:
    """Load data from cache if it exists and is recent."""
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        # Check if cache is less than 1 hour old
        cache_time = datetime.fromisoformat(cache['timestamp'])
        if (datetime.now() - cache_time).total_seconds() < 3600:
            return cache['data']
    except Exception as e:
        print(f"Error loading cache: {e}")
    
    return None

def get_candidate_data(force_refresh: bool = False) -> List[Dict]:
    """Get candidate data, either from cache or by loading fresh data."""
    if not force_refresh:
        cached_data = load_from_cache()
        if cached_data:
            return cached_data
    
    # Load fresh data
    data = load_all_data()
    save_to_cache(data)
    return data 