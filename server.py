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

PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
VIDEO_CACHE_DIR = os.path.join(STATIC_DIR, "video_cache")
os.makedirs(VIDEO_CACHE_DIR, exist_ok=True)

FFMPEG_PATH = r"C:\Users\pc\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
NODE_PATH = r"C:\Users\pc\AppData\Local\hermes\node\node.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# In-memory caches for lightning fast responses
search_cache = {}
stream_cache = {}
movies_cache = {}
movie_detail_cache = {}

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

        js_dict = {"node": {"path": NODE_PATH}} if os.path.exists(NODE_PATH) else {}
        ydl_opts = {
            "quiet": True,
            "js_runtimes": js_dict
        }
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
                    js_dict = {"node": {"path": NODE_PATH}} if os.path.exists(NODE_PATH) else {}
                    ydl_opts = {
                        "format": "bestaudio/best",
                        "noplaylist": True,
                        "quiet": True,
                        "extract_flat": True,
                        "js_runtimes": js_dict,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        res = ydl.extract_info(f"ytsearch15:{q}", download=False)
                        results = []
                        for entry in res.get("entries", []):
                            if not entry or not entry.get("id"):
                                continue
                            
                            duration_sec = entry.get("duration") or 0
                            mins = int(duration_sec) // 60
                            secs = int(duration_sec) % 60
                            duration_str = f"{mins}:{secs:02d}"

                            video_id = entry.get("id")
                            thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                            results.append({
                                "id": video_id,
                                "title": entry.get("title", "Unknown Title"),
                                "channel": entry.get("channel") or entry.get("uploader") or "Artist",
                                "duration": duration_str,
                                "duration_sec": duration_sec,
                                "thumbnail": thumb
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
                    js_dict = {"node": {"path": NODE_PATH}} if os.path.exists(NODE_PATH) else {}
                    ydl_opts = {
                        "format": "bestaudio[ext=m4a]/bestaudio/best",
                        "noplaylist": True,
                        "quiet": True,
                        "js_runtimes": js_dict,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                        stream_url = info.get("url")
                        
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

            elif path == "/api/movies":
                genre = query.get("genre", [""])[0].strip().lower()
                language = query.get("language", [""])[0].strip().lower()
                page = query.get("page", ["1"])[0].strip()
                try:
                    p_num = int(page)
                except ValueError:
                    p_num = 1

                cache_key = f"m_{genre}_{language}_{p_num}"
                if cache_key in movies_cache:
                    self.send_json(movies_cache[cache_key])
                    return

                if language:
                    base_url = f"https://vegamovie.website/language/{language}/"
                elif genre and genre != "all":
                    base_url = f"https://vegamovie.website/genre/{genre}/"
                else:
                    base_url = "https://vegamovie.website/genre/action/"

                req_url = base_url if p_num == 1 else f"{base_url}page/{p_num}/"

                try:
                    data = parse_vegamovies_page(req_url)
                    data["page"] = p_num
                    data["genre"] = genre or "action"
                    data["language"] = language
                    movies_cache[cache_key] = data
                    self.send_json(data)
                except Exception as e:
                    print("Error fetching movies:", e)
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
                    data = parse_vegamovies_detail(slug)
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
                    url = f"https://vegamovie.website/wp-admin/admin-ajax.php?action=movie_search&query={urllib.parse.quote(q)}"
                    req = urllib.request.Request(url, headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        raw = json.loads(resp.read().decode('utf-8'))

                    results = []
                    for item in raw:
                        link = item.get("link", "")
                        slug = link.strip("/").split("/")[-1] if link else ""
                        results.append({
                            "title": unescape(item.get("title", "")),
                            "slug": slug,
                            "link": link,
                            "image": item.get("image", "")
                        })

                    res_obj = {"results": results}
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
                    js_dict = {"node": {"path": NODE_PATH}} if os.path.exists(NODE_PATH) else {}
                    ydl_opts = {
                        "format": "bestaudio[ext=m4a]/bestaudio/best",
                        "noplaylist": True,
                        "quiet": True,
                        "js_runtimes": js_dict,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                        stream_url = info.get("url")
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
