"""
Loads environment variables from .env into the process environment.
Import this before anything that needs those variables (e.g. shared/ai_client.py).
"""

from dotenv import load_dotenv

load_dotenv()
