import requests
import os
from urllib.parse import unquote
import time
import csv

# ----------------------------
# Configuration
# ----------------------------
TOURIST_LOCATIONS = [
    # District 1 — Most popular
    "Ben Thanh Market",
    "Saigon Notre Dame Cathedral",
    "Saigon Central Post Office",
    "Nguyen Hue Walking Street",
    "Bitexco Financial Tower",
    "Saigon Skydeck",
    "Nguyen Hue Flower Street (seasonal)",
    "Ho Chi Minh City Opera House",
    "City Hall (People's Committee Building)",
    "Turtle Lake",
    "War Remnants Museum",
    "Reunification Palace",
    "Book Street Nguyen Van Binh",
    "Diamond Plaza",
    "Bui Vien Walking Street",
    "Ho Chi Minh City Museum",
    "Fine Arts Museum",
    "Saigon Zoo and Botanical Gardens",
    "Jade Emperor Pagoda",
    "Tan Dinh Church (Pink Church)",
    
    # District 3
    "Vinh Nghiem Pagoda",
    "Southern Women’s Museum",
    "War Memorial Park Le Van Tam",
    
    # District 5 (Chinatown)
    "Binh Tay Market",
    "Tran Hung Dao Statue",
    "Thien Hau Temple",
    "Chinese Assembly Halls",
    "Nghia An Hoi Quan Pagoda",
    "Vietnam Quoc Tu Pagoda",
    
    # District 7
    "Crescent Mall",
    "Crescent Lake & Starlight Bridge",
    
    # Thu Duc City / District 9
    "Suoi Tien Theme Park",
    "Vietnam National Museum of History (Thu Duc branch)",
    "Ao Dai Museum",
    
    # District 2 / Thu Thiem
    "Thu Thiem Bridge Viewpoint",
    "Saigon River Tunnel Park",
    
    # District 4
    "Khanh Hoi Riverside Park",
    
    # District 10 / District 11
    "Dam Sen Cultural Park",
    "Dam Sen Water Park",
    
    # District 12
    "Quang Trung Software City Park",
    
    # Religious / Cultural Sites
    "Giac Lam Pagoda",
    "Giac Vien Pagoda",
    "Xa Loi Pagoda",
    "Mariamman Hindu Temple",
    
    # Extra Modern Attractions
    "Landmark 81",
    "Landmark 81 SkyView Deck",
    "Vinhomes Central Park",
    
    # Museums
    "Ho Chi Minh City Museum of History",
    "Museum of Traditional Vietnamese Medicine",
    "Southern Women Museum",
    "Ao Dai Museum",
    
    # Local lifestyle attractions
    "Ben Nghe Wharf",
    "Saigon River Cruise Port",
    "Saigon Chinatown (Cho Lon)",
]


BASE_DOWNLOAD_DIR = "images/landmarks"  # root folder for all images
THUMB_SIZE = 800             
DELAY_BETWEEN_REQUESTS = 1   

# Create root folder if it doesn't exist
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

# ----------------------------
# Session with proper User-Agent
# ----------------------------
session = requests.Session()
session.headers.update({
    "User-Agent": "HCMTripPlannerBot/1.0 (your_email@example.com)"
})


# ----------------------------
# Function: Get main image of a location
# ----------------------------
def get_location_image_from_commons(location_name):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": location_name,
        "srnamespace": 6,
        "srlimit": 1
    }
    try:
        response = session.get("https://commons.wikimedia.org/w/api.php", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
        
        file_title = search_results[0]['title']
        
        params2 = {
            "action": "query",
            "format": "json",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url"
        }
        response2 = session.get("https://commons.wikimedia.org/w/api.php", params=params2, timeout=10)
        response2.raise_for_status()
        data2 = response2.json()
        page = next(iter(data2['query']['pages'].values()))
        if 'imageinfo' in page:
            return page['imageinfo'][0]['url']
    except requests.exceptions.RequestException as e:
        print(f"Request error for {location_name}: {e}")
    except ValueError:
        print(f"Failed to parse JSON for {location_name}")
    
    return None


# ----------------------------
# Function: Download image
# ----------------------------
def download_image(url, save_path):
    if not url:
        return False
    try:
        r = session.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {save_path}")
        return True
    except requests.exceptions.RequestException:
        print(f"Failed to download: {save_path}")
        return False


# ----------------------------
# Main
# ----------------------------
def main():
    csv_rows = []  # store (name, local_path)

    for location in TOURIST_LOCATIONS:
        loc_folder = os.path.join(BASE_DOWNLOAD_DIR, location)
        os.makedirs(loc_folder, exist_ok=True)

        existing_files = os.listdir(loc_folder)
        if existing_files:
            # use first existing file
            image_path = os.path.join(loc_folder, existing_files[0])
            csv_rows.append([location, image_path])
            print(f"Image already exists for {location}, skipping...")
            continue

        image_url = get_location_image_from_commons(location)
        if not image_url:
            print(f"No image found for {location}")
            csv_rows.append([location, ""])
            continue

        filename = "image.jpg"
        save_path = os.path.join(loc_folder, filename)

        success = download_image(image_url, save_path)
        if success:
            csv_rows.append([location, save_path])
        else:
            csv_rows.append([location, ""])

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # ----------------------------
    # Write CSV file
    # ----------------------------
    csv_path = "landmarks_simple.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "image_local_path"])
        writer.writerows(csv_rows)

    print(f"\nCSV saved → {csv_path}")


if __name__ == "__main__":
    main()
