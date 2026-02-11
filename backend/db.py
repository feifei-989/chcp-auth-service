"""
Supabase Client - single shared instance for database operations.

Supabase Cloud provides:
- SUPABASE_URL: your project's API endpoint
- SUPABASE_KEY: service_role key for server-side access

Tables needed in Supabase (create via Dashboard → SQL Editor):

CREATE TABLE users (
    id TEXT PRIMARY KEY,             -- Clerk User ID
    email TEXT UNIQUE NOT NULL,
    nickname TEXT,
    avatar_url TEXT,
    credits INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
"""
import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Client = None


def get_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_KEY', '')

    if not url or not key:
        raise ValueError("SUPABASE_URL 和 SUPABASE_KEY 环境变量未设置！")

    _client = create_client(url, key)
    logger.info(f"Supabase client initialized: {url}")
    return _client
