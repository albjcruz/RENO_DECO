import time
import asyncio
import requests
requests.packages.urllib3.disable_warnings()

async def _read_and_log_response(reader):
    buffer_size = 1024
    data = await reader.read(buffer_size)
    return data

async def log_and_forward_response(reader, writer):
    data = await _read_and_log_response(reader)
    writer.write(data)
    await writer.drain()
    if(len(data) == 244):
        try:
            requests.post('http://200.126.14.228:5000/api/data', data=data, verify=False)
            print("data enviada")
            time.sleep(10)
        except Exception as e:
            print(str(e))
            time.sleep(10)

async def handle_inverter_message(inverter_reader, inverter_writer):
    server_reader, server_writer = await asyncio.open_connection('47.88.8.200', 10000)
    await log_and_forward_response(inverter_reader, server_writer)
    await log_and_forward_response(server_reader, inverter_writer)
    server_writer.close()
    inverter_writer.close()

async def main():
    server = await asyncio.start_server(handle_inverter_message, '192.168.0.10', 9999)
    print(f"serving on {server.sockets[0].getsockname()}")
    async with server:
        await server.serve_forever()

asyncio.run(main())