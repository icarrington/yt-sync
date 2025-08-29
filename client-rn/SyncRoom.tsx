import React, { useEffect, useRef, useState, useCallback } from "react";
import { View, Text, Button, TextInput, StyleSheet, Platform } from "react-native";
import YoutubePlayer, { YoutubeIframeRef } from "react-native-youtube-iframe";

type PlaylistItem = { videoId: string; title: string };
type State = {
  playlist_id?: string | null;
  playlist: PlaylistItem[];
  index: number;
  is_playing: boolean;
  play_start_server_time?: number | null;
  seek_offset: number;
};

export default function SyncRoom() {
  const [wsUrl, setWsUrl] = useState("ws://10.0.2.2:8000/ws/demo-room"); // Android emulator loops to host
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<State | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const ref = useRef<YoutubeIframeRef>(null);

  const send = (obj: any) => ws.current?.send(JSON.stringify(obj));

  const connect = () => {
    ws.current = new WebSocket(wsUrl);
    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);
    ws.current.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "STATE") {
        setState(msg.data);
        cueCurrent(msg.data);
        if (!msg.data.is_playing) ref.current?.pauseVideo();
      } else if (msg.type === "PLAY") {
        const { index, seek_offset } = msg.data;
        setState((s) => s ? {...s, index, is_playing:true} : s);
        cueIndex(index);
        ref.current?.seekTo(seek_offset, true);
        ref.current?.playVideo();
      } else if (msg.type === "PAUSE") {
        setState((s) => s ? {...s, is_playing:false, seek_offset: msg.data.seek_offset} : s);
        ref.current?.pauseVideo();
        ref.current?.seekTo(msg.data.seek_offset, true);
      } else if (msg.type === "SEEK") {
        const { seek_offset, play_start_server_time } = msg.data;
        setState((s) => s ? {...s, seek_offset, play_start_server_time} : s);
        ref.current?.seekTo(seek_offset, true);
        if (play_start_server_time != null) ref.current?.playVideo();
      }
    };
  };

  const cueIndex = (i: number) => {
    const v = state?.playlist?.[i];
    if (v) ref.current?.cueVideo(v.videoId);
  };
  const cueCurrent = (st: State) => {
    const v = st.playlist?.[st.index];
    if (v) ref.current?.cueVideo(v.videoId);
  };

  const setDemoPlaylist = () => {
    send({ type: "SET_PLAYLIST", playlist: [
      { videoId: "dQw4w9WgXcQ", title: "Never Gonna Give You Up" },
      { videoId: "9bZkp7q19f0", title: "Gangnam Style" }
    ]});
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>YT Sync – React Native</Text>
      <View style={styles.row}>
        <TextInput style={styles.input} value={wsUrl} onChangeText={setWsUrl} />
        <Button title={connected ? "Connected" : "Connect"} onPress={connect} />
      </View>

      <YoutubePlayer
        ref={ref}
        height={220}
        play={false}
        videoId={"dQw4w9WgXcQ"}
        webViewStyle={{ opacity: 0.99 }} // rendering fix
      />

      <View style={styles.row}>
        <Button title="SET_PLAYLIST" onPress={setDemoPlaylist} />
        <Button title="PLAY" onPress={() => send({type:"PLAY"})} />
        <Button title="PAUSE" onPress={() => send({type:"PAUSE"})} />
        <Button title="PREV" onPress={() => send({type:"PREV"})} />
        <Button title="NEXT" onPress={() => send({type:"NEXT"})} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container:{ flex:1, padding:16, gap:12 },
  title:{ fontSize:18, fontWeight:"600" },
  row:{ flexDirection:"row", gap:8, alignItems:"center", flexWrap:"wrap" },
  input:{ flex:1, borderWidth:1, borderColor:"#ccc", padding:8, borderRadius:6 },
});
