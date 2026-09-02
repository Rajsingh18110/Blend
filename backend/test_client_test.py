from blend.webapp import app
import time

with app.test_client() as client:
    t0 = time.time()
    resp = client.get("/search?q=markanm&format=json")
    print("Time taken:", time.time() - t0)
    print("Results:", len(resp.get_json().get("results", [])))
