def serialize(value):
    """Convert Python data structures to RESP format."""
    if value is None:
        return "$-1\r\n"
    elif isinstance(value, str):
        return f"${len(value)}\r\n{value}\r\n"
    elif isinstance(value, int):
        return f":{value}\r\n"
    elif isinstance(value, list):
        return f"*{len(value)}\r\n" + "".join(serialize(item) for item in value)
    elif isinstance(value, Exception):
        return f"-{value.args[0]}\r\n"
    else:
        raise ValueError("Unsupported type")

def deserialize(message):
    """Parse RESP messages into Python data structures."""
    if not message:
        raise ValueError("Empty message")

    first_char = message[0]
    
    if first_char == "+":
        return message[1:-2]  # Simple String
    elif first_char == "-":
        raise Exception(message[1:-2])  # Error
    elif first_char == ":": 
        return int(message[1:-2])  # Integer
    elif first_char == "$":
        length = int(message[1:message.index("\r\n")])
        if length == -1:
            return None
        start = message.index("\r\n") + 2
        return message[start:start + length]
    elif first_char == "*":
        num_elements = int(message[1:message.index("\r\n")])
        if num_elements == -1:
            return None
        
        # Initialize list to hold parsed elements
        elements = []
        
        rest = message[message.index("\r\n") + 2:]
        for _ in range(num_elements):
            item, rest = deserialize(rest), rest[len(serialize(deserialize(rest))):]
            elements.append(item)
        
        return elements
    else:
        raise ValueError("Invalid RESP message")

