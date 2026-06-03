import os
import subprocess
import time
import requests

files_to_backup = [
    "backend/app.py",
    "backend/blend_engine/search_router.py",
    "backend/blend_engine/ranking_engine.py",
    "backend/blend_engine/result_processor.py",
    "backend/blend_engine/provider_manager.py",
    "backend/providers/google_provider.py",
    "backend/providers/bing_provider.py"
]

print("Backing up files...")
for f in files_to_backup:
    subprocess.run(["cp", f, f + ".bak"], check=True)

print("Instrumenting files...")
subprocess.run(["python3", "instrument2.py"], check=True)

print("Starting Flask app...")
env = os.environ.copy()
env["PYTHONPATH"] = "backend"
process = subprocess.Popen(["./venv/bin/python", "backend/app.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

print("Waiting for app to start...")
time.sleep(3)

print("Curling /api/search?q=python...")
try:
    resp = requests.get("http://127.0.0.1:8081/api/search?q=python", timeout=10)
    print("Curl status code:", resp.status_code)
except Exception as e:
    print("Curl failed:", e)

print("Stopping app...")
process.terminate()
try:
    process.wait(timeout=2)
except subprocess.TimeoutExpired:
    process.kill()

print("\n--- APP LOGS ---")
stdout, _ = process.communicate()
print(stdout)
print("--- END LOGS ---\n")

print("Restoring files...")
for f in files_to_backup:
    subprocess.run(["mv", f + ".bak", f], check=True)
print("Done.")
