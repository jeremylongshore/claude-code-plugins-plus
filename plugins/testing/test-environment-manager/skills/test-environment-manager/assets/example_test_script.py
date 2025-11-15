#!/usr/bin/env python3

"""
Example Python test script that uses the test environment.

This script demonstrates how to interact with services running in the test environment,
managed by the test-environment-manager plugin.

It assumes that services like a database or message queue are running within Docker containers.
"""

import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def connect_to_database(host, port, user, password, database):
    """
    Attempts to connect to the database.

    Args:
        host (str): Database host.
        port (int): Database port.
        user (str): Database user.
        password (str): Database password.
        database (str): Database name.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        import psycopg2  # Example: PostgreSQL
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)
        conn.close()
        logging.info("Successfully connected to the database.")
        return True
    except ImportError:
        logging.error("psycopg2 (PostgreSQL driver) is not installed. Please install it: pip install psycopg2-binary")
        return False
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return False


def send_message(queue_host, queue_port, message):
    """
    Sends a message to a message queue.

    Args:
        queue_host (str): Message queue host.
        queue_port (int): Message queue port.
        message (str): Message to send.

    Returns:
        bool: True if message sent successfully, False otherwise.
    """
    try:
        import redis  # Example: Redis
        r = redis.Redis(host=queue_host, port=queue_port)
        r.publish('test_channel', message)
        logging.info(f"Successfully sent message to the queue: {message}")
        return True
    except ImportError:
        logging.error("redis is not installed. Please install it: pip install redis")
        return False
    except Exception as e:
        logging.error(f"Failed to send message to the queue: {e}")
        return False


def main():
    """
    Main function to demonstrate test environment interaction.
    """
    database_host = os.environ.get("DATABASE_HOST", "localhost")
    database_port = int(os.environ.get("DATABASE_PORT", "5432"))
    database_user = os.environ.get("DATABASE_USER", "test_user")
    database_password = os.environ.get("DATABASE_PASSWORD", "test_password")
    database_name = os.environ.get("DATABASE_NAME", "test_db")

    queue_host = os.environ.get("QUEUE_HOST", "localhost")
    queue_port = int(os.environ.get("QUEUE_PORT", "6379"))

    # Example usage:
    if connect_to_database(database_host, database_port, database_user, database_password, database_name):
        logging.info("Database connection test passed.")
    else:
        logging.error("Database connection test failed.")

    if send_message(queue_host, queue_port, "Hello from the test environment!"):
        logging.info("Message queue test passed.")
    else:
        logging.error("Message queue test failed.")


if __name__ == "__main__":
    main()