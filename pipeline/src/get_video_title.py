import requests
import sys
from urllib.parse import quote
from config import SUPADATA_API_KEY

def get_video_title(youtube_url) -> str:
    """
    Get video title from Supadata API
    
    Args:
        youtube_url: YouTube video URL
        
    Returns:
        str: Video title or None if failed
    """
    # Encode the YouTube URL
    encoded_url = quote(youtube_url, safe='')
    
    # Construct the API endpoint
    api_url = f"https://api.supadata.ai/v1/metadata?url={encoded_url}"
    
    # Set headers
    headers = {
        "x-api-key": SUPADATA_API_KEY
    }
    
    try:
        # Make the request
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Extract title from the response
        title = data.get('title')
        
        if title:
            return title
        else:
            print("Title not found in response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching video title: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_video_title.py <youtube_url>", file=sys.stderr)
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    title = get_video_title(youtube_url)

    if title:
        print(title)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
