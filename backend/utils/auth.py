"""
Authentication middleware - verifies Clerk JWT tokens on protected routes.

Usage:
    from utils.auth import require_auth

    @app.route('/api/protected')
    @require_auth
    def protected_route():
        user_id = request.user_id
        ...
"""
import os
import logging
from functools import wraps
from flask import request
import jwt

logger = logging.getLogger(__name__)

_jwks_client = None


def _get_jwks_client():
    """Lazy-initialize the JWKS client using Clerk's public key endpoint."""
    global _jwks_client

    if _jwks_client is not None:
        return _jwks_client

    clerk_domain = os.getenv('CLERK_DOMAIN', '')
    if not clerk_domain:
        logger.error("CLERK_DOMAIN 环境变量未设置！")
        return None

    if not clerk_domain.startswith('http'):
        clerk_domain = f'https://{clerk_domain}'

    jwks_uri = f'{clerk_domain}/.well-known/jwks.json'
    _jwks_client = jwt.PyJWKClient(jwks_uri)
    logger.info(f"Clerk JWKS client initialized: {jwks_uri}")
    return _jwks_client


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT token.

    Returns:
        Decoded token payload (sub = user_id, etc.)
    """
    client = _get_jwks_client()
    if client is None:
        raise ValueError("Clerk JWKS client not initialized. Check CLERK_DOMAIN.")

    signing_key = client.get_signing_key_from_jwt(token)

    decoded = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_exp": True, "verify_aud": False},
    )
    return decoded


def require_auth(f):
    """
    Decorator to protect API routes with Clerk authentication.
    Injects request.user_id and request.user_email.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': '未登录'}}, 401

        token = auth_header.split('Bearer ', 1)[1].strip()
        if not token:
            return {'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Token 为空'}}, 401

        try:
            payload = verify_clerk_token(token)
            request.user_id = payload.get('sub')
            request.user_email = payload.get('email', '')

            if not request.user_id:
                return {'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Token 缺少用户 ID'}}, 401

        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': {'code': 'TOKEN_EXPIRED', 'message': 'Token 已过期'}}, 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return {'success': False, 'error': {'code': 'INVALID_TOKEN', 'message': 'Token 无效'}}, 401
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return {'success': False, 'error': {'code': 'AUTH_ERROR', 'message': '验证失败'}}, 401

        return f(*args, **kwargs)
    return decorated
