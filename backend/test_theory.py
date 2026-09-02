import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:8081/api/search?q=github&format=json&pageno=1")
    resp = urllib.request.urlopen(req)
    print("Status:", resp.status)
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
