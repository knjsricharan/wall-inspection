"""
Supabase client initialisation for AWIS-HM.
Credentials are loaded from environment variables only.
"""

from supabase import create_client, Client
from backend.core.config import get_settings

_client: Client | None = None


def get_supabase_client() -> Client | None:
    """
    Return a Supabase client if credentials are configured.
    Returns None if Supabase credentials are not set.
    This prevents a hard crash when credentials are absent during early development.
    """
    global _client
    if _client is not None:
        return _client

    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_anon_key:
        return None

    _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def check_supabase_connection() -> dict:
    """
    Attempt to verify that Supabase is reachable.
    Returns a status dict with connected bool and optional error message.
    """
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_anon_key:
        return {
            "connected": False,
            "reason": "Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env.",
        }

    try:
        client = get_supabase_client()
        # Minimal connectivity probe: list tables in the public schema.
        # This does not require any custom tables to exist.
        client.table("_awis_probe").select("id").limit(1).execute()
        return {"connected": True, "reason": None}
    except Exception as exc:
        error_msg = str(exc)
        # A "relation does not exist" error still means the connection works.
        if "does not exist" in error_msg or "42P01" in error_msg:
            return {"connected": True, "reason": None}
        return {"connected": False, "reason": error_msg}
