#!/usr/bin/python
import asyncio
import sys

async def tcp_echo_client(message):
    host = "::1"
    port = 15555
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2.0)
    except asyncio.TimeoutError:
        print('Failed to connect')
        sys.exit(1)

    writer.write(message.encode())
    await writer.drain()
    data = await reader.read(1024)
    print(f'Received: {data.decode()!r}')
    writer.close()
    await writer.wait_closed()

asyncio.run(tcp_echo_client('conf_gen workspaces\n'))
