from gevent import monkey
monkey.patch_all()

import uuid
import random
from locust import User, task, between, events
import socket
import time

class UdpSocketClient(socket.socket):
    def __init__(self, af_inet, socket_type):
        super(UdpSocketClient, self).__init__(af_inet, socket_type)
        self._locust_environment = None

    def sendto(self, data, address):
        start_time = time.time()
        try:
            super(UdpSocketClient, self).sendto(data, address)
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="udpsocket", name="sendto", response_time=total_time, response_length=0)
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="udpsocket", name="sendto", response_time=total_time, exception=e)

    def recvfrom(self, bufsize):
        recv_data = b''
        start_time = time.time()
        try:
            recv_data, address = super(UdpSocketClient, self).recvfrom(bufsize)
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="udpsocket", name="recvfrom", response_time=total_time, response_length=0)
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="udpsocket", name="recvfrom", response_time=total_time, exception=e)
        return recv_data, address

class DirectUser(User):
    wait_time = between(0, 0)

    def on_start(self):
        self.client = UdpSocketClient(socket.AF_INET, socket.SOCK_DGRAM)
        self.client._locust_environment = self.environment

    @task(7)
    def search(self):
        q = random.choice([
            "123456789012345678",
            "987654321098765432",
            "user_example",
            "ip:192.168.0.1",
        ])
        data = q.encode('utf-8')
        address = ('target_host', target_port)  # Replace with your target host and port
        self.client.sendto(data, address)

    @task(3)
    def heavy_api(self):
        payload = {"data": "x" * random.randint(1000, 10000)}
        data = str(payload).encode('utf-8')
        address = ('target_host', target_port)  # Replace with your target host and port
        self.client.sendto(data, address)
