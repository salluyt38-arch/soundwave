import urllib.request
import re

url = "https://vegamovie.website/movie/colony/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
except Exception as e:
    print("Error:", e)
    html = ""

print("HTML length:", len(html))
# Let's search for download buttons, iframes, video tags, or links with 1080p / 720p / 480p
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
    href = m.group(1)
    text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    if any(w in href.lower() or w in text.lower() for w in ['1080p', '720p', '480p', 'download', 'watch', 'stream', 'play', 'server', 'drive']):
        print(f"LINK: {text} --> {href}")

# Find any iframes or players
for ifr in re.findall(r'<iframe[^>]+src="([^"]+)"', html):
    print("IFRAME:", ifr)

# Find sections or headings
for h in re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', html):
    print("HEADING:", re.sub(r'<[^>]+>', '', h).strip())
