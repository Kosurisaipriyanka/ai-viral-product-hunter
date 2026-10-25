"""YouTube Data API connector for product-research signals.

Uses Google's official YouTube Data API; it does not scrape YouTube pages.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def search_youtube_videos(query: str, max_results: int = 10, region_code: str = "US") -> dict:
    """Search public video metadata and attach view/like/comment counts where available."""
    query = query.strip()
    if not query:
        return {
            "source": "YouTube Data API v3",
            "query": query,
            "count": 0,
            "items": [],
            "note": "Enter a keyword to search.",
        }

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return {
            "source": "YouTube Data API v3",
            "query": query,
            "count": 0,
            "items": [],
            "error": "YouTube API key is missing. Add YOUTUBE_API_KEY to your local .env file, then restart the backend.",
            "note": "The API key is read locally and must never be committed to GitHub.",
        }

    max_results = max(1, min(int(max_results), 25))
    region_code = (region_code or "US").upper()
    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": "viewCount",
                "regionCode": region_code,
                "key": api_key,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            # Avoid returning request URLs or raw exception details that may contain the API key.
            if response.status_code == 403:
                message = "YouTube rejected the request. Check that YouTube Data API v3 is enabled, the key is valid, and quota remains."
            elif response.status_code == 400:
                message = "YouTube rejected the search parameters. Check the keyword and region."
            else:
                message = f"YouTube API request failed with HTTP {response.status_code}."
            return {"source": "YouTube Data API v3", "query": query, "count": 0, "items": [], "error": message}
        search_data = response.json()
        videos = []
        ids = []
        for item in search_data.get("items", []):
            video_id = (item.get("id") or {}).get("videoId")
            snippet = item.get("snippet") or {}
            if not video_id:
                continue
            ids.append(video_id)
            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": (snippet.get("thumbnails") or {}).get("medium", {}).get("url", ""),
                "views": None,
                "likes": None,
                "comments": None,
            })

        if ids:
            stats_response = requests.get(
                VIDEOS_URL,
                params={"part": "statistics", "id": ",".join(ids), "key": api_key},
                timeout=20,
            )
            if stats_response.status_code < 400:
                stats_by_id = {
                    item.get("id"): item.get("statistics", {})
                    for item in stats_response.json().get("items", [])
                }
                for video in videos:
                    stats = stats_by_id.get(video["video_id"], {})
                    for field in ("views", "likes", "comments"):
                        stat_key = {"views": "viewCount", "likes": "likeCount", "comments": "commentCount"}[field]
                        value = stats.get(stat_key)
                        video[field] = int(value) if value is not None else None

        return {
            "source": "YouTube Data API v3",
            "query": query,
            "region_code": region_code,
            "count": len(videos),
            "items": videos,
            "note": "Public video metadata and available engagement counts are discovery signals, not proof of product sales, profitability, or future virality. Results are ordered by YouTube view count; use upload date and engagement context when comparing videos.",
        }
    except requests.RequestException:
        return {
            "source": "YouTube Data API v3",
            "query": query,
            "count": 0,
            "items": [],
            "error": "Could not connect to the YouTube API. Check your internet connection and try again.",
        }
    except (ValueError, TypeError):
        return {
            "source": "YouTube Data API v3",
            "query": query,
            "count": 0,
            "items": [],
            "error": "YouTube returned a response the app could not read. Please try again.",
        }
