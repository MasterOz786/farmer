import os
import requests
from bs4 import BeautifulSoup
import re

# data from ETH Zurich Research Collection
# https://www.research-collection.ethz.ch/entities/researchdata/160b68a0-cbfb-4b11-900c-3d144f41eb07
# DOI: 10.3929/ethz-b-000383116

# Dataset page URL
dataset_url = 'https://www.research-collection.ethz.ch/entities/researchdata/160b68a0-cbfb-4b11-900c-3d144f41eb07'
uuid = '160b68a0-cbfb-4b11-900c-3d144f41eb07'

def find_download_url():
    """Try multiple methods to find the CSV download URL"""
    
    # Method 1: Parse the dataset page HTML
    try:
        print("Attempting to find download link from dataset page...")
        response = requests.get(dataset_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for download links - ETH Research Collection may use various patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Check if it's a CSV download link
            if '.csv' in href.lower() or 'Raw_data' in text or 'raw_data' in text.lower():
                # Construct full URL
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return 'https://www.research-collection.ethz.ch' + href
                else:
                    return 'https://www.research-collection.ethz.ch/' + href
        
        # Also check for data attributes or download buttons
        for element in soup.find_all(['a', 'button'], attrs={'download': True}):
            href = element.get('href', '')
            if href and '.csv' in href.lower():
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return 'https://www.research-collection.ethz.ch' + href
        
        # Look for script tags that might contain download URLs
        for script in soup.find_all('script'):
            if script.string:
                # Look for CSV URLs in JavaScript
                csv_urls = re.findall(r'https?://[^\s"\'<>]+\.csv', script.string)
                if csv_urls:
                    return csv_urls[0]
                
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Try common DSpace/ETH Research Collection URL patterns
    print("Trying common download URL patterns...")
    possible_patterns = [
        # DSpace bitstream pattern
        f'https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/{uuid}/Raw_data.csv',
        f'https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/{uuid}/raw_data.csv',
        f'https://www.research-collection.ethz.ch/bitstream/handle/20.500.11850/{uuid}/data.csv',
        # Alternative patterns
        f'https://www.research-collection.ethz.ch/entities/file/{uuid}/Raw_data.csv',
        f'https://www.research-collection.ethz.ch/entities/file/{uuid}/raw_data.csv',
    ]
    
    for url in possible_patterns:
        try:
            test_response = requests.head(url, allow_redirects=True, timeout=10)
            if test_response.status_code == 200:
                print(f"Found working URL: {url}")
                return url
        except:
            continue
    
    return None

# Main download logic
try:
    download_link = find_download_url()
    
    if not download_link:
        raise Exception("Could not automatically find download link.")
    
    # Download the CSV file
    print(f"Downloading data from: {download_link}")
    csv_response = requests.get(download_link, allow_redirects=True, timeout=60)
    csv_response.raise_for_status()
    
    # Verify it's actually CSV content
    content_type = csv_response.headers.get('content-type', '').lower()
    if 'csv' not in content_type and not download_link.endswith('.csv'):
        # Check first few bytes
        if not csv_response.content[:100].decode('utf-8', errors='ignore').replace('\n', '').replace(',', '').replace(';', '').strip():
            raise Exception("Downloaded file does not appear to be CSV format.")
    
    # Save as data_raw.csv
    with open('data_raw.csv', 'wb') as f:
        f.write(csv_response.content)
    
    file_size = os.path.getsize('data_raw.csv')
    print(f"Download complete! Saved as data_raw.csv ({file_size:,} bytes)")
    
except requests.exceptions.RequestException as e:
    print(f"Error downloading data: {e}")
    print(f"\nPlease download the CSV file manually from:")
    print(f"{dataset_url}")
    print("Look for the 'Raw_data (CSV)' download link and save it as 'data_raw.csv' in the current directory.")
    raise
except Exception as e:
    print(f"Error: {e}")
    print(f"\nPlease download the CSV file manually from:")
    print(f"{dataset_url}")
    print("Look for the 'Raw_data (CSV)' download link and save it as 'data_raw.csv' in the current directory.")
    raise

