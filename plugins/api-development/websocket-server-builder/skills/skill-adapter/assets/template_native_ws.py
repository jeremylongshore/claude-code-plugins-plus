#!/usr/bin/env python3

"""
Template for a basic WebSocket server using native WebSockets.

This script provides a foundation for building real-time bidirectional
communication applications using Python's built-in `websockets` library.
It includes basic connection handling, message reception, and sending.

Example usage:
1. Install the `websockets` library: `pip install websockets`
2. Run the script: `python template_native_ws.py`
3. Connect to the server using a WebSocket client (e.g., a browser-based client).
"""

import asyncio
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


async def handle_client(websocket, path):
    """
    Handles a single WebSocket client connection.

    Args:
        websocket: The WebSocket connection object.
        path: The path requested by the client (unused in this example).
    """
    try:
        logging.info(f"Client connected from {websocket.remote_address}")
        async for message in websocket:
            logging.info(f"Received message: {message}")
            try:
                # Process the message (replace with your application logic)
                response = f"Server received: {message}"
                await websocket.send(response)
                logging.info(f"Sent message: {response}")
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await websocket.send(f"Error: {e}")

    except websockets.exceptions.ConnectionClosedError as e:
        logging.info(f"Client disconnected abruptly: {e}")
    except websockets.exceptions.ConnectionClosedOK as e:
        logging.info(f"Client disconnected gracefully: {e}")
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        logging.info(f"Connection with {websocket.remote_address} closed.")


async def main():
    """
    Starts the WebSocket server.
    """
    try:
        server = await websockets.serve(handle_client, "localhost", 8765)
        logging.info("WebSocket server started on ws://localhost:8765")
        await server.wait_closed()
    except OSError as e:
        logging.error(f"Could not start server: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by keyboard interrupt.")
    except Exception as e:
        logging.error(f"Unhandled exception during server startup: {e}")