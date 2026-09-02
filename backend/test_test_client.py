from app import app
with app.test_client() as client:
    resp = client.get("/search?q=github&format=json")
    print("Status:", resp.status_code)
    print("Data length:", len(resp.data))
    if resp.is_json:
        data = resp.get_json()
        print("Results size:", data.get("number_of_results", 0))
