import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from resp import serialize, deserialize

@pytest.mark.parametrize("message, expected", [
    # Bulk String cases
    ("$-1\r\n", None),
    ("$0\r\n\r\n", ""),
    ("$4\r\nping\r\n", "ping"),
    
    # Array cases
    ("*1\r\n$4\r\nping\r\n", ["ping"]),
    ("*2\r\n$4\r\necho\r\n$11\r\nhello world\r\n", ["echo", "hello world"]),
    ("*2\r\n$3\r\nget\r\n$3\r\nkey\r\n", ["get", "key"]),
    
    # Simple Strings
    ("+OK\r\n", "OK"),
    ("+hello world\r\n", "hello world"),
    
    # Errors
    ("-Error message\r\n", Exception("Error message")),
    
    # Integers
    (":1000\r\n", 1000),
    
    # Null Array
    ("*-1\r\n", None)
])
def test_deserialize(message, expected):
    if isinstance(expected, Exception):
        with pytest.raises(Exception) as excinfo:
            deserialize(message)
        assert str(excinfo.value) == str(expected)
    else:
        assert deserialize(message) == expected
