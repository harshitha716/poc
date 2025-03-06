import os

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")

bind = f"{host}:{port}"
