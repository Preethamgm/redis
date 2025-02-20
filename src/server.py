import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import asyncio
import socket
import time
import json
from resp import serialize, deserialize

DB_FILE = "dump.rdb"
memory = {}  # Store key-value pairs

# Load database from disk
def load_data():
    global memory
    try:
        with open(DB_FILE, "r") as f:
            raw_data = json.load(f)
            # Convert back into proper types (int, list)
            for key, value in raw_data.items():
                if isinstance(value, str) and value.isdigit():
                    raw_data[key] = int(value)
                elif isinstance(value, list):
                    raw_data[key] = list(value)
        memory = raw_data
        print("Database loaded successfully.")
    except FileNotFoundError:
        print("No previous database found. Starting fresh.")
    except Exception as e:
        print(f"Error loading database: {e}")

# Save database to disk
def save_data():
    try:
        with open(DB_FILE, "w") as f:
            json.dump(memory, f, default=lambda o: o if isinstance(o, (int, list)) else str(o))
        return "+OK\r\n"
    except Exception as e:
        return f"-ERR Failed to save: {str(e)}\r\n"

# Clean up expired keys
def cleanup_expired_keys():
    global memory
    now = time.time()
    keys_to_delete = [key for key, value in memory.items() if isinstance(value, dict) and value["expiry_time"] and value["expiry_time"] < now]
    for key in keys_to_delete:
        del memory[key]

async def handle_client(reader, writer):
    client_info = writer.get_extra_info('peername')
    print(f"Connection started with {client_info}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break  # Close connection if no data
            
            message = data.decode('utf-8')
            print(f"Received: {message}")

            command = deserialize(message)
            print(f"Deserialized command: {command}")

            response = "-ERR unknown command\r\n"
            cleanup_expired_keys()  # Clean expired keys before handling any commands

            # EXISTS
            if command[0] == "EXISTS":
                key = command[1]
                response = f":{1 if key in memory else 0}\r\n"

            # DEL
            elif command[0] == "DEL":
                count = sum(1 for key in command[1:] if memory.pop(key, None) is not None)
                response = f":{count}\r\n"

            # INCR
            elif command[0] == "INCR":
                key = command[1]
                if key in memory and isinstance(memory[key], int):
                    memory[key] += 1
                else:
                    memory[key] = 1
                response = f":{memory[key]}\r\n"

            # DECR
            elif command[0] == "DECR":
                key = command[1]
                if key in memory and isinstance(memory[key], int):
                    memory[key] -= 1
                else:
                    memory[key] = -1
                response = f":{memory[key]}\r\n"

            # LPUSH
            elif command[0] == "LPUSH":
                key, *values = command[1:]
                if key not in memory:
                    memory[key] = []
                elif not isinstance(memory[key], list):
                    response = "-ERR Operation against non-list key\r\n"
                    continue
                memory[key] = list(reversed(values)) + memory[key]
                response = f":{len(memory[key])}\r\n"

            # RPUSH
            elif command[0] == "RPUSH":
                key, *values = command[1:]
                if key not in memory:
                    memory[key] = []
                elif not isinstance(memory[key], list):
                    response = "-ERR Operation against non-list key\r\n"
                    continue
                memory[key].extend(values)
                response = f":{len(memory[key])}\r\n"

            # LRANGE
            elif command[0] == "LRANGE":
                key = command[1]
                start = int(command[2])
                end = int(command[3])

                if key in memory and isinstance(memory[key], list):
                    list_length = len(memory[key])
                    
                    # Handle negative indexing
                    if end < 0:
                        end = list_length + end
                    end = min(end + 1, list_length)  # Redis includes the end index
                    start = max(0, start)

                    result = memory[key][start:end]
                    response = f"*{len(result)}\r\n" + "".join(
                        f"${len(item)}\r\n{item}\r\n" for item in result
                    )
                else:
                    response = "*0\r\n"  # Return empty list if key doesn't exist or isn't a list

            # SAVE
            elif command[0] == "SAVE":
                response = save_data()

            # SET (Modified to handle expiry)
            elif command[0] == "SET":
                key, value = command[1], command[2]
                expiry = None

                if len(command) > 3:
                    if command[3] == "EX":
                        expiry = time.time() + int(command[4])
                    elif command[3] == "PX":
                        expiry = time.time() + int(command[4]) / 1000

                memory[key] = {"value": value, "expiry_time": expiry}
                response = "+OK\r\n"

            # GET (Check expiry)
            elif command[0] == "GET":
                key = command[1]
                if key in memory:
                    item = memory[key]
                    if isinstance(item, dict) and item["expiry_time"] and item["expiry_time"] < time.time():
                        del memory[key]  # Key expired
                        response = "$-1\r\n"
                    else:
                        response = f"${len(item['value'])}\r\n{item['value']}\r\n"
                else:
                    response = "$-1\r\n"

            # TTL
            elif command[0] == "TTL":
                key = command[1]
                if key not in memory:
                    response = ":-2\r\n"  # -2 means key does not exist
                elif isinstance(memory[key], dict) and memory[key]["expiry_time"]:
                    remaining = int(memory[key]["expiry_time"] - time.time())
                    response = f":{remaining if remaining > 0 else -1}\r\n"  # -1 means no expiry
                else:
                    response = ":-1\r\n"

            # EXPIRE
            elif command[0] == "EXPIRE":
                key = command[1]
                ttl = int(command[2])

                if key in memory:
                    if isinstance(memory[key], dict):
                        memory[key]["expiry_time"] = time.time() + ttl
                    else:
                        memory[key] = {"value": memory[key], "expiry_time": time.time() + ttl}
                    response = ":1\r\n"  # 1 means expiry was set
                else:
                    response = ":0\r\n"  # 0 means key does not exist

            # KEYS
            elif command[0] == "KEYS":
                response = f"*{len(memory)}\r\n" + "".join(
                    f"${len(key)}\r\n{key}\r\n" for key in memory
                )

            # FLUSHDB
            elif command[0] == "FLUSHDB":
                memory.clear()
                response = "+OK\r\n"

            print(f"Sending response: {response}")
            writer.write(response.encode('utf-8'))
            await writer.drain()

        writer.close()
        await writer.wait_closed()
        print(f"Connection with {client_info} closed.")

    except Exception as e:
        print(f"Error handling client {client_info}: {e}")

async def start_server():
    load_data()  # Load database at startup
    server = await asyncio.start_server(handle_client, '0.0.0.0', 6380)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(start_server())
