import logging
import pykka
import subprocess
import os
import time
import json
import threading
from pathlib import Path

from mopidy.models import Album, Artist, Track, TlTrack
from mopidy.types import PlaybackState, DurationMs
from mopidy.core.listener import CoreListener

logger = logging.getLogger(__name__)


class SpotifyRenderFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self._config = config
        self.core = core
        self.running = True
        self.last_event = ""
        self.uri= ""
        self.track = None
        self.timer = None
        self.timer_running = True
        self.timer_paused = False
        self.elapsed_timer_count = 0

    def start_librespot(self):
        self.end_librespot()  # Ensure no duplicate process
        librespot_path = Path(__file__).parent / "librespot"
        on_event_path = Path(__file__).parent / "on_event.sh"

        cmd = [
                librespot_path,
                "--bitrate", self._config["spotify-render"]["bitrate"],
                "--format", self._config["spotify-render"]["format"],
                "--name", self._config["spotify-render"]["name"],
                "--cache", "/tmp/spotify_cache",
                "--disable-audio-cache",
                "--backend", self._config["spotify-render"]["backend"],
                "--onevent", on_event_path,
                "--initial-volume", self._config["spotify-render"]["initial-volume"],
                "--device-type", self._config["spotify-render"]["device-type"],
                "--device", self._config["spotify-render"]["device"]
            ]  
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def end_librespot(self):
        logger.info("Spotify renderer: Stopped")
        subprocess.Popen(["killall","-s9", "librespot"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    

    # Elpased Time Timer
    def pause_timer(self):
        self.timer_paused = True

    def resume_timer(self):
        self.timer_paused = False

    def stop_timer(self):
        self.timer_running = False
        self.timer_paused = False
        self.elapsed_timer_count = 0
        if self.timer and self.timer.is_alive():
            self.timer.join()
        self.timer = None

    def start_timer(self):
        self.timer_running = True
        self.timer_paused = False
        self.elapsed_timer_count = 0
        self.timer = threading.Thread(target=self.elapsed_timer, daemon=True)
        self.timer.start()

    def elapsed_timer(self):
        while self.timer_running:
            if not self.timer_paused:
                self.elapsed_timer_count += 1
                self.core.playback.set_position(DurationMs(self.elapsed_timer_count * 1000))
                time.sleep(1) 
            else:
                time.sleep(0.1)

    def on_event(self, event, **kwargs):
        """Handle Mopidy events"""
    

    def on_start(self):
        threading.Thread(target=self.start_librespot, daemon=True).start()
        threading.Thread(target=self.handle_on_events, daemon=True).start()
        logger.info("Spotify renderer: Initialized")


    def handle_on_events(self):
        EVENT_FILE = "/tmp/librespot_event.json"
        while self.running:
            try:
                if not os.path.exists(EVENT_FILE):
                    continue
                if os.path.getsize(EVENT_FILE) == 0:
                    continue

                with open(EVENT_FILE, "r") as file:
                    content = file.read().strip()
                    if not content: 
                        continue
                    try:
                        event = json.loads(content)  
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON: {e}")
                        continue
                    
                    
                    if "player_event" in event and event["player_event"] != self.last_event:
                        self.last_event = event["player_event"]

                        if event["player_event"] == 'session_connected':
                            self.core.playback.stop()
                            self.core.playback.set_metadata(None)
                            CoreListener.send("options_changed", source='spotify-connect', state={'connected': True})
                            logger.info("Spotify renderer: Connected")

                        if event["player_event"] == 'session_disconnected':
                            self.core.playback.stop()
                            self.core.playback.set_metadata(None)
                            self.core.playback.set_position(DurationMs(int(0)))
                            self.stop_timer()
                            CoreListener.send("options_changed", source='spotify-connect', state={'connected': False})
                            logger.info("Spotify renderer: Disconnected")

                        if event["player_event"] in ('seeked', 'position_correction', 'playing'):
                            self.core.playback.set_state(PlaybackState.PLAYING)
                            self.core.playback.set_position(DurationMs(int(event["position_ms"])))
                            self.elapsed_timer_count = int(event["position_ms"]) / 1000

                        if event["player_event"] == 'playing':
                            self.resume_timer()
                        
                        if event["player_event"] == 'paused':
                            self.core.playback.set_state(PlaybackState.PAUSED)
                            self.core.playback.set_position(DurationMs(int(event["position_ms"])))
                            self.pause_timer()

                        if event["player_event"] == 'track_changed':

                            if self.track is not None:
                                CoreListener.send("track_playback_ended", tl_track=self.track)
                                self.stop_timer()

                            track_id = int(event["number"])
                            track = Track(
                                uri = event["uri"],
                                name = event["name"],
                                artists = frozenset(Artist(name=name) for name in event["artists"] if name),
                                album = Album(name = event["album"]),
                                composers=frozenset(),
                                performers=frozenset(),
                                track_no = int(event["number"]) or None,
                                disc_no = int(event["disc_number"]) or None,
                                length = int(event["duration_ms"]),  
                                bitrate= int(self._config["spotify-render"]["bitrate"]) * 1000,  
                                comment=event["description"] or None,
                            )
                            

                            tl_track = TlTrack(track_id, track=track)
                            self.track = tl_track
                            self.core.playback.set_metadata(tl_track)
                            CoreListener.send("track_playback_started", tl_track=tl_track)
                            self.stop_timer()
                            self.start_timer()
                            self.uri = event["uri"]

            except Exception as e:
                print(f"Unexpected error: {e}")


    def on_stop(self):
        self.running = False
        self.end_librespot()
