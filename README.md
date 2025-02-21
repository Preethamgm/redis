
# Redis Clone - Python Implementation

## Overview

This project aims to implement a basic version of **Redis** from scratch using **Python**. The goal is to build a custom Redis-like database system with basic functionality such as setting and retrieving keys and handling requests through TCP sockets.

## Project Structure

- `src/`: Contains the main implementation files for the custom Redis server.
- `tests/`: Includes test cases to ensure the functionality of the Redis implementation.
- `redis_clone_env/`: Contains any environment-related configurations or dependencies.

## Features

- **TCP Socket**: Handle client-server communication via sockets.
- **Basic Data Storage**: Store and retrieve string data.
- **Commands**: Support basic Redis commands such as `SET`, `GET`, etc.

## Requirements

Make sure to install the following dependencies:

- `pandas`
- `numpy`
- `scikit-learn` (if necessary)

You can install the required libraries using pip:

```bash
pip install <required-libraries>
```

## How to Run

1. Clone the repository to your local machine:

```bash
git clone https://github.com/Preethamgm/redis.git
```

2. Navigate to the project directory:

```bash
cd redis
```

3. Run the Redis server script:

```bash
python3 src/redis_server.py
```

4. Connect to the server using a Redis client or your own custom client implementation.

## Future Work

- **Persistence**: Implement disk-based storage.
- **Security**: Add authentication mechanisms.
- **Advanced Features**: Add more advanced Redis features like pub/sub, data structures, etc.
