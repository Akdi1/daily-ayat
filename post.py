import os, json, datetime
import urllib.request, urllib.parse

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
START = datetime.date(2026, 11, 17)
TOTAL = 6236

days = (datetime.date.today() - START).days
first = (days * 3) % TOTAL

def get(n):
    url = f"https://api.alquran.cloud/v1/ayah/{n}/quran-uthmani"
    d = json.load(urllib.request.urlopen(url, timeout=30))["data"]
    return f'{d["text"]} ﴿{d["surah"]["name"]}: {d["numberInSurah"]}﴾'

lines = [get((first + i) % TOTAL + 1) for i in range(3)]
text = "\n\n".join(lines)

data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
urllib.request.urlopen(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data=data, timeout=30)
