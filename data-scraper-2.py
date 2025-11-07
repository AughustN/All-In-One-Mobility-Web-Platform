from playwright.sync_api import sync_playwright
import json

def scrape_busmap_hcm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
        context = browser.new_context()
        
        # Intercept API calls to capture real data
        api_responses = []
        
        def handle_response(response):
            if 'api' in response.url or 'route' in response.url:
                try:
                    data = response.json()
                    api_responses.append({
                        'url': response.url,
                        'data': data
                    })
                    print(f"📡 Captured API: {response.url}")
                except:
                    pass
        
        page = context.new_page()
        page.on('response', handle_response)
        
        print("🔄 Loading BusMap HCM...")
        page.goto("https://map.busmap.vn/hcm", timeout=60000)
        page.wait_for_load_state('networkidle')
        
        # Save captured API data
        with open("api_responses.json", "w", encoding="utf-8") as f:
            json.dump(api_responses, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved {len(api_responses)} API responses")
        browser.close()

if __name__ == "__main__":
    scrape_busmap_hcm()