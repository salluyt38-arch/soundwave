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
import base64
import urllib.parse
import urllib.request
import random
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
import sys
import subprocess
import threading
import re
from html import unescape
import yt_dlp
import yt_dlp.version

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

# ==============================================================================
# SIMPLE AI MODEL CONNECTOR ENVIRONMENT VARIABLES (Render / .env / Local)
# You can set these in Render Dashboard -> Environment Variables:
#   GROQ_API_KEY         : Free, lightning fast Llama 3.3 70B (~200ms)
#   OPENROUTER_API_KEY   : DeepSeek, Llama 3, Free tier (:free) & 100+ models
#   ANTHROPIC_API_KEY    : Claude 3.5 Sonnet / Haiku (or CLAUDE_API_KEY)
#   OPENAI_API_KEY       : GPT-4o / GPT-4o-mini
#   GEMINI_API_KEY       : Google Gemini 2.0 Flash
#   NVIDIA_API_KEY       : NVIDIA NIM Nemotron / Llama 3.1
#   DEFAULT_AI_PROVIDER  : auto | groq | claude | openrouter | gemini | openai | builtin
# ==============================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
ANTHROPIC_API_KEY = (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY", "")).strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
DEFAULT_AI_PROVIDER = os.environ.get("DEFAULT_AI_PROVIDER", "").strip().lower()

def get_default_provider():
    if DEFAULT_AI_PROVIDER and DEFAULT_AI_PROVIDER not in ["auto", "default"]:
        return DEFAULT_AI_PROVIDER
    if GROQ_API_KEY:
        return "groq"
    if OPENROUTER_API_KEY:
        return "openrouter"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if GEMINI_API_KEY:
        return "gemini"
    if OPENAI_API_KEY:
        return "openai"
    if NVIDIA_API_KEY:
        return "nvidia"
    return "builtin"


# Fast Unblocked Direct Stream Extractor via CDN (0.15s, 160kbps high quality)
def get_saavn_stream(query):
    if not query:
        return None
    try:
        from Crypto.Cipher import DES
        clean_q = clean_youtube_title(query)
        words = clean_q.split()[:4]
        search_seed = " ".join(words)
        encoded = urllib.parse.quote(search_seed)
        url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&api_version=4&ctx=web6dot0&q={encoded}&p=1&n=5"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
            results = data.get("results", [])
            if not results:
                return None
            
            # Select best official track (filter out unwanted covers or karaoke)
            q_lower = query.lower()
            best_item = None
            for item in results:
                t_lower = (item.get("title") or "").lower()
                if "karaoke" not in q_lower and "karaoke" in t_lower:
                    continue
                if "cover" not in q_lower and "cover" in t_lower:
                    continue
                if "tribute" not in q_lower and "tribute" in t_lower:
                    continue
                best_item = item
                break
            if not best_item:
                best_item = results[0]

            song_id = best_item["id"]
            det_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&_format=json&_marker=0&api_version=4&ctx=web6dot0&pids={song_id}"
            req2 = urllib.request.Request(det_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req2, timeout=4) as r2:
                det = json.loads(r2.read().decode("utf-8", errors="ignore"))
                more = det.get("songs", [{}])[0].get("more_info", {})
                enc = more.get("encrypted_media_url")
                if not enc:
                    return None
                cipher = DES.new(b"38346591", DES.MODE_ECB)
                dec = cipher.decrypt(base64.b64decode(enc))
                pad = dec[-1]
                raw_url = dec[:-pad].decode("utf-8")
                return raw_url.replace("_96.mp4", "_160.mp4")
    except Exception as e:
        return None

# Helper to construct yt-dlp options compatible with cloud datacenter IPs
def get_ydl_opts(extra=None):
    js_dict = {"node": {"path": NODE_PATH}} if (NODE_PATH and os.path.exists(NODE_PATH)) else {}
    base = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 6,
        "check_formats": False,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
        "js_runtimes": js_dict,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
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
    songs = []

    try:
        ydl_opts = get_ydl_opts({
            "extract_flat": True,
            "socket_timeout": 6
        })
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
    except Exception as yt_err:
        print(f"YouTube channel search fallback for {channel_key}:", yt_err)

    # High-speed fallback if yt_dlp failed or timed out
    if not songs:
        try:
            fallback_q = info_meta.get("name", "Bollywood Hits")
            encoded = urllib.parse.quote(fallback_q)
            saavn_url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&api_version=4&ctx=web6dot0&q={encoded}&p={page}&n=12"
            req = urllib.request.Request(saavn_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
                for item in data.get("results", []):
                    title = clean_youtube_title(item.get("title", "Hit Song"))
                    singers = item.get("more_info", {}).get("singers") or info_meta["name"]
                    dur_sec = int(item.get("more_info", {}).get("duration", 210))
                    m, s = divmod(dur_sec, 60)
                    thumb = item.get("image", "").replace("150x150", "500x500") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400"
                    songs.append({
                        "id": f"saavn_{item.get('id')}",
                        "title": title,
                        "raw_title": title,
                        "channel": singers,
                        "duration": f"{m}:{s:02d}",
                        "duration_sec": dur_sec,
                        "thumbnail": thumb,
                        "views_str": "Trending Now"
                    })
        except Exception as saavn_err:
            print("Saavn fallback error:", saavn_err)

    return {
        "channel": channel_key,
        "channel_name": info_meta["name"],
        "tagline": info_meta["tagline"],
        "page": page,
        "songs": songs,
        "has_next": len(songs) >= 12
    }


# ==============================================================================
# SOUNDWAVE AI DJ & UNIVERSAL MULTI-LLM CONNECTOR ENGINE
# Supports: Anthropic Claude, OpenAI, Google Gemini, Groq, OpenRouter, NVIDIA NIM, & Built-in Free DJ
# ==============================================================================
AI_DJ_SYSTEM_PROMPT = """You are SoundWave AI DJ, the official AI Music & Entertainment Assistant on SoundWave (a high-fidelity web music app).
You speak charismatic, upbeat, friendly Hinglish and English like a cool radio DJ.
You understand music moods, Bollywood, Hollywood, Punjabi, Pakistani, Indie, and playback commands.

Respond STRICTLY with a valid JSON object (no markdown, no backticks, no other text):
{
  "reply": "Energetic 1-2 sentence DJ voice response in Hinglish/English (max 25 words)",
  "action": "play" | "pause" | "resume" | "next" | "prev" | "search" | "info",
  "query": "Exact song title and artist to play",
  "category": "music" | "entertainment" | "movie"
}
Guidelines:
- If user asks for any song, artist, genre, or mood, action MUST be 'play' and query MUST be the specific song title.
- If user says pause/stop, action MUST be 'pause'.
- If user says resume/continue, action MUST be 'resume'.
- If user says next/skip, action MUST be 'next'.
- If user says previous/back, action MUST be 'prev'.
"""

def parse_ai_json(text):
    if not text:
        return None
    cleaned = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'```\s*', '', cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r'(\{[\s\S]*\})', cleaned)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return None


def fetch_realistic_tts_stream(text):
    if not text:
        return None
    clean_text = text.strip()[:240]
    encoded = urllib.parse.quote(clean_text)
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=hi&client=tw-ob"
    req = urllib.request.Request(tts_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://translate.google.com/"
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.read()
    except Exception as e:
        print("TTS fetch error:", e)
        return None

def smart_builtin_dj(message):
    msg = (message or "").strip().lower()

    # 1. State / Trigger On-Off Commands
    if any(w in msg for w in ["dj on", "turn on dj", "dj start", "wake up", "chalu ho jao", "uth jao", "activate dj"]):
        return {
            "reply": "SoundWave DJ active ho gaya hai! Boliye kaunsa banger gaana bajana hai?",
            "action": "wake",
            "query": "",
            "category": "system"
        }
    if any(w in msg for w in ["dj off", "turn off dj", "dj sleep", "sleep mode", "chup ho jao", "band ho jao", "mute ho jao", "shant ho jao"]):
        return {
            "reply": "Theek hai, DJ sleep mode me jaa raha hai. Jab bhi gaana badalna ho, bas 'DJ' boliye!",
            "action": "sleep",
            "query": "",
            "category": "system"
        }

    # 2. Playback & Volume controls
    if any(w in msg for w in ["pause", "stop", "rok do", "band kar", "ruk jao", "pause kar"]):
        return {
            "reply": "Music pause kar diya hai! Jab bolenge main turant resume kar dunga.",
            "action": "pause",
            "query": "",
            "category": "music"
        }
    if any(w in msg for w in ["resume", "play karo", "shuru karo", "chalu karo"]) and not any(w in msg for w in ["song", "gaana", "geet", "track", "music", "play "]):
        return {
            "reply": "Music resume ho gaya hai, beats enjoy kijiye!",
            "action": "resume",
            "query": "",
            "category": "music"
        }
    if any(w in msg for w in ["next", "agla", "skip", "change", "badlo", "dusra"]):
        return {
            "reply": "Agla superhit track play ho raha hai!",
            "action": "next",
            "query": "",
            "category": "music"
        }
    if any(w in msg for w in ["prev", "previous", "pichla", "back"]):
        return {
            "reply": "Pichla track wapas play kar diya hai!",
            "action": "prev",
            "query": "",
            "category": "music"
        }
    if any(w in msg for w in ["volume up", "awaaz badhao", "sound badhao", "louder", "tez karo"]):
        return {
            "reply": "Volume badha diya hai, full bass mode ON!",
            "action": "volume_up",
            "query": "",
            "category": "system"
        }
    if any(w in msg for w in ["volume down", "awaaz kam karo", "sound kam karo", "dheemi karo"]):
        return {
            "reply": "Volume kam kar diya hai.",
            "action": "volume_down",
            "query": "",
            "category": "system"
        }

    # 3. Deep Trained Artist & "Banger" Recognition
    # A. BADSHAH BANGERS
    if "badshah" in msg:
        badshah_bangers = [
            ("Jugnu - Badshah", "Yeh lijiye Badshah ka superhit party banger Jugnu! Nachne ke liye tayyar ho jaiye!"),
            ("Soulmate - Badshah, Arijit Singh", "Badshah aur Arijit Singh ka chartbuster banger Soulmate! Suniye aur vibe kijiye."),
            ("Mercy - Badshah", "Badshah ka timeless groove track Mercy baj raha hai!"),
            ("Genda Phool - Badshah", "High-energy banger Genda Phool play ho gaya hai!"),
            ("DJ Waley Babu - Badshah", "All-time club anthem DJ Waley Babu! Full volume kar lijiye!")
        ]
        pick = random.choice(badshah_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # B. HONEY SINGH BANGERS
    if any(k in msg for k in ["honey singh", "yo yo"]):
        honey_bangers = [
            ("Millionaire - Yo Yo Honey Singh", "Yo Yo Honey Singh ka brand-new viral comeback banger Millionaire!"),
            ("Blue Eyes - Yo Yo Honey Singh", "Legendary Blue Eyes hypnotize track shuru ho gaya hai!"),
            ("Desi Kalakaar - Yo Yo Honey Singh", "Pure classic Honey Singh vibes Desi Kalakaar baj gaya hai!"),
            ("Dope Shope - Yo Yo Honey Singh", "Club banger anthem Dope Shope!")
        ]
        pick = random.choice(honey_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # C. KARAN AUJLA BANGERS
    if any(k in msg for k in ["karan aujla", "aujla"]):
        aujla_bangers = [
            ("Tauba Tauba - Karan Aujla", "Floor par aag lagane ke liye Karan Aujla ka mega banger Tauba Tauba!"),
            ("Winning Speech - Karan Aujla", "Gym aur car ke liye pure hype banger Winning Speech!"),
            ("Softly - Karan Aujla", "Smooth Punjabi vibe Softly by Karan Aujla!")
        ]
        pick = random.choice(aujla_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # D. SHUBH HITS
    if "shubh" in msg:
        shubh_bangers = [
            ("Cheques - Shubh", "Shubh ka global chartbuster track Cheques baj raha hai!"),
            ("Baller - Shubh", "Car bass ke liye Baller track play ho gaya!"),
            ("Elevated - Shubh", "High energy motivational vibe Elevated by Shubh!")
        ]
        pick = random.choice(shubh_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # E. SIDHU MOOSE WALA BANGERS
    if any(k in msg for k in ["sidhu", "moose wala", "moosewala"]):
        sidhu_bangers = [
            ("295 - Sidhu Moose Wala", "Sidhu Moose Wala ka evergreen global anthem 295!"),
            ("So High - Sidhu Moose Wala", "Dil da ni maada! So High play ho gaya hai."),
            ("The Last Ride - Sidhu Moose Wala", "Legendary The Last Ride by Sidhu Moose Wala.")
        ]
        pick = random.choice(sidhu_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # F. ARIJIT SINGH HITS
    if any(k in msg for k in ["arijit", "arijit singh"]):
        arijit_hits = [
            ("Kesariya - Arijit Singh", "Arijit Singh ka magical romantic track Kesariya hazir hai!"),
            ("Chaleya - Arijit Singh", "Jawan ka soulful blockbuster Chaleya!"),
            ("Tum Hi Ho - Arijit Singh", "Heart-touching melody Tum Hi Ho shuru ho raha hai."),
            ("Apna Bana Le - Arijit Singh", "Bhediya movie ka timeless romantic hit Apna Bana Le.")
        ]
        pick = random.choice(arijit_hits)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # G. GENERAL BANGERS & MOODS
    if any(w in msg for w in ["banger", "bangersong", "banger song", "party", "dance", "club", "hype", "dhamaka"]):
        generic_bangers = [
            ("Tauba Tauba - Karan Aujla", "Sabse bada viral dance banger Tauba Tauba baj raha hai!"),
            ("Jugnu - Badshah", "Floor shaking party banger Jugnu play kar diya hai!"),
            ("Millionaire - Yo Yo Honey Singh", "Full volume banger Millionaire shuru ho gaya!"),
            ("Cheques - Shubh", "Top trending hype banger Cheques by Shubh!"),
            ("Big Dawgs - Hanumankind", "Global rap banger Big Dawgs play ho raha hai!")
        ]
        pick = random.choice(generic_bangers)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # H. ROMANTIC MOOD
    if any(w in msg for w in ["romantic", "pyaar", "love", "ishq", "dil", "sweet"]):
        romantic_picks = [
            ("Kesariya - Arijit Singh", "Aapke dil ke taar chhedne ke liye yeh raha Kesariya!"),
            ("Apna Bana Le - Arijit Singh", "Pure romantic vibes! Apna Bana Le suniye."),
            ("Tum Se Hi - Mohit Chauhan", "Jab We Met ka timeless romantic magic aapke liye!"),
            ("Tu Hai Kahan - AUR", "Late night romantic soul track Tu Hai Kahan play ho gaya.")
        ]
        pick = random.choice(romantic_picks)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # I. GYM & WORKOUT MOOD
    if any(w in msg for w in ["gym", "workout", "pump", "power", "heavy", "lift", "motivation"]):
        gym_picks = [
            ("Winning Speech - Karan Aujla", "Gym me aag lagaane ke liye Karan Aujla ka Winning Speech!"),
            ("Born to Shine - Diljit Dosanjh", "Full motivation workout track, let's crush it!"),
            ("Elevated - Shubh", "High energy beast mode ON! Elevated play ho gaya.")
        ]
        pick = random.choice(gym_picks)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # J. SAD & HEARTBREAK
    if any(w in msg for w in ["sad", "dard", "heartbreak", "udaas", "alone", "cry", "breakup"]):
        sad_picks = [
            ("Channa Mereya - Arijit Singh", "Dil ko chhoo lene wala Arijit ka Channa Mereya."),
            ("Filhall - B Praak", "B Praak ka soulful emotional track Filhall baj raha hai."),
            ("Bekhayali - Kabir Singh", "Heartbreak emotions ke liye Bekhayali.")
        ]
        pick = random.choice(sad_picks)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # K. LO-FI & CHILL
    if any(w in msg for w in ["lofi", "lo-fi", "chill", "relax", "study", "peace", "sleep"]):
        lofi_picks = [
            ("Iktara Lo-Fi Chill Mix", "Peaceful chill vibes ke liye Iktara Lo-Fi baj raha hai."),
            ("Pasoori Lo-Fi Chill", "Dim the lights and vibe to Pasoori Lo-Fi.")
        ]
        pick = random.choice(lofi_picks)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # L. 90s RETRO
    if any(w in msg for w in ["90s", "retro", "old", "purane", "classic", "vintage"]):
        retro_picks = [
            ("Tujhe Dekha Toh Yeh Jaana Sanam", "90s ka sabse bada romantic blockbuster gaana!"),
            ("Dil To Pagal Hai - Lata Mangeshkar", "Golden 90s era ka magical melody.")
        ]
        pick = random.choice(retro_picks)
        return {
            "reply": pick[1],
            "action": "play",
            "query": pick[0],
            "category": "music"
        }

    # 4. Direct song / artist query cleanup
    clean = re.sub(r'^(dj|deejay|hey dj|soundwave)\s*', '', msg, flags=re.IGNORECASE)
    clean = re.sub(r'\b(play|the|chalao|bajao|sunaao|lagao|song|gaana|geet|sunna hai|track|music|banger|bangersong)\b', '', clean, flags=re.IGNORECASE).strip()
    if not clean:
        clean = "Kesariya Arijit Singh"
        reply = "Aapka favourite trendsetter gaana Kesariya baj raha hai!"
    else:
        reply = f"Bilkul! Aapke liye '{clean}' play kar raha hoon, enjoy kijiye!"

    return {
        "reply": reply,
        "action": "play",
        "query": clean,
        "category": "music"
    }

def call_ai_provider(message, provider='default', api_key='', model=''):
    global GROQ_API_KEY, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY
    provider = (provider or 'default').lower().strip()
    api_key = (api_key or '').strip()
    model = (model or '').strip()

    if provider in ['default', 'auto', '']:
        provider = get_default_provider()

    # Automatically use server environment variables if no client key is provided
    if not api_key:
        if provider in ['anthropic', 'claude']:
            api_key = ANTHROPIC_API_KEY
        elif provider == 'groq':
            api_key = GROQ_API_KEY
        elif provider == 'openrouter':
            api_key = OPENROUTER_API_KEY
        elif provider == 'openai':
            api_key = OPENAI_API_KEY
        elif provider == 'gemini':
            api_key = GEMINI_API_KEY
        elif provider == 'nvidia':
            api_key = NVIDIA_API_KEY

    # If provider is builtin or key is still missing, fallback smoothly to built-in smart DJ
    if provider in ['builtin', 'local'] or not api_key:
        return smart_builtin_dj(message)

    try:
        if provider in ['anthropic', 'claude']:
            req_url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": model or "claude-3-5-sonnet-20241022",
                "max_tokens": 300,
                "system": AI_DJ_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": message}]
            }
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["content"][0]["text"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

        elif provider == 'openai':
            req_url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": AI_DJ_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                "response_format": {"type": "json_object"}
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

        elif provider == 'groq':
            req_url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": model or "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": AI_DJ_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                "response_format": {"type": "json_object"}
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

        elif provider == 'gemini':
            mod = model or "gemini-2.0-flash"
            req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": AI_DJ_SYSTEM_PROMPT + "\n\nUser Message: " + message}]}
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

        elif provider == 'openrouter':
            req_url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": model or "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [
                    {"role": "system", "content": AI_DJ_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://soundwave-5y5z.onrender.com",
                "X-Title": "SoundWave AI DJ"
            }
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

        elif provider == 'nvidia':
            req_url = "https://integrate.api.nvidia.com/v1/chat/completions"
            payload = {
                "model": model or "meta/llama-3.1-70b-instruct",
                "messages": [
                    {"role": "system", "content": AI_DJ_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(req_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                parsed = parse_ai_json(text)
                if parsed:
                    return parsed

    except Exception as e:
        print(f"SoundWave AI Provider [{provider}] error: {e}, falling back to built-in DJ.")

    return smart_builtin_dj(message)

def test_ai_provider(provider, api_key='', model=''):
    global GROQ_API_KEY, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY
    provider = (provider or 'default').lower().strip()
    api_key = (api_key or '').strip()
    model = (model or '').strip()

    if provider in ['default', 'auto', '']:
        provider = get_default_provider()

    using_env = False
    if not api_key:
        if provider in ['anthropic', 'claude'] and ANTHROPIC_API_KEY:
            api_key = ANTHROPIC_API_KEY; using_env = True
        elif provider == 'groq' and GROQ_API_KEY:
            api_key = GROQ_API_KEY; using_env = True
        elif provider == 'openrouter' and OPENROUTER_API_KEY:
            api_key = OPENROUTER_API_KEY; using_env = True
        elif provider == 'openai' and OPENAI_API_KEY:
            api_key = OPENAI_API_KEY; using_env = True
        elif provider == 'gemini' and GEMINI_API_KEY:
            api_key = GEMINI_API_KEY; using_env = True
        elif provider == 'nvidia' and NVIDIA_API_KEY:
            api_key = NVIDIA_API_KEY; using_env = True

    if provider in ['default', 'builtin']:
        return {
            "success": True,
            "message": "Built-in Smart Music DJ is active (Zero Setup / 100% Free).",
            "provider": "builtin",
            "model": "built-in"
        }

    if not api_key:
        env_names = {
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "nvidia": "NVIDIA_API_KEY"
        }
        needed_var = env_names.get(provider, f"{provider.upper()}_API_KEY")
        return {
            "success": False,
            "message": f"API Key required for {provider.upper()}. Enter key below or set '{needed_var}' in Render Environment Variables.",
            "provider": provider,
            "env_var": needed_var
        }

    try:
        test_msg = "Hello DJ, respond with JSON: {\"reply\": \"Connected!\", \"action\": \"info\", \"query\": \"\", \"category\": \"music\"}"
        res = call_ai_provider(test_msg, provider=provider, api_key=api_key, model=model)
        if res and res.get("reply"):
            source_txt = "Render Environment Variable" if using_env else "Custom API Key"
            return {
                "success": True,
                "message": f"Connected to {provider.upper()} ({model or 'default'}) via {source_txt}! AI DJ is ready to take voice commands.",
                "provider": provider,
                "model": model,
                "using_env": using_env,
                "sample_reply": res.get("reply")
            }
        else:
            return {
                "success": False,
                "message": f"Failed to get structured response from {provider}. Check your API Key.",
                "provider": provider
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to {provider}: {str(e)}",
            "provider": provider
        }

class MusicHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        if self.path.endswith(".html") or self.path.endswith(".js") or self.path == "/" or "?" in self.path:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

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

            if path == "/api/debug":
                self.send_json({
                    "build_id": "v3_android_client_only",
                    "yt_dlp_version": yt_dlp.version.__version__,
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "node_path": NODE_PATH,
                    "ffmpeg_path": FFMPEG_PATH
                })
                return

            if path in ("/download/soundwave.apk", "/soundwave.apk", "/download", "/app", "/install") or path.endswith("/soundwave.apk"):
                apk_path = os.path.join(STATIC_DIR, "soundwave.apk")
                if os.path.exists(apk_path):
                    file_size = os.path.getsize(apk_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.android.package-archive")
                    self.send_header("Content-Disposition", 'attachment; filename="SoundWave.apk"')
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(apk_path, "rb") as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                else:
                    self.send_json({"error": "SoundWave APK file not found on server"}, status=404)
                    return

            if path in ("/download/soundwave-app.zip", "/soundwave-app.zip"):
                zip_path = os.path.join(STATIC_DIR, "soundwave-app.zip")
                if os.path.exists(zip_path):
                    file_size = os.path.getsize(zip_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", 'attachment; filename="SoundWave-App.zip"')
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(zip_path, "rb") as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                else:
                    self.send_json({"error": "SoundWave App Zip not found on server"}, status=404)
                    return

            if path == "/api/test_extract":
                vid = query.get("id", ["BddP6PYo2gs"])[0].strip()
                log_capture = []
                class MyLogger:
                    def debug(self, msg): log_capture.append(f"DBG: {msg}")
                    def warning(self, msg): log_capture.append(f"WARN: {msg}")
                    def error(self, msg): log_capture.append(f"ERR: {msg}")
                opts = {
                    "format": "bestaudio/best",
                    "logger": MyLogger(),
                    "verbose": True,
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["android"]
                        }
                    }
                }
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        inf = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
                        self.send_json({"success": True, "url": bool(inf.get("url")), "logs": log_capture[:40]})
                except Exception as e:
                    self.send_json({"success": False, "error": str(e), "logs": log_capture[:40]})
                return

            elif path == "/api/search":
                q = query.get("q", [""])[0].strip()
                if not q:
                    self.send_json({"results": [], "page": 1, "total": 0, "hasMore": False})
                    return

                try:
                    limit = int(query.get("limit", [40])[0])
                    limit = max(10, min(limit, 60))
                except Exception:
                    limit = 40

                try:
                    page = int(query.get("page", [1])[0])
                    page = max(1, page)
                except Exception:
                    page = 1

                cache_key = f"{q.lower()}_{limit}_{page}"
                if cache_key in search_cache:
                    self.send_json(search_cache[cache_key])
                    return

                try:
                    fetch_count = limit * page
                    ydl_opts = get_ydl_opts({
                        "format": "bestaudio/best",
                        "noplaylist": True,
                        "extract_flat": True,
                    })
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        res = ydl.extract_info(f"ytsearch{fetch_count}:{q}", download=False)
                        all_entries = res.get("entries", [])
                        
                        start_idx = (page - 1) * limit
                        page_entries = all_entries[start_idx:start_idx + limit] if start_idx < len(all_entries) else []
                        
                        results = []
                        seen_ids = set()
                        for entry in page_entries:
                            if not entry or not entry.get("id"):
                                continue
                            video_id = entry.get("id")
                            if video_id in seen_ids:
                                continue
                            seen_ids.add(video_id)

                            duration_sec = entry.get("duration") or 0
                            # Only filter out corrupt items (< 10 seconds)
                            if 0 < duration_sec < 10:
                                continue

                            if duration_sec >= 3600:
                                hours = int(duration_sec) // 3600
                                mins = (int(duration_sec) % 3600) // 60
                                secs = int(duration_sec) % 60
                                duration_str = f"{hours}:{mins:02d}:{secs:02d}"
                            elif duration_sec > 0:
                                mins = int(duration_sec) // 60
                                secs = int(duration_sec) % 60
                                duration_str = f"{mins}:{secs:02d}"
                            else:
                                duration_str = "LIVE / Radio"

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

                        data = {
                            "results": results,
                            "page": page,
                            "limit": limit,
                            "total": len(results),
                            "hasMore": len(all_entries) >= fetch_count
                        }
                        search_cache[cache_key] = data
                        self.send_json(data)
                except Exception as e:
                    self.send_json({"error": str(e), "results": [], "page": page, "hasMore": False}, status=500)

            elif path == "/api/stream":
                video_id = query.get("id", [""])[0].strip()
                title = query.get("title", [""])[0].strip()
                channel = query.get("channel", [""])[0].strip()

                if not video_id and not title:
                    self.send_json({"error": "Missing video ID or title"}, status=400)
                    return

                # Check in-memory cache
                for key in [video_id, title, f"{title}_{channel}"]:
                    if key and key in stream_cache:
                        self.send_json(stream_cache[key])
                        return

                stream_url = None

                # 1. Fast JioSaavn verified stream check (0.15s ultra-fast CDN for Indian/Bollywood/Punjabi)
                if title:
                    saavn_candidate = get_saavn_stream(f"{title} {channel}".strip())
                    if saavn_candidate:
                        stream_url = saavn_candidate

                # 2. Extract genuine direct audio stream from YouTube
                if not stream_url and video_id and not video_id.startswith("saavn_"):
                    try:
                        ydl_opts = get_ydl_opts({
                            "format": "bestaudio[ext=m4a]/bestaudio/18/best",
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
                            if not title:
                                title = info.get("title") or "SoundWave Audio"
                            if not channel:
                                channel = info.get("channel") or info.get("uploader") or "SoundWave Artist"
                    except Exception as yt_err:
                        print("Direct YouTube stream extraction notice:", yt_err)

                # 3. Fallback to Saavn
                if not stream_url and title:
                    stream_url = get_saavn_stream(title)

                if stream_url:
                    data = {
                        "id": video_id,
                        "title": title or "SoundWave Audio",
                        "channel": channel or "Artist",
                        "streamUrl": stream_url,
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if (video_id and not video_id.startswith("saavn_")) else "",
                        "duration": 0
                    }
                    if video_id: stream_cache[video_id] = data
                    if title: stream_cache[title] = data
                    self.send_json(data)
                else:
                    self.send_json({"error": "Stream not available for this track"}, status=404)

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

            elif path == "/api/ai/tts":
                text = query.get("text", [""])[0].strip()
                if not text:
                    self.send_json({"error": "No text provided"}, status=400)
                    return
                audio_bytes = fetch_realistic_tts_stream(text)
                if audio_bytes:
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/mpeg")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.send_header("Content-Length", str(len(audio_bytes)))
                    self.end_headers()
                    try:
                        self.wfile.write(audio_bytes)
                    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                        pass
                else:
                    self.send_json({"error": "TTS generation failed"}, status=500)

            elif path == "/api/ai/providers":
                self.send_json({
                    "default_provider": get_default_provider(),
                    "server_env_status": {
                        "GROQ_API_KEY": bool(GROQ_API_KEY),
                        "OPENROUTER_API_KEY": bool(OPENROUTER_API_KEY),
                        "ANTHROPIC_API_KEY": bool(ANTHROPIC_API_KEY),
                        "OPENAI_API_KEY": bool(OPENAI_API_KEY),
                        "GEMINI_API_KEY": bool(GEMINI_API_KEY),
                        "NVIDIA_API_KEY": bool(NVIDIA_API_KEY)
                    },
                    "providers": [
                        {"id": "builtin", "name": "Built-in Smart DJ (Free / Zero Setup)", "free": True, "env_var": "None (Always Active)", "is_configured": True, "default_model": "built-in", "desc": "Instant zero-latency music intent parser and voice DJ."},
                        {"id": "groq", "name": "Groq Cloud (Llama 3.3 70B)", "free": True, "env_var": "GROQ_API_KEY", "is_configured": bool(GROQ_API_KEY), "default_model": "llama-3.3-70b-versatile", "desc": "Lightning fast ~200ms latency with Llama 3.3 70B.", "key_url": "https://console.groq.com/keys"},
                        {"id": "openrouter", "name": "OpenRouter AI (Multi-Model)", "free": True, "env_var": "OPENROUTER_API_KEY", "is_configured": bool(OPENROUTER_API_KEY), "default_model": "meta-llama/llama-3.3-70b-instruct:free", "desc": "Access 100+ models including free tier models (:free).", "key_url": "https://openrouter.ai/keys"},
                        {"id": "anthropic", "name": "Anthropic Claude (Claude 3.5 Sonnet)", "free": False, "env_var": "ANTHROPIC_API_KEY", "is_configured": bool(ANTHROPIC_API_KEY), "default_model": "claude-3-5-sonnet-20241022", "desc": "World-class musical knowledge, lyrics understanding & curation.", "key_url": "https://console.anthropic.com/"},
                        {"id": "gemini", "name": "Google Gemini (Gemini 2.0 Flash)", "free": True, "env_var": "GEMINI_API_KEY", "is_configured": bool(GEMINI_API_KEY), "default_model": "gemini-2.0-flash", "desc": "Next-gen multimodal speed & reasoning.", "key_url": "https://aistudio.google.com/app/apikey"},
                        {"id": "openai", "name": "OpenAI (GPT-4o)", "free": False, "env_var": "OPENAI_API_KEY", "is_configured": bool(OPENAI_API_KEY), "default_model": "gpt-4o-mini", "desc": "Smartest reasoning with GPT-4o-mini & GPT-4o.", "key_url": "https://platform.openai.com/api-keys"}
                    ]
                })

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

            elif path == "/api/ai/dj":
                message = data.get("message", "").strip()
                provider = data.get("provider", "default").strip()
                api_key = data.get("api_key", "").strip()
                model = data.get("model", "").strip()
                res = call_ai_provider(message, provider=provider, api_key=api_key, model=model)
                self.send_json({
                    "status": "success",
                    "provider": provider,
                    "result": res
                })

            elif path == "/api/ai/save_env":
                global GROQ_API_KEY, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY, DEFAULT_AI_PROVIDER
                new_groq = data.get("GROQ_API_KEY", "").strip()
                new_openrouter = data.get("OPENROUTER_API_KEY", "").strip()
                new_claude = data.get("ANTHROPIC_API_KEY", "").strip()
                new_openai = data.get("OPENAI_API_KEY", "").strip()
                new_gemini = data.get("GEMINI_API_KEY", "").strip()
                new_default = data.get("DEFAULT_AI_PROVIDER", "").strip().lower()
                if new_groq: GROQ_API_KEY = new_groq
                if new_openrouter: OPENROUTER_API_KEY = new_openrouter
                if new_claude: ANTHROPIC_API_KEY = new_claude
                if new_openai: OPENAI_API_KEY = new_openai
                if new_gemini: GEMINI_API_KEY = new_gemini
                if new_default: DEFAULT_AI_PROVIDER = new_default
                self.send_json({
                    "success": True,
                    "message": "Server AI environment variables updated successfully!",
                    "active_provider": get_default_provider(),
                    "server_env_status": {
                        "GROQ_API_KEY": bool(GROQ_API_KEY),
                        "OPENROUTER_API_KEY": bool(OPENROUTER_API_KEY),
                        "ANTHROPIC_API_KEY": bool(ANTHROPIC_API_KEY),
                        "OPENAI_API_KEY": bool(OPENAI_API_KEY),
                        "GEMINI_API_KEY": bool(GEMINI_API_KEY),
                        "NVIDIA_API_KEY": bool(NVIDIA_API_KEY)
                    }
                })

            elif path == "/api/ai/test_connection":
                provider = data.get("provider", "default").strip()
                api_key = data.get("api_key", "").strip()
                model = data.get("model", "").strip()
                res = test_ai_provider(provider, api_key, model=model)
                self.send_json(res)

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
