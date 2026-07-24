from gevent import monkey
monkey.patch_all()

import uuid
import random
import string
from locust import HttpUser, task, between
import threading
import time

class StressTestUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Reduced wait time for more aggressive testing
    
    def on_start(self):
        # Initialize session for connection reuse
        self.session_id = str(uuid.uuid4())
        
    @task(5)
    def search_flood(self):
        # Generate complex search queries with random parameters
        queries = [
            f"{''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 50)))}",
            f"ip:{'.'.join(str(random.randint(1, 255)) for _ in range(4))}",
            f"user:{''.join(random.choices(string.ascii_letters, k=random.randint(5, 20)))}",
            f"date:{random.randint(2000, 2023)}-{random.randint(1, 12)}-{random.randint(1, 28)}",
            f"id:{random.randint(100000, 999999999)}"
        ]
        
        # Multiple concurrent search requests
        for _ in range(random.randint(1, 5)):
            q = random.choice(queries)
            self.client.get(
                f"/search?q={q}&nocache={uuid.uuid4().hex}&session={self.session_id}",
                name="GET /search",
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "User-Agent": random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                        "Mozilla/5.0 (X11; Linux x86_64)"
                    ])
                },
                timeout=5
            )
    
    @task(3)
    def heavy_api_bombardment(self):
        # Generate increasingly large payloads
        payload_size = random.randint(5000, 50000)
        payload = {
            "data": "x" * payload_size,
            "metadata": {
                "timestamp": time.time(),
                "session": self.session_id,
                "nested": {
                    "level1": {
                        "level2": {
                            "level3": "y" * random.randint(100, 1000)
                        }
                    }
                }
            },
            "array": ["item" + str(i) for i in range(random.randint(100, 1000))]
        }
        
        # Send multiple concurrent requests
        for _ in range(random.randint(1, 3)):
            self.client.post(
                "/api/process",
                name="POST /api/process",
                json=payload,
                timeout=10
            )
    
    @task(2)
    def resource_intensive_requests(self):
        # Request large resources
        self.client.get(
            f"/api/export?format=json&size=large&session={self.session_id}",
            name="GET /api/export",
            timeout=15
        )
        
        # Request multiple images simultaneously
        for _ in range(random.randint(1, 5)):
            self.client.get(
                f"/images/{random.randint(1, 10000)}.jpg",
                name="GET /images",
                timeout=5
            )
    
    @task(1)
    def connection_exhaustion(self):
        # Open multiple connections without properly closing them
        for _ in range(random.randint(5, 20)):
            try:
                self.client.get(
                    "/api/long-polling",
                    name="GET /api/long-polling",
                    timeout=30,
                    params={"session": self.session_id, "timeout": 25}
                )
            except:
                pass  # Ignore timeouts
