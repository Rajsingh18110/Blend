import time
import requests
import sys

PORT = 8081
BASE_URL = f"http://127.0.0.1:{PORT}/api/search"

def run_test(category, query="artificial intelligence"):
    url = f"{BASE_URL}?q={query}&categories={category}&format=json"
    print(f"\n--- Testing Category: {category.upper()} ---")
    start_time = time.perf_counter()
    try:
        response = requests.get(url, timeout=12)
        latency = time.perf_counter() - start_time
        
        if response.status_code != 200:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
        data = response.json()
        results = data.get("results", [])
        
        print(f"Latency: {latency:.2f}s")
        print(f"Results: {len(results)}")
        
        if len(results) == 0:
            print("❌ Failed: 0 results returned")
            return False
            
        # Specific checks based on category
        first = results[0]
        print(f"Top Result: {first.get('title')} - {first.get('url')[:60]}...")
        if category == "images":
            print(f"Has Thumbnail: {'Yes' if 'thumbnail_src' in first else 'No'}")
            
        if latency > 7.0 and category != "news":
            print("⚠️ Warning: Latency exceeded 7 seconds")
            
        return True
    except Exception as e:
        latency = time.perf_counter() - start_time
        print(f"❌ Failed after {latency:.2f}s: {e}")
        return False

def main():
    print("Starting E2E API Tests for Blend Search Architecture...")
    categories = ["web", "images", "news", "videos", "music"]
    
    passed = 0
    for cat in categories:
        success = run_test(cat)
        if success:
            passed += 1
            
    print(f"\n✅ Tests Complete. Passed: {passed}/{len(categories)}")
    if passed < len(categories):
        sys.exit(1)

if __name__ == "__main__":
    main()
