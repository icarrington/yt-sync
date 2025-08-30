from dataclasses import dataclass, field
from typing import List, Optional, TypedDict
import time

def now_mono() -> float:
    return time.monotonic()

class PlaylistItem(TypedDict):
    videoId: str
    title: str

@dataclass
class RoomState:
    playlist_id: Optional[str] = None
    playlist: List[PlaylistItem] = field(default_factory=list)
    index: int = 0
    is_playing: bool = False
    play_start_server_time: Optional[float] = None
    seek_offset: float = 0.0
