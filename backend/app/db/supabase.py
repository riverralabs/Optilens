"""Supabase client singleton for backend operations.

Uses the service key for server-side operations (bypasses RLS).
RLS is enforced via org_id filtering in all queries.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Create and cache the Supabase client using the service key."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
