import os, httpx
from typing import List, Dict
YOUTUBE_API = "https://www.googleapis.com/youtube/v3/playlistItems"

async def fetch_playlist(playlist_id: str) -> List[Dict]:
    key = os.getenv("YT_API_KEY")
    if not key:
        return []
    items, token = [], None
    async with httpx.AsyncClient(timeout=20.0) as client:
        while True:
            params = {"part":"snippet,contentDetails", "maxResults":50, "playlistId":playlist_id, "key":key}
            if token: params["pageToken"] = token
            r = await client.get(YOUTUBE_API, params=params)
            r.raise_for_status()
            data = r.json()
            for it in data.get("items", []):
                items.append({"videoId": it["contentDetails"]["videoId"], "title": it["snippet"]["title"]})
            token = data.get("nextPageToken")
            if not token: break
    return items
