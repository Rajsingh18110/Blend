import asyncio
import urllib.parse
from .security import is_safe_url

class SecureEgressProxy:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)

    async def handle_client(self, reader, writer):
        try:
            req = await reader.readuntil(b'\r\n\r\n')
            lines = req.split(b'\r\n')
            first_line = lines[0].decode('utf-8')
            method, url, _ = first_line.split(' ')

            if method == 'CONNECT':
                host, port = url.split(':')
                is_safe, resolved_ip = is_safe_url(f"https://{host}", resolve_dns=True)
                if not is_safe or not resolved_ip:
                    writer.close()
                    return
                
                # IP Pinning at network layer: connect to resolved_ip
                remote_reader, remote_writer = await asyncio.open_connection(resolved_ip, int(port))
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()

                await asyncio.gather(
                    self.relay(reader, remote_writer),
                    self.relay(remote_reader, writer)
                )
            else:
                writer.close()
        except Exception:
            writer.close()

    async def relay(self, reader, writer):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
