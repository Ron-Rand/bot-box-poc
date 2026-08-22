import asyncio
import os
import re
import time
import hashlib
from collections import deque
import dns.message

UPSTREAM_DNS = os.getenv('UPSTREAM_DNS', '10.5.0.10')
BORBOX_ENABLED = os.getenv('BORBOX_ENABLED', 'true').lower() == 'true'
UPSTREAM_PORT = 53
LISTEN_PORT = 53

domain_counts = {}
last_reset_time = time.time()
recent_responses = deque(maxlen=20)
pending_queries = {} 

WATER_TORTURE_REGEX = re.compile(r'^[a-zA-Z0-9]{8,}\.[^.]+\.[^.]+\.$')
WHITELIST = ['www.example.com.', 'mail.example.com.', 'target-banking.example.com.']
RESOLVER_CAPACITY = asyncio.Semaphore(20)

async def forward_to_upstream(data, client_addr, client_transport, qname, txid, question_count):
    try:
        await asyncio.wait_for(RESOLVER_CAPACITY.acquire(), timeout=0.5)
    except asyncio.TimeoutError:
        return

    try:
        # THE TUDOOR VULNERABILITY SIMULATION (Always Active)
        if question_count > 1:
            # Flawed pre-processing logic panics: 300ms CPU-draining loop
            await asyncio.sleep(0.300)
        else:
            # Standard resolution time
            await asyncio.sleep(0.015) 
            
        if qname == "target-banking.example.com.":
            await asyncio.sleep(0.100) 
        
        class UpstreamProtocol(asyncio.DatagramProtocol):
            def __init__(self):
                self.transport = None
            def connection_made(self, transport):
                self.transport = transport
                transport.sendto(data)
            def datagram_received(self, response_data, addr):
                if txid in pending_queries:
                    client_transport.sendto(response_data, client_addr)
                    del pending_queries[txid]
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
        RESOLVER_CAPACITY.release()

async def rate_limited_worker(queue):
    while True:
        data, addr, client_transport, qname, txid, question_count = await queue.get()
        try:
            msg = dns.message.from_wire(data)
            is_response = (msg.flags & 0x8000) != 0
        except:
            is_response = False
        
        if not is_response:
            await forward_to_upstream(data, addr, client_transport, qname, txid, question_count)
        queue.task_done()
        await asyncio.sleep(0.1)  

class BorBoxProtocol(asyncio.DatagramProtocol):
    def __init__(self, rate_limited_queue):
        self.rate_limited_queue = rate_limited_queue

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        global domain_counts, last_reset_time, recent_responses, pending_queries
        
        try:
            msg = dns.message.from_wire(data)
            qname = str(msg.question[0].name) if msg.question else ""
            is_response = (msg.flags & 0x8000) != 0
            txid = msg.id
            question_count = len(msg.question)
        except Exception:
            qname = ""
            is_response = False
            txid = None
            question_count = 0

        if not BORBOX_ENABLED:
            if is_response:
                if txid in pending_queries:
                    c_addr, c_trans = pending_queries[txid]
                    c_trans.sendto(data, c_addr)
                    del pending_queries[txid]
                return
            else:
                if txid is not None:
                    pending_queries[txid] = (addr, self.transport)
                asyncio.create_task(forward_to_upstream(data, addr, self.transport, qname, txid, question_count))
                return

        limit = False
        if is_response:
            payload_hash = hashlib.sha256(data[2:]).hexdigest()
            recent_responses.append(payload_hash)
            
            match_count = sum(1 for h in recent_responses if h == payload_hash)
            if match_count >= 5:
                limit = True
                
            if not limit and txid in pending_queries:
                c_addr, c_trans = pending_queries[txid]
                c_trans.sendto(data, c_addr)
                del pending_queries[txid]
        else:
            current_time = time.time()
            if current_time - last_reset_time > 1.0:
                domain_counts.clear()
                last_reset_time = current_time

            domain_counts[qname] = domain_counts.get(qname, 0) + 1

            # NEW: Rule Type 2 - TuDoor Mitigation
            if question_count > 1:
                limit = True
            elif qname in WHITELIST:
                limit = False
            elif bool(WATER_TORTURE_REGEX.match(qname)):
                limit = True
            elif domain_counts[qname] > 10:
                limit = True

            if txid is not None:
                pending_queries[txid] = (addr, self.transport)

        if limit:
            try:
                self.rate_limited_queue.put_nowait((data, addr, self.transport, qname, txid, question_count))
            except asyncio.QueueFull:
                pass
        elif not is_response:
            asyncio.create_task(forward_to_upstream(data, addr, self.transport, qname, txid, question_count))

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
