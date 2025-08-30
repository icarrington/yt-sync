from __future__ import annotations
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .state import RoomState, now_mono
from .playlist import fetch_playlist

ROOMS: dict[str, dict] = {}  # room_id -> {"state": RoomState, "clients": set}

def get_room(room_id: str):
    if room_id not in ROOMS:
        ROOMS[room_id] = {"state": RoomState(), "clients": set()}
    return ROOMS[room_id]

class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group = f"room_{self.room_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        room = get_room(self.room_id)
        room["clients"].add(self.channel_name)
        await self.send_json({"type":"STATE","data": room["state"].__dict__})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)
        room = get_room(self.room_id)
        room["clients"].discard(self.channel_name)
        if not room["clients"]:
            ROOMS.pop(self.room_id, None)

    async def receive_json(self, msg, **kwargs):
        mtype = msg.get("type")
        room = get_room(self.room_id)
        st: RoomState = room["state"]

        if mtype == "SET_PLAYLIST":
            pid, given = msg.get("playlist_id"), msg.get("playlist")
            if pid and not given:
                st.playlist_id, st.playlist = pid, await fetch_playlist(pid)
            else:
                st.playlist_id, st.playlist = pid, (given or [])
            st.index = 0; st.is_playing = False; st.seek_offset = 0.0; st.play_start_server_time = None
            await self._broadcast("STATE", st.__dict__)

        elif mtype == "PLAY":
            st.is_playing = True; st.play_start_server_time = now_mono()
            await self._broadcast("PLAY", {
                "index": st.index, "seek_offset": st.seek_offset,
                "play_start_server_time": st.play_start_server_time
            })

        elif mtype == "PAUSE":
            if st.is_playing and st.play_start_server_time is not None:
                st.seek_offset += now_mono() - st.play_start_server_time
            st.is_playing = False; st.play_start_server_time = None
            await self._broadcast("PAUSE", {"seek_offset": st.seek_offset})

        elif mtype == "SEEK":
            st.seek_offset = max(0.0, float(msg.get("seconds", 0)))
            if st.is_playing: st.play_start_server_time = now_mono()
            await self._broadcast("SEEK", {
                "seek_offset": st.seek_offset,
                "play_start_server_time": st.play_start_server_time
            })

        elif mtype == "NEXT":
            if st.index < max(0, len(st.playlist) - 1): st.index += 1
            st.seek_offset = 0.0; st.play_start_server_time = now_mono() if st.is_playing else None
            await self._broadcast("STATE", st.__dict__)

        elif mtype == "PREV":
            if st.index > 0: st.index -= 1
            st.seek_offset = 0.0; st.play_start_server_time = now_mono() if st.is_playing else None
            await self._broadcast("STATE", st.__dict__)

        elif mtype == "PING":
            await self.send_json({"type":"PONG","data":{"server_time": now_mono()}})

    async def _broadcast(self, msg_type: str, data: dict):
        await self.channel_layer.group_send(self.group, {"type":"_fanout","msg_type":msg_type,"data":data})

    async def _fanout(self, event):
        await self.send_json({"type": event["msg_type"], "data": event["data"]})
