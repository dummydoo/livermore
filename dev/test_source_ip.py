import requests
from requests_toolbelt.adapters.source import SourceAddressAdapter


r = requests.get("https://api.ipify.org?format=json")
print("expecting: 54.178.187.42, got: {}".format(r.json()["ip"]))

s = requests.Session()
s.mount("http://", SourceAddressAdapter("172.31.3.12"))
s.mount("https://", SourceAddressAdapter("172.31.3.12"))

r = s.get("https://api.ipify.org?format=json")
print("expecting: 13.113.144.139, got: {}".format(r.json()["ip"]))

s = requests.Session()
s.mount("http://", SourceAddressAdapter("172.31.9.144"))
s.mount("https://", SourceAddressAdapter("172.31.9.144"))

r = s.get("https://api.ipify.org?format=json")
print("expecting: 18.179.235.142, got: {}".format(r.json()["ip"]))
