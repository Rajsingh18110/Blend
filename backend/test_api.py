import urllib.request
import json

req = urllib.request.Request("http://127.0.0.1:8081/api/search?q=markanm+chat&format=json")
resp = urllib.request.urlopen(req)
print(resp.read().decode())
