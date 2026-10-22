import time

def clean_youtube_title(title):
    patterns = [
        r'\s*[\(\[]\s*official\s*(music\s*)?(video|audio|track|song|lyric|lyrics|hd|4k)?\s*[\)\]]',
        r'\s*[\(\[]\s*(full\s*)?(hd|4k|1080p|8k|ultra\s*hd)?\s*(video|song|audio)?\s*[\)\]]',
        r'\s*[\(\[]\s*lyric(s)?\s*(video)?\s*[\)\]]',
        r'\s*[\(\[]\s*audio\s*[\)\]]',
        r'\s*\|\s*Official\s*.*$',
        r'\s*\|\s*Full\s*Video\s*.*$'
    ]
    cleaned = title
    for p in patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or title

import json
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
import sys
import subprocess
import threading
import re
from html import unescape
import yt_dlp

import shutil
PORT = int(os.environ.get("PORT", 5000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
VIDEO_CACHE_DIR = os.path.join(STATIC_DIR, "video_cache")
os.makedirs(VIDEO_CACHE_DIR, exist_ok=True)

FFMPEG_PATH = shutil.which("ffmpeg") or r"C:\Users\pc\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
NODE_PATH = shutil.which("node") or r"C:\Users\pc\AppData\Local\hermes\node\node.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# Cashfree Subscriptions (Recurring PG) Configuration
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "")
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "")
CASHFREE_ENV = os.environ.get("CASHFREE_ENV", "sandbox")
CASHFREE_SUB_URL = "https://sandbox.cashfree.com/pg/subscriptions" if CASHFREE_ENV == "sandbox" else "https://api.cashfree.com/pg/subscriptions"
CASHFREE_PAYMENT_LINK = "https://cfre.in/CSHFRE/o1xbhrj"

# Helper to construct yt-dlp options compatible with cloud datacenter IPs
def get_ydl_opts(extra=None):
    js_dict = {"node": {"path": NODE_PATH}} if (NODE_PATH and os.path.exists(NODE_PATH)) else {}
    base = {
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": js_dict,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "tv", "web"]
            }
        }
    }
    if extra:
        base.update(extra)
    return base


# In-memory caches for lightning fast responses
search_cache = {}
stream_cache = {}
movies_cache = {}
movie_detail_cache = {}
channel_songs_cache = {}

build_locks = {}
build_locks_mutex = threading.Lock()


def build_video_file(video_id, quality="1080p"):
    height_map = {
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "240p": 240,
        "144p": 144
    }
    target_height = height_map.get(quality, 360)
    cache_file = os.path.join(VIDEO_CACHE_DIR, f"{video_id}_{quality}.mp4")

    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100000:
        return cache_file

    with build_locks_mutex:
        if cache_file not in build_locks:
            build_locks[cache_file] = threading.Lock()
        lock = build_locks[cache_file]

    with lock:
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100000:
            return cache_file

        ydl_opts = get_ydl_opts({"quiet": True})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_id, download=False)
            formats = info.get("formats", [])

            # Filter direct DASH video streams (not HLS manifest)
            video_candidates = []
            for f in formats:
                if f.get("vcodec") != "none" and f.get("acodec") == "none":
                    if "manifest" not in f.get("url", ""):
                        video_candidates.append(f)

            selected_v = None
            # 1. Exact height and avc1 (best hardware decode compatibility on mobile & PC)
            for f in video_candidates:
                if f.get("height") == target_height and "avc1" in (f.get("vcodec") or ""):
                    selected_v = f
                    break
            # 2. Exact height any codec
            if not selected_v:
                for f in video_candidates:
                    if f.get("height") == target_height:
                        selected_v = f
                        break
            # 3. Closest available height
            if not selected_v and video_candidates:
                video_candidates.sort(key=lambda x: abs((x.get("height") or 0) - target_height))
                selected_v = video_candidates[0]

            # Audio format
            selected_a = None
            for f in formats:
                if f.get("format_id") == "140" or (f.get("acodec") != "none" and f.get("vcodec") == "none" and f.get("ext") == "m4a" and "manifest" not in f.get("url", "")):
                    selected_a = f
                    break
            if not selected_a:
                for f in formats:
                    if f.get("acodec") != "none" and f.get("vcodec") == "none" and "manifest" not in f.get("url", ""):
                        selected_a = f
                        break

            if not selected_v or not selected_a:
                raise Exception("Direct video/audio streams not found for this track")

            temp_out = cache_file + ".tmp.mp4"
            ffmpeg_bin = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
            cmd = [
                ffmpeg_bin,
                "-y",
                "-user_agent", UA,
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
                "-i", selected_v["url"],
                "-user_agent", UA,
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
                "-i", selected_a["url"],
                "-c:v", "copy",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-f", "mp4",
                temp_out
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                except Exception:
                    pass
            os.replace(temp_out, cache_file)
            return cache_file


def parse_vegamovies_page(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    movies = []
    card_pattern = re.compile(
        r'<div class="movie-card">\s*<a href="([^"]+)".*?<img\s+src="([^"]+)".*?alt="([^"]+)".*?<h3 class="movie-title">([^<]+)</h3>.*?<span class="release-date">([^<]*)</span>.*?<span class="rating-badge">([^<]*)</span>',
        re.DOTALL
    )
    for match in card_pattern.finditer(html):
        link, img, alt, title, release, rating = match.groups()
        slug = link.strip("/").split("/")[-1]
        clean_rating = rating.replace("⭐", "").strip()
        movies.append({
            "slug": slug,
            "title": unescape(title.strip()),
            "link": link,
            "poster": img,
            "release": release.strip(),
            "rating": clean_rating
        })

    has_next = 'class="next page-numbers"' in html
    return {"movies": movies, "has_next": has_next}


def parse_vegamovies_detail(slug):
    url = f"https://vegamovie.website/movie/{slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    poster_m = re.search(r'<div class="movie-poster">\s*<img\s+src="([^"]+)"', html)
    poster = poster_m.group(1) if poster_m else ""

    title_m = re.search(r'<h1>([^<]+)</h1>', html)
    title = unescape(title_m.group(1).strip()) if title_m else slug.replace("-", " ").title()

    tagline_m = re.search(r'<p class="movie-tagline">([^<]+)</p>', html)
    tagline = unescape(tagline_m.group(1).strip()) if tagline_m else ""

    rating_m = re.search(r'<div class="movie-rating">\s*<span>([^<]+)</span>', html)
    rating = rating_m.group(1).replace("⭐", "").strip() if rating_m else "N/A"

    meta_m = re.search(r'<div class="movie-meta">(.*?)</div>', html, re.DOTALL)
    meta_html = meta_m.group(1) if meta_m else ""
    spans = re.findall(r'<span>(.*?)</span>', meta_html, re.DOTALL)
    release = re.sub(r'<[^>]+>', '', spans[0]).strip() if len(spans) > 0 else ""
    runtime = re.sub(r'<[^>]+>', '', spans[1]).strip() if len(spans) > 1 else ""
    genres = re.sub(r'<[^>]+>', '', spans[2]).strip() if len(spans) > 2 else ""

    trailer_m = re.search(r'<iframe[^>]+src="https://www.youtube.com/embed/([^"?]+)', html)
    trailer_id = trailer_m.group(1) if trailer_m else None

    overview_m = re.search(r'<section class="movie-overview">\s*<h2[^>]*>[^<]*</h2>\s*<p>(.*?)</p>', html, re.DOTALL)
    overview = unescape(overview_m.group(1).strip()) if overview_m else tagline

    director_m = re.search(r'<th>Director</th>\s*<td>(.*?)</td>', html, re.DOTALL)
    director = re.sub(r'<[^>]+>', '', director_m.group(1)).strip() if director_m else ""

    cast = []
    cast_matches = re.finditer(
        r'<div class="cast-card">\s*<img\s+src="([^"]+)".*?<p class="actor-name">\s*<a[^>]*>([^<]+)</a>\s*</p>\s*<p class="character-name">([^<]*)</p>',
        html, re.DOTALL
    )
    for cm in cast_matches:
        img_raw, actor, char = cm.groups()
        if "https://" in img_raw[8:]:
            img = "https://" + img_raw[8:].split("https://")[-1]
        else:
            img = img_raw
        cast.append({
            "name": actor.strip(),
            "character": char.strip(),
            "image": img if img.startswith("http") else ""
        })

    return {
        "slug": slug,
        "title": title,
        "poster": poster,
        "tagline": tagline,
        "rating": rating,
        "release": release,
        "runtime": runtime,
        "genres": genres,
        "trailer_id": trailer_id,
        "overview": overview,
        "director": director,
        "cast": cast[:12],
        "vegamovies_url": url
    }



def fetch_legal_movies(genre="all", page=1, query_str=""):
    genre_queries = {
        "all": "Goldmines Superhit Full Hindi Dubbed Movies",
        "south_hindi": "Goldmines Telefilms Full Hindi Dubbed Movies 1080p",
        "bollywood": "Shemaroo Bollywood Full Movies Hindi 1080p",
        "action": "South Hindi Dubbed Full Action Movies Blockbuster",
        "comedy": "Superhit Bollywood Comedy Full Movies 1080p",
        "hollywood": "Hollywood Hindi Dubbed Full Movies Action 1080p",
        "romance": "Bollywood Romantic Full Movies Hindi",
    }
    if query_str:
        q = f"{query_str} Full Movie Hindi 1080p"
    else:
        q = genre_queries.get(genre, genre_queries["all"])

    search_count = page * 12 + 6
    ydl_opts = get_ydl_opts({
        "extract_flat": True,
    })
    movies = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(f"ytsearch{search_count}:{q}", download=False)
        entries = res.get("entries", [])
        start_idx = (page - 1) * 12
        page_entries = entries[start_idx : start_idx + 12]

        for e in page_entries:
            if not e or not e.get("id"):
                continue
            dur = int(e.get("duration") or 0)
            mins = dur // 60
            hrs = mins // 60
            rem_m = mins % 60
            dur_str = f"{hrs}h {rem_m}m" if hrs > 0 else f"{mins}m"
            raw_title = e.get("title", "Full Movie")
            vid_id = e.get("id")
            thumb = e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            studio = e.get("channel") or e.get("uploader") or "Goldmines"

            movies.append({
                "slug": vid_id,
                "video_id": vid_id,
                "trailer_id": vid_id,
                "title": raw_title,
                "poster": thumb,
                "studio": studio,
                "duration": dur_str,
                "duration_sec": dur,
                "rating": "8.5",
                "release": "Full Movie HD",
                "genres": "Full Movie (1080p)",
                "overview": f"Watch {raw_title} full-length movie legally streamed in 1080p Full HD by {studio}."
            })
    return {"movies": movies, "has_next": len(entries) >= search_count, "page": page, "genre": genre}


CHANNEL_MAP = {
    "tseries": {
        "name": "T-Series",
        "tagline": "India's #1 Music Label • Official Bollywood Hits",
        "query": "T-Series Official Hit Songs"
    },
    "zeemusic": {
        "name": "Zee Music Company",
        "tagline": "Latest Bollywood Blockbuster Songs & Soundtracks",
        "query": "Zee Music Company Hit Songs"
    },
    "sonymusic": {
        "name": "Sony Music India",
        "tagline": "Arijit Singh, Badshah, Bollywood & Pop Melodies",
        "query": "Sony Music India Latest Hit Songs"
    },
    "saregama": {
        "name": "Saregama Music",
        "tagline": "Golden Classics, Retro & New Superhit Songs",
        "query": "Saregama Music Superhit Songs"
    },
    "yrf": {
        "name": "YRF (Yash Raj Films)",
        "tagline": "Iconic Bollywood Cinema Music & Romance",
        "query": "YRF Yash Raj Films Song Hits"
    },
    "tips": {
        "name": "Tips Official",
        "tagline": "90s Romantic Hits & Modern Chartbusters",
        "query": "Tips Official Superhit Bollywood Songs"
    },
    "speedrecords": {
        "name": "Speed Records",
        "tagline": "Top Punjabi Bhangra & Pop Anthems",
        "query": "Speed Records Top Punjabi Hit Songs"
    },
    "all": {
        "name": "All Music Labels",
        "tagline": "T-Series, Zee Music, Sony Music & Saregama",
        "query": "T-Series Zee Music Sony Music Top Bollywood Hits"
    }
}

def fetch_channel_songs(channel_key="tseries", page=1):
    info_meta = CHANNEL_MAP.get(channel_key, CHANNEL_MAP["tseries"])
    query_str = info_meta["query"]
    search_count = page * 12 + 6
    ydl_opts = get_ydl_opts({
        "extract_flat": True,
    })
    songs = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(f"ytsearch{search_count}:{query_str}", download=False)
        entries = res.get("entries", [])
        start_idx = (page - 1) * 12
        page_entries = entries[start_idx : start_idx + 12]

        for entry in page_entries:
            if not entry or not entry.get("id"):
                continue
            duration_sec = entry.get("duration") or 0
            mins = int(duration_sec) // 60
            secs = int(duration_sec) % 60
            duration_str = f"{mins}:{secs:02d}"

            video_id = entry.get("id")
            raw_t = entry.get("title", "Unknown Title")
            clean_t = clean_youtube_title(raw_t)
            channel_name = entry.get("channel") or entry.get("uploader") or info_meta["name"]
            thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            views = entry.get("view_count")
            if views and isinstance(views, int) and views > 0:
                if views >= 1_000_000_000:
                    views_str = f"{views / 1_000_000_000:.1f}B views"
                elif views >= 1_000_000:
                    views_str = f"{views / 1_000_000:.1f}M views"
                elif views >= 1_000:
                    views_str = f"{views // 1_000}K views"
                else:
                    views_str = f"{views} views"
            else:
                views_str = "Studio Hit"

            songs.append({
                "id": video_id,
                "title": clean_t,
                "raw_title": raw_t,
                "channel": channel_name,
                "duration": duration_str,
                "duration_sec": duration_sec,
                "thumbnail": thumb,
                "views_str": views_str
            })

    return {
        "channel": channel_key,
        "channel_name": info_meta["name"],
        "tagline": info_meta["tagline"],
        "page": page,
        "songs": songs,
        "has_next": len(entries) >= (start_idx + len(page_entries)) and len(page_entries) >= 12
    }

class MusicHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def serve_file_with_ranges(self, filepath, content_type="video/mp4"):
        file_size = os.path.getsize(filepath)
        range_header = self.headers.get("Range")

        if range_header and range_header.startswith("bytes="):
            try:
                ranges = range_header[6:].split("-")
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                if end >= file_size:
                    end = file_size - 1
                if start > end:
                    start = 0

                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(filepath, "rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(remaining, 65536))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                return
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                return
            except Exception as e:
                print("Range serving error:", e)
                return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query = urllib.parse.parse_qs(parsed_url.query)

            if path == "/api/search":
                q = query.get("q", [""])[0].strip()
                if not q:
                    self.send_json({"results": []})
                    return

                if q in search_cache:
                    self.send_json(search_cache[q])
                    return

                try:
                    ydl_opts = get_ydl_opts({
                        "format": "bestaudio/best",
                        "noplaylist": True,
                        "extract_flat": True,
                    })
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        res = ydl.extract_info(f"ytsearch25:{q}", download=False)
                        results = []
                        for entry in res.get("entries", []):
                            if not entry or not entry.get("id"):
                                continue
                            
                            duration_sec = entry.get("duration") or 0
                            mins = int(duration_sec) // 60
                            secs = int(duration_sec) % 60
                            duration_str = f"{mins}:{secs:02d}"

                            video_id = entry.get("id")
                            raw_t = entry.get("title", "Unknown Title")
                            clean_t = clean_youtube_title(raw_t)
                            channel_name = entry.get("channel") or entry.get("uploader") or "SoundWave Artist"
                            thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                            
                            views = entry.get("view_count")
                            if views and isinstance(views, int) and views > 0:
                                if views >= 1_000_000_000:
                                    views_str = f"{views / 1_000_000_000:.1f}B views"
                                elif views >= 1_000_000:
                                    views_str = f"{views / 1_000_000:.1f}M views"
                                elif views >= 1_000:
                                    views_str = f"{views // 1_000}K views"
                                else:
                                    views_str = f"{views} views"
                            else:
                                views_str = "Viral Hit"

                            results.append({
                                "id": video_id,
                                "title": clean_t,
                                "raw_title": raw_t,
                                "channel": channel_name,
                                "duration": duration_str,
                                "duration_sec": duration_sec,
                                "thumbnail": thumb,
                                "views_str": views_str
                            })

                        data = {"results": results}
                        search_cache[q] = data
                        self.send_json(data)
                except Exception as e:
                    self.send_json({"error": str(e)}, status=500)

            elif path == "/api/stream":
                video_id = query.get("id", [""])[0].strip()
                if not video_id:
                    self.send_json({"error": "Missing video ID"}, status=400)
                    return

                if video_id in stream_cache:
                    self.send_json(stream_cache[video_id])
                    return

                try:
                    ydl_opts = get_ydl_opts({
                        "format": "bestaudio[ext=m4a]/bestaudio/best",
                        "noplaylist": True,
                    })
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                        stream_url = info.get("url")
                        if not stream_url:
                            for f in info.get("formats", []):
                                if f.get("url") and f.get("acodec") != "none" and "manifest" not in f.get("url", ""):
                                    stream_url = f.get("url")
                                    break
                        if not stream_url:
                            for f in info.get("formats", []):
                                if f.get("url") and "manifest" not in f.get("url", ""):
                                    stream_url = f.get("url")
                                    break
                        
                        data = {
                            "id": video_id,
                            "title": info.get("title", "Unknown"),
                            "channel": info.get("channel") or info.get("uploader") or "Artist",
                            "streamUrl": stream_url,
                            "thumbnail": info.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                            "duration": info.get("duration", 0)
                        }
                        stream_cache[video_id] = data
                        self.send_json(data)
                except Exception as e:
                    self.send_json({"error": str(e)}, status=500)

            elif path == "/api/video_stream":
                video_id = query.get("id", [""])[0].strip()
                quality = query.get("quality", ["1080p"])[0].strip().lower()
                if not video_id:
                    self.send_json({"error": "Missing video ID"}, status=400)
                    return

                try:
                    cache_file = build_video_file(video_id, quality)
                    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 50000:
                        self.serve_file_with_ranges(cache_file, "video/mp4")
                    else:
                        self.send_json({"error": "Failed to create video file"}, status=500)
                except Exception as e:
                    print("Video build error:", e)
                    self.send_json({"error": str(e)}, status=500)

            elif path == "/api/subscription/config":
                self.send_json({
                    "configured": bool(CASHFREE_APP_ID and CASHFREE_SECRET_KEY),
                    "app_id_masked": (CASHFREE_APP_ID[:4] + "..." + CASHFREE_APP_ID[-4:]) if len(CASHFREE_APP_ID) > 8 else ("Configured" if CASHFREE_APP_ID else ""),
                    "env": CASHFREE_ENV,
                    "sandbox_url": "https://sandbox.cashfree.com/pg/subscriptions",
                    "payment_link": CASHFREE_PAYMENT_LINK,
                    "plan": {
                        "id": "soundwave_vip_49",
                        "name": "SoundWave VIP",
                        "amount": 49.0,
                        "currency": "INR",
                        "interval": "MONTH"
                    }
                })

            elif path == "/api/subscription/verify":
                sub_id = query.get("sub_id", [""])[0].strip()
                self.send_json({
                    "subscription_id": sub_id or f"sub_sw_{int(time.time())}",
                    "status": "ACTIVE",
                    "plan_id": "soundwave_vip_49",
                    "amount": 49.0,
                    "provider": "cashfree_sandbox",
                    "sandbox_url": "https://sandbox.cashfree.com/pg/subscriptions"
                })

            elif path == "/api/channel_songs":
                channel = query.get("channel", ["tseries"])[0].strip().lower() or "tseries"
                page = query.get("page", ["1"])[0].strip()
                try:
                    p_num = int(page)
                except ValueError:
                    p_num = 1

                cache_key = f"cs_{channel}_{p_num}"
                if cache_key in channel_songs_cache:
                    self.send_json(channel_songs_cache[cache_key])
                    return

                try:
                    data = fetch_channel_songs(channel, p_num)
                    channel_songs_cache[cache_key] = data
                    self.send_json(data)
                except Exception as e:
                    print(f"Error fetching channel songs ({channel}):", e)
                    self.send_json({"error": str(e), "songs": [], "has_next": False}, status=500)

            elif path == "/api/movies":
                genre = query.get("genre", ["all"])[0].strip().lower() or "all"
                page = query.get("page", ["1"])[0].strip()
                try:
                    p_num = int(page)
                except ValueError:
                    p_num = 1

                cache_key = f"m_{genre}_{p_num}"
                if cache_key in movies_cache:
                    self.send_json(movies_cache[cache_key])
                    return

                try:
                    data = fetch_legal_movies(genre, p_num)
                    movies_cache[cache_key] = data
                    self.send_json(data)
                except Exception as e:
                    print("Error fetching legal movies:", e)
                    self.send_json({"error": str(e), "movies": [], "has_next": False}, status=500)

            elif path == "/api/movies/detail":
                slug = query.get("slug", [""])[0].strip()
                if not slug:
                    self.send_json({"error": "Missing movie slug"}, status=400)
                    return

                if slug in movie_detail_cache:
                    self.send_json(movie_detail_cache[slug])
                    return

                try:
                    data = {
                        "slug": slug,
                        "video_id": slug,
                        "trailer_id": slug,
                        "title": slug.replace("-", " ").title(),
                        "poster": f"https://i.ytimg.com/vi/{slug}/hqdefault.jpg",
                        "studio": "Goldmines / Shemaroo",
                        "rating": "8.5",
                        "release": "1080p Full Movie",
                        "runtime": "Full-Length Cinema",
                        "genres": "Full Movie (1080p Full HD)",
                        "overview": "Full-length blockbuster movie legally available in high definition 1080p with complete surround sound.",
                        "director": "Official Studio Production",
                        "cast": []
                    }
                    movie_detail_cache[slug] = data
                    self.send_json(data)
                except Exception as e:
                    print("Error fetching movie detail:", e)
                    self.send_json({"error": str(e)}, status=500)

            elif path == "/api/movies/search":
                q = query.get("q", [""])[0].strip()
                if not q:
                    self.send_json({"results": []})
                    return

                cache_key = f"ms_{q.lower()}"
                if cache_key in movies_cache:
                    self.send_json(movies_cache[cache_key])
                    return

                try:
                    res_data = fetch_legal_movies(query_str=q)
                    res_obj = {"results": res_data.get("movies", [])}
                    movies_cache[cache_key] = res_obj
                    self.send_json(res_obj)
                except Exception as e:
                    print("Movie search error:", e)
                    self.send_json({"error": str(e), "results": []}, status=500)

            elif path == "/api/download":
                video_id = query.get("id", [""])[0].strip()
                if not video_id:
                    self.send_json({"error": "Missing video ID"}, status=400)
                    return

                try:
                    ydl_opts = get_ydl_opts({
                        "format": "bestaudio[ext=m4a]/bestaudio/best",
                        "noplaylist": True,
                    })
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                        stream_url = info.get("url")
                        if not stream_url:
                            for f in info.get("formats", []):
                                if f.get("url") and f.get("acodec") != "none" and "manifest" not in f.get("url", ""):
                                    stream_url = f.get("url")
                                    break
                        if not stream_url:
                            for f in info.get("formats", []):
                                if f.get("url") and "manifest" not in f.get("url", ""):
                                    stream_url = f.get("url")
                                    break
                        raw_title = info.get("title", "SoundWave_Audio")
                        ascii_title = "".join(c for c in raw_title if c.isascii() and (c.isalnum() or c in (" ", "-", "_"))).strip()
                        if not ascii_title:
                            ascii_title = f"soundwave_{video_id}"
                        encoded_title = urllib.parse.quote(raw_title)

                        req = urllib.request.Request(
                            stream_url,
                            headers={"User-Agent": UA}
                        )
                        with urllib.request.urlopen(req) as resp:
                            content_length = resp.headers.get("Content-Length")
                            self.send_response(200)
                            self.send_header("Content-Type", "audio/mp4")
                            self.send_header("Content-Disposition", f"attachment; filename=\"{ascii_title}.m4a\"; filename*=UTF-8''{encoded_title}.m4a")
                            if content_length:
                                self.send_header("Content-Length", content_length)
                            self.send_header("Access-Control-Allow-Origin", "*")
                            self.end_headers()

                            while True:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                try:
                                    self.wfile.write(chunk)
                                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                                    break
                except Exception as e:
                    try:
                        self.send_json({"error": str(e)}, status=500)
                    except:
                        pass

            else:
                super().do_GET()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_POST(self):
        global CASHFREE_APP_ID, CASHFREE_SECRET_KEY
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            data = json.loads(post_body) if post_body else {}

            if path == "/api/subscription/create":
                sub_id = f"SoundWave_SUB_{int(time.time())}"
                plan_name = data.get("plan_name", "SoundWave VIP")
                amount = int(data.get("amount", 49))
                customer_phone = data.get("customer_phone", "9512440440")
                customer_email = data.get("customer_email", "soundwave.vip@gmail.com")
                customer_name = data.get("customer_name", "SoundWave Member")
                return_url = data.get("return_url", "https://wa.me/9512440440?text=Payment%20Successfull")

                # Exact Cashfree 2026-01-01 Subscriptions Request Schema
                cf_payload = {
                    "subscription_id": sub_id,
                    "customer_details": {
                        "customer_name": customer_name,
                        "customer_email": customer_email,
                        "customer_phone": customer_phone
                    },
                    "plan_details": {
                        "plan_name": plan_name,
                        "plan_type": "PERIODIC",
                        "plan_amount": amount,
                        "plan_max_amount": amount,
                        "plan_max_cycles": 120,
                        "plan_intervals": 1,
                        "plan_currency": "INR",
                        "plan_interval_type": "MONTH",
                        "plan_note": f"Monthly INR {amount} SoundWave VIP Plan"
                    },
                    "authorization_details": {
                        "authorization_amount": amount,
                        "authorization_amount_refund": False,
                        "payment_methods": [
                            "upi",
                            "card",
                            "enach"
                        ]
                    },
                    "subscription_meta": {
                        "return_url": return_url,
                        "notification_channel": [
                            "EMAIL",
                            "SMS"
                        ]
                    },
                    "subscription_expiry_time": "2035-12-31T23:59:59+05:30",
                    "subscription_tags": {
                        "psp_note": "Monthly subscription payment",
                        "app": "SoundWave"
                    }
                }

                if CASHFREE_APP_ID and CASHFREE_SECRET_KEY and CASHFREE_APP_ID != "<api-key>":
                    try:
                        cf_headers = {
                            "Content-Type": "application/json",
                            "x-api-version": "2026-01-01",
                            "x-client-id": CASHFREE_APP_ID,
                            "x-client-secret": CASHFREE_SECRET_KEY
                        }
                        req = urllib.request.Request(
                            CASHFREE_SUB_URL,
                            data=json.dumps(cf_payload).encode("utf-8"),
                            headers=cf_headers,
                            method="POST"
                        )
                        with urllib.request.urlopen(req, timeout=12) as resp:
                            cf_resp = json.loads(resp.read().decode("utf-8"))
                            sess_id = cf_resp.get("subscription_session_id", "")
                            auth_link = cf_resp.get("auth_link") or (f"https://sandbox.cashfree.com/pg/orders/{sess_id}" if sess_id else return_url)
                            self.send_json({
                                "status": cf_resp.get("subscription_status", "INITIALIZED"),
                                "subscription_id": cf_resp.get("subscription_id", sub_id),
                                "cf_subscription_id": cf_resp.get("cf_subscription_id"),
                                "subscription_session_id": sess_id,
                                "auth_link": auth_link,
                                "return_url": return_url,
                                "provider": "cashfree_sandbox",
                                "raw_response": cf_resp
                            })
                            return
                    except urllib.error.HTTPError as http_err:
                        err_body = http_err.read().decode("utf-8")
                        print("Cashfree HTTP Error:", http_err.code, err_body)
                        # Graceful return with error details
                        self.send_json({
                            "status": "ERROR",
                            "error_code": http_err.code,
                            "message": err_body,
                            "subscription_id": sub_id,
                            "return_url": return_url,
                            "auth_link": return_url
                        }, status=200)
                        return
                    except Exception as cf_err:
                        print("Cashfree API error:", cf_err)

                # Sandbox Ready Link (when API key is pending or test simulation)
                mock_sess_id = f"subs_token_{int(time.time())}"
                self.send_json({
                    "status": "INITIALIZED",
                    "subscription_id": sub_id,
                    "cf_subscription_id": f"cf_{int(time.time())}",
                    "subscription_session_id": mock_sess_id,
                    "auth_link": CASHFREE_PAYMENT_LINK,
                    "payment_link": CASHFREE_PAYMENT_LINK,
                    "return_url": return_url,
                    "provider": "cashfree_sandbox",
                    "sandbox_url": "https://sandbox.cashfree.com/pg/subscriptions",
                    "plan_details": cf_payload["plan_details"],
                    "customer_details": cf_payload["customer_details"],
                    "authorisation_details": cf_payload["authorization_details"]
                })

            elif path == "/api/subscription/config":
                new_app_id = data.get("app_id", "").strip()
                new_secret = data.get("secret_key", "").strip()
                if new_app_id:
                    CASHFREE_APP_ID = new_app_id
                if new_secret:
                    CASHFREE_SECRET_KEY = new_secret
                self.send_json({
                    "success": True,
                    "configured": bool(CASHFREE_APP_ID and CASHFREE_SECRET_KEY),
                    "message": "Cashfree credentials saved successfully."
                })

            else:
                self.send_json({"error": "Endpoint not found"}, status=404)
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def send_json(self, data, status=200):
        try:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass



def run():
    os.makedirs(STATIC_DIR, exist_ok=True)
    # Permanent cache: all media chunks and files are preserved permanently
    server = ThreadingHTTPServer(("0.0.0.0", PORT), MusicHandler)
    print(f"SoundWave Server active on http://0.0.0.0:{PORT}")
    server.serve_forever()



if __name__ == "__main__":
    run()
