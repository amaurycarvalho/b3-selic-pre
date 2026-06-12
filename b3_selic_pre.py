import urllib.request
import urllib.parse
import json
import base64

payload = {
    "language": "pt-br",
    "id": "SLP",
    "pageNumber": 1,
    "pageSize": 20,
    "date": "2026-06-10"
}

encoded = base64.b64encode(
    json.dumps(payload, separators=(',', ':')).encode('utf-8')
).decode('utf-8')

url = (
    "https://sistemaswebb3-derivativos.b3.com.br/"
    f"referenceRatesProxy/Search/GetList/{encoded}"
)

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

for item in data["results"]:
    print(
        f"{item['day252']:>4} "
        f"{item['day360']:>4} "
        f"{item['rate']}"
    )
