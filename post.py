import os, io, json, glob, uuid, datetime
import urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont, features

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
START = datetime.date(2026, 11, 16)
TOTAL = 6236
BASMALA = "بسم الله الرحمن الرحيم"
INVITE = "شارك الصورة لتكون صدقة جارية"
HANDLE = "@my_ayat_daily"
W = H = 1080
BOX = 640

days = (datetime.date.today() - START).days
first = (days * 3) % TOTAL

def get(n):
    url = f"https://api.alquran.cloud/v1/ayah/{n}/quran-uthmani"
    d = json.load(urllib.request.urlopen(url, timeout=30))["data"]
    return d["text"], f'{d["surah"]["name"]} : {d["numberInSurah"]}'

def find_font():
    for p in ("/usr/share/fonts/**/Amiri-Regular.ttf",
              "/usr/share/fonts/**/*Amiri*.ttf",
              "/usr/share/fonts/**/*Naskh*Arabic*.ttf"):
        r = glob.glob(p, recursive=True)
        if r:
            return r[0]
    return None

def make_image(text, ref, top):
    path = find_font()
    if not path or not features.check("raqm"):
        return None
    kw = {"direction": "rtl", "language": "ar"}
    def font(s):
        return ImageFont.truetype(path, s, layout_engine=ImageFont.Layout.RAQM)
    def wrap(f, s, maxw):
        lines, cur = [], ""
        for w in s.split():
            t = (cur + " " + w).strip()
            if f.getlength(t, **kw) <= maxw:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines
    size = 80
    while True:
        f = font(size)
        lines = wrap(f, text, W - 200)
        lh = int(size * 1.9)
        if len(lines) * lh <= BOX or size <= 30:
            break
        size -= 4
    if len(lines) * lh > BOX:
        return None
    img = Image.new("RGB", (W, H), (12, 59, 46))
    d = ImageDraw.Draw(img)
    d.rectangle([30, 30, W - 30, H - 30], outline=(212, 175, 55), width=4)
    if top:
        d.text((W // 2, 90), BASMALA, font=font(54),
               fill=(212, 175, 55), anchor="ma", **kw)
    y = 200 + (BOX - len(lines) * lh) // 2
    for line in lines:
        d.text((W // 2, y), line, font=f, fill=(255, 255, 255),
               anchor="ma", **kw)
        y += lh
    d.text((W // 2, 870), ref, font=font(44),
           fill=(212, 175, 55), anchor="ma", **kw)
    d.text((W // 2, 940), INVITE, font=font(38),
           fill=(255, 255, 255), anchor="ma", **kw)
    d.text((W // 2, 995), HANDLE, font=font(32),
           fill=(190, 200, 195), anchor="ma")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()

def send_photo(png):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="chat_id"'
            f'\r\n\r\n{CHAT}\r\n').encode()
    body += (f'--{b}\r\nContent-Disposition: form-data; name="photo"; '
             f'filename="a.png"\r\nContent-Type: image/png\r\n\r\n').encode()
    body += png + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    urllib.request.urlopen(req, timeout=60)

def send_text(t):
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": t}).encode()
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data=data, timeout=30)

for i in range(3):
    text, ref = get((first + i) % TOTAL + 1)
    sent = False
    try:
        png = make_image(text, ref, i == 0)
        if png:
            send_photo(png)
            sent = True
    except Exception as e:
        print("image failed:", e)
    if not sent:
        head = BASMALA + "\n\n" if i == 0 else ""
        send_text(head + f"{text} ﴿{ref}﴾")
