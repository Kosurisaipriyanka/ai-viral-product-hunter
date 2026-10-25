
"""YouTube Data API connector for product-research signals.

Uses Google's official YouTube Data API; it does not scrape YouTube pages.
"""
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def _normalize_text(value: str) -> str:
    """Normalize text for simple, transparent keyword matching."""
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def score_video_relevance(query: str, title: str, description: str) -> dict:
    """Score title/description keyword overlap; this is a heuristic, not AI."""
    query_terms = set(_normalize_text(query).split())
    title_terms = set(_normalize_text(title).split())
    description_terms = set(_normalize_text(description).split())

    if not query_terms:
        return {"relevance_score": 0, "relevance_label": "LOW"}

    title_overlap = len(query_terms & title_terms) / len(query_terms)
    description_overlap = len(query_terms & description_terms) / len(query_terms)

    # Titles matter more than descriptions because descriptions may contain tags.
    score = round(100 * (0.75 * title_overlap + 0.25 * description_overlap))
    label = "HIGH" if score >= 75 else "MEDIUM" if score >= 40 else "LOW"

    return {"relevance_score": score, "relevance_label": label}


def search_youtube_videos(
    query: str,
    max_results: int = 10,
    region_code: str = "US",
    relevant_only: bool = False,
) -> dict:
    """Search public video metadata and attach stats and relevance indicators."""
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
            if response.status_code == 403:
                message = "YouTube rejected the request. Check that YouTube Data API v3 is enabled, the key is valid, and quota remains."
            elif response.status_code == 400:
                message = "YouTube rejected the search parameters. Check the keyword and region."
            else:
                message = f"YouTube API request failed with HTTP {response.status_code}."
            return {
                "source": "YouTube Data API v3",
                "query": query,
                "count": 0,
                "items": [],
                "error": message,
            }

        search_data = response.json()
        videos = []
        ids = []

        for item in search_data.get("items", []):
            video_id = (item.get("id") or {}).get("videoId")
            snippet = item.get("snippet") or {}
            if not video_id:
                continue

            video = {
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
            }
            video.update(
                score_video_relevance(
                    query,
                    video["title"],
                    video["description"],
                )
            )
            videos.append(video)
            ids.append(video_id)

        if ids:
            stats_response = requests.get(
                VIDEOS_URL,
                params={
                    "part": "statistics",
                    "id": ",".join(ids),
                    "key": api_key,
                },
                timeout=20,
            )
            if stats_response.status_code < 400:
                stats_by_id = {
                    item.get("id"): item.get("statistics", {})
                    for item in stats_response.json().get("items", [])
                }
                for video in videos:
                    stats = stats_by_id.get(video["video_id"], {})
                    for field, stat_key in (
                        ("views", "viewCount"),
                        ("likes", "likeCount"),
                        ("comments", "commentCount"),
                    ):
                        value = stats.get(stat_key)
                        video[field] = int(value) if value is not None else None

        if relevant_only:
            videos = [
                video for video in videos
                if video["relevance_label"] in ("HIGH", "MEDIUM")
            ]

        videos.sort(
            key=lambda video: (
                video["relevance_score"],
                video["views"] or 0,
            ),
            reverse=True,
        )

        return {
            "source": "YouTube Data API v3",
            "query": query,
            "region_code": region_code,
            "count": len(videos),
            "items": videos,
            "note": (
                "Videos include a simple keyword-overlap relevance heuristic. "
                "It may miss synonyms or include misleading matches; inspect titles "
                "and channels. View counts are discovery signals, not proof of sales."
            ),
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
