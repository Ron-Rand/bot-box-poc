import asyncio
import os
import re
import time
import dns.message

UPSTREAM_DNS = os.getenv('UPSTREAM_DNS', '10.5.0.10')
BORBOX_ENABLED = os.getenv('BORBOX_ENABLED', 'true').lower() == 'true'
UPSTREAM_PORT = 53
LISTEN_PORT = 53

domain_counts = {}
last_reset_time = time.time()

# Slide 11: Water Torture Regex
WATER_TORTURE_REGEX = re.compile(r'^[a-zA-Z0-9]{8,}\.[^.]+\.[^.]+\.$')
WHITELIST = ['www.example.com.', 'mail.example.com.']

# Simulate a resolver that can only process 20 queries concurrently
# This applies to ALL attacks (QPS Flood, Cache Poison, Water Torture)
RESOLVER_CAPACITY = asyncio.Semaphore(20)

async def forward_to_upstream(data, client_addr, client_transport):
    # Try to acquire a processing slot in the upstream resolver
    try:
        # If we wait longer than 0.5s for a free slot, the client has already timed out
        await asyncio.wait_for(RESOLVER_CAPACITY.acquire(), timeout=0.5)
    except asyncio.TimeoutError:
        # Resolver is completely overwhelmed (Resource Exhaustion) - Packet dropped
        return

    try:
        # Simulate the base time it takes a resolver to parse and process ANY packet
        await asyncio.sleep(0.015) 
        
        class UpstreamProtocol(asyncio.DatagramProtocol):
            def __init__(self):
                self.transport = None
            def connection_made(self, transport):
                self.transport = transport
                transport.sendto(data)
            def datagram_received(self, response_data, addr):
                client_transport.sendto(response_data, client_addr)
                self.transport.close()
            def error_received(self, exc):
                pass
                
        loop = asyncio.get_running_loop()
        try:
            await loop.create_datagram_endpoint(
                lambda: UpstreamProtocol(),
                remote_addr=(UPSTREAM_DNS, UPSTREAM_PORT)
            )
        except Exception:
            pass
    finally:
        # Always release the slot when done
        RESOLVER_CAPACITY.release()

async def rate_limited_worker(queue):
    while True:
        data, addr, client_transport = await queue.get()
        await forward_to_upstream(data, addr, client_transport)
        queue.task_done()
        await asyncio.sleep(0.1)  # Strict rate limit: 10 QPS max for all flagged traffic

class BorBoxProtocol(asyncio.DatagramProtocol):
    def __init__(self, rate_limited_queue):
        self.rate_limited_queue = rate_limited_queue

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        global domain_counts, last_reset_time
        
        if not BORBOX_ENABLED:
            # Passthrough Mode: Attacker instantly consumes all 20 RESOLVER_CAPACITY slots
            asyncio.create_task(forward_to_upstream(data, addr, self.transport))
            return

        try:
            msg = dns.message.from_wire(data)
            qname = str(msg.question[0].name)
        except Exception:
            qname = ""

        current_time = time.time()
        if current_time - last_reset_time > 1.0:
            domain_counts.clear()
            last_reset_time = current_time

        domain_counts[qname] = domain_counts.get(qname, 0) + 1
        limit = False

        if bool(WATER_TORTURE_REGEX.match(qname)):
            limit = True
        elif qname in WHITELIST:
            limit = False
        elif domain_counts[qname] > 10:
            limit = True

        if limit:
            try:
                self.rate_limited_queue.put_nowait((data, addr, self.transport))
            except asyncio.QueueFull:
                pass
        else:
            # High-priority queue (direct fast-path)
            asyncio.create_task(forward_to_upstream(data, addr, self.transport))

async def main():
    loop = asyncio.get_running_loop()
    rate_limited_queue = asyncio.Queue(maxsize=10000)
    asyncio.create_task(rate_limited_worker(rate_limited_queue))

    transport, _ = await loop.create_datagram_endpoint(
        lambda: BorBoxProtocol(rate_limited_queue),
        local_addr=('0.0.0.0', LISTEN_PORT)
    )

    try:
        await asyncio.sleep(36000)
    finally:
        transport.close()

if __name__ == '__main__':
    asyncio.run(main())
