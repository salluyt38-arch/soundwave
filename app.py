import os
import sys
import json
import time
import urllib.parse
import urllib.request
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import server

# Gradio Interface wrapper
with gr.Blocks(title="SoundWave HD Audio") as demo:
    gr.HTML("""
    <div style="text-align:center; padding: 40px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #121212; color: #fff; border-radius: 16px;">
        <h1 style="color: #1db954; font-size: 2.4rem; margin-bottom: 8px;">SoundWave HD Audio Engine</h1>
        <p style="color: #a7a7a7; font-size: 1.05rem; margin-bottom: 24px;">24/7 Cloud Streaming Backend Active (16 GB RAM • Unstoppable Background Audio).</p>
        <a href="/" target="_blank" style="display: inline-block; background: #1db954; color: #000; font-weight: 800; font-size: 1rem; padding: 14px 32px; border-radius: 30px; text-decoration: none; box-shadow: 0 4px 20px rgba(29, 185, 84, 0.4);">Launch SoundWave Player ➔</a>
    </div>
    """)

# FastAPI instance from Gradio
app = demo.app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search")
async def api_search(q: str = "", page: int = 1):
    q = q.strip()
    if not q:
        return JSONResponse({"results": []})
    if q in server.search_cache:
        return JSONResponse(server.search_cache[q])
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "extract_flat": True
        }
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
                clean_t = server.clean_youtube_title(raw_t)
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
            server.search_cache[q] = data
            return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/stream")
async def api_stream(id: str = ""):
    if not id:
        return JSONResponse({"error": "Missing video ID"}, status_code=400)
    if id in server.stream_cache:
        return JSONResponse(server.stream_cache[id])
    try:
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "noplaylist": True,
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={id}", download=False)
            stream_url = info.get("url")
            data = {
                "id": id,
                "title": info.get("title", "Unknown"),
                "channel": info.get("channel") or info.get("uploader") or "Artist",
                "streamUrl": stream_url,
                "thumbnail": info.get("thumbnail") or f"https://i.ytimg.com/vi/{id}/hqdefault.jpg",
                "duration": info.get("duration", 0)
            }
            server.stream_cache[id] = data
            return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/channel_songs")
async def api_channel_songs(channel: str = "tseries", page: int = 1):
    cache_key = f"cs_{channel}_{page}"
    if cache_key in server.channel_songs_cache:
        return JSONResponse(server.channel_songs_cache[cache_key])
    try:
        data = server.fetch_channel_songs(channel, page)
        server.channel_songs_cache[cache_key] = data
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e), "songs": [], "has_next": False}, status_code=500)

@app.get("/api/movies")
async def api_movies(genre: str = "all", page: int = 1):
    cache_key = f"m_{genre}_{page}"
    if cache_key in server.movies_cache:
        return JSONResponse(server.movies_cache[cache_key])
    try:
        data = server.fetch_legal_movies(genre, page)
        server.movies_cache[cache_key] = data
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e), "movies": [], "has_next": False}, status_code=500)

@app.get("/api/movies/detail")
async def api_movies_detail(slug: str = ""):
    if not slug:
        return JSONResponse({"error": "Missing slug"}, status_code=400)
    return JSONResponse({
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
        "overview": "Full-length blockbuster movie legally available in high definition 1080p."
    })

@app.get("/api/subscription/config")
async def api_sub_config():
    return JSONResponse({
        "configured": True,
        "env": "production",
        "payment_link": server.CASHFREE_PAYMENT_LINK,
        "sandbox_url": "https://sandbox.cashfree.com/pg/subscriptions",
        "plan": {
            "id": "soundwave_vip_49",
            "name": "SoundWave VIP",
            "amount": 49.0,
            "currency": "INR",
            "interval": "MONTH"
        }
    })

@app.post("/api/subscription/create")
async def api_sub_create(request: Request):
    return JSONResponse({
        "status": "INITIALIZED",
        "subscription_id": f"SoundWave_SUB_{int(time.time())}",
        "cf_subscription_id": f"cf_{int(time.time())}",
        "subscription_session_id": f"subs_token_{int(time.time())}",
        "auth_link": server.CASHFREE_PAYMENT_LINK,
        "return_url": server.CASHFREE_PAYMENT_LINK,
        "provider": "cashfree",
        "payment_link": server.CASHFREE_PAYMENT_LINK
    })

# Serve root index.html
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Serve any root static asset (app.js, style.css, sw.js, manifest.json)
@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    file_path = os.path.join("static", filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("static/index.html")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
