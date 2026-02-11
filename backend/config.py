"""
Backend configuration
"""
import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Supabase Cloud
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

    # Clerk
    CLERK_DOMAIN = os.getenv('CLERK_DOMAIN', '')
    CLERK_WEBHOOK_SECRET = os.getenv('CLERK_WEBHOOK_SECRET', '')

    # Credits
    SIGNUP_BONUS_CREDITS = int(os.getenv('SIGNUP_BONUS_CREDITS', '50'))

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
