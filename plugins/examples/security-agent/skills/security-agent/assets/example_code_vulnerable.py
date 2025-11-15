#!/usr/bin/env python3

"""
Example code snippets demonstrating common vulnerabilities.

This module provides examples of vulnerable code that can be used for
security testing and education. It includes examples of:

- SQL Injection
- Cross-Site Scripting (XSS)
- Path Traversal
- Command Injection
- Buffer Overflow (simulated in Python)
- Insecure Deserialization
"""

import os
import subprocess
import pickle
import base64
import sys

def sql_injection_example(user_input):
    """
    Demonstrates a simple SQL injection vulnerability.

    Args:
        user_input (str):  A string that could be malicious.

    Returns:
        str: A dummy SQL query string.
    """
    try:
        query = "SELECT * FROM users WHERE username = '" + user_input + "'"
        # In a real application, this query would be executed against a database.
        print(f"Generated query: {query}")  # For demonstration purposes only
        return query
    except Exception as e:
        print(f"Error in sql_injection_example: {e}")
        return None


def xss_example(user_input):
    """
    Demonstrates a simple XSS vulnerability.

    Args:
        user_input (str): A string that could contain malicious JavaScript.

    Returns:
        str: The potentially vulnerable HTML output.
    """
    try:
        output = "<h1>Welcome, " + user_input + "!</h1>"
        # In a real application, this output would be rendered in a web page.
        print(f"Generated HTML: {output}") # For demonstration purposes only
        return output
    except Exception as e:
        print(f"Error in xss_example: {e}")
        return None


def path_traversal_example(filename):
    """
    Demonstrates a path traversal vulnerability.

    Args:
        filename (str): A filename provided by the user.

    Returns:
        str: The contents of the file (if accessible).  Returns None on error.
    """
    try:
        # Vulnerable to path traversal: user can use "../" to access other files.
        filepath = os.path.join("data", filename)
        with open(filepath, "r") as f:
            content = f.read()
            print(f"File content (if accessible): {content}")
            return content
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except Exception as e:
        print(f"Error in path_traversal_example: {e}")
        return None


def command_injection_example(user_input):
    """
    Demonstrates a command injection vulnerability.

    Args:
        user_input (str): A string that could contain malicious commands.

    Returns:
        str: The output of the executed command (if any). Returns None on error.
    """
    try:
        # Vulnerable to command injection: user can inject shell commands.
        command = "echo " + user_input
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout
        print(f"Command output: {output}")
        return output
    except Exception as e:
        print(f"Error in command_injection_example: {e}")
        return None


def buffer_overflow_example(data, buffer_size):
    """
    Simulates a buffer overflow vulnerability in Python.

    Python is generally memory-safe, so this is a simplified simulation.

    Args:
        data (str): The data to write to the buffer.
        buffer_size (int): The size of the buffer.
    """
    try:
        buffer = bytearray(buffer_size)
        if len(data.encode('utf-8')) > buffer_size:
            print("Simulating Buffer Overflow: Data exceeds buffer size.")
            # Normally this would overwrite adjacent memory, but in Python,
            # this will raise an IndexError. We avoid the error by truncating.
            buffer[:] = data.encode('utf-8')[:buffer_size]  # Truncate to buffer size
        else:
            buffer[:] = data.encode('utf-8')
        print(f"Buffer content: {buffer.decode('utf-8', 'ignore')}")
    except Exception as e:
        print(f"Error in buffer_overflow_example: {e}")


def insecure_deserialization_example(serialized_data):
    """
    Demonstrates an insecure deserialization vulnerability using pickle.

    Args:
        serialized_data (str): A base64 encoded pickled object.

    Returns:
        The deserialized object, or None if an error occurs.
    """
    try:
        # Deserialize the data (potentially dangerous if the data is untrusted)
        decoded_data = base64.b64decode(serialized_data)
        obj = pickle.loads(decoded_data)
        print(f"Deserialized object: {obj}")
        return obj
    except Exception as e:
        print(f"Error in insecure_deserialization_example: {e}")
        return None


if __name__ == "__main__":
    print("Example Vulnerable Code Snippets:")

    print("\nSQL Injection Example:")
    sql_injection_example("'; DROP TABLE users; --")

    print("\nXSS Example:")
    xss_example("<script>alert('XSS Vulnerability!')</script>")

    print("\nPath Traversal Example:")
    # Create a dummy file for the path traversal example.
    if not os.path.exists("data"):
        os.makedirs("data")
    with open("data/test.txt", "w") as f:
        f.write("This is a test file.")

    path_traversal_example("../example_code_vulnerable.py") # Attempt to access this file

    print("\nCommand Injection Example:")
    command_injection_example("&& ls -l")

    print("\nBuffer Overflow Example:")
    buffer_overflow_example("A" * 100, 10)

    print("\nInsecure Deserialization Example:")
    # Create a malicious object and serialize it.
    class MaliciousClass:
        def __reduce__(self):
            return (os.system, ("rm -rf /",))  # DANGEROUS: Never do this in real code!

    malicious_object = MaliciousClass()
    serialized_data = base64.b64encode(pickle.dumps(malicious_object)).decode('utf-8')
    print(f"Serialized data: {serialized_data}")
    # WARNING: Deserializing this will execute the 'rm -rf /' command (if permitted)
    # This line is commented out for safety.  UNCOMMENT AT YOUR OWN RISK AND ONLY IN A SAFE ENVIRONMENT.
    # insecure_deserialization_example(serialized_data)

    print("\nNote: Some examples are commented out for safety. Exercise caution when running these examples.")