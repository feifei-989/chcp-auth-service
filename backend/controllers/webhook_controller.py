"""
Webhook Controller - handles Clerk user events.

Clerk sends POST to /webhooks/clerk when users register/update/delete.
All requests are verified using Svix signature.
"""
import os
import logging
from flask import Blueprint, request, jsonify
from svix.webhooks import Webhook, WebhookVerificationError
from db import get_client

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhook', __name__)

SIGNUP_BONUS_CREDITS = int(os.getenv('SIGNUP_BONUS_CREDITS', '50'))


def _verify_webhook(payload: bytes, headers: dict) -> dict:
    """Verify Clerk webhook signature using Svix."""
    secret = os.getenv('CLERK_WEBHOOK_SECRET', '')
    if not secret:
        raise ValueError("CLERK_WEBHOOK_SECRET 未设置！")

    wh = Webhook(secret)
    svix_headers = {
        'svix-id': headers.get('svix-id', ''),
        'svix-timestamp': headers.get('svix-timestamp', ''),
        'svix-signature': headers.get('svix-signature', ''),
    }
    return wh.verify(payload, svix_headers)


@webhook_bp.route('/webhooks/clerk', methods=['POST'])
def clerk_webhook():
    """Handle Clerk webhook events."""
    payload = request.get_data()
    headers = dict(request.headers)

    try:
        data = _verify_webhook(payload, headers)
    except WebhookVerificationError as e:
        logger.warning(f"Webhook 签名验证失败: {e}")
        return jsonify({'error': 'Invalid signature'}), 401
    except ValueError as e:
        logger.error(str(e))
        return jsonify({'error': str(e)}), 500

    event_type = data.get('type', '')
    event_data = data.get('data', {})
    logger.info(f"Clerk Webhook: {event_type}")

    try:
        if event_type == 'user.created':
            _handle_user_created(event_data)
        elif event_type == 'user.updated':
            _handle_user_updated(event_data)
        elif event_type == 'user.deleted':
            _handle_user_deleted(event_data)
        else:
            logger.info(f"忽略事件: {event_type}")

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"处理 Webhook 失败: {e}", exc_info=True)
        return jsonify({'error': 'Internal error'}), 500


def _extract_email(data: dict) -> str:
    addrs = data.get('email_addresses', [])
    primary_id = data.get('primary_email_address_id')
    for addr in addrs:
        if addr.get('id') == primary_id:
            return addr.get('email_address', '')
    return addrs[0].get('email_address', '') if addrs else ''


def _extract_name(data: dict) -> str:
    first = data.get('first_name', '') or ''
    last = data.get('last_name', '') or ''
    return f"{first} {last}".strip() or None


def _handle_user_created(data: dict):
    """Create user + grant signup bonus credits."""
    clerk_id = data.get('id')
    if not clerk_id:
        return

    supabase = get_client()

    # Idempotency: check if user already exists
    existing = supabase.table('users').select('id').eq('id', clerk_id).execute()
    if existing.data:
        logger.info(f"用户 {clerk_id} 已存在，跳过")
        return

    email = _extract_email(data)
    nickname = _extract_name(data)
    avatar = data.get('image_url', '')

    # Insert user
    supabase.table('users').insert({
        'id': clerk_id,
        'email': email,
        'nickname': nickname,
        'avatar_url': avatar,
        'credits': SIGNUP_BONUS_CREDITS,
    }).execute()

    # Insert signup bonus transaction
    supabase.table('credit_transactions').insert({
        'user_id': clerk_id,
        'amount': SIGNUP_BONUS_CREDITS,
        'balance_after': SIGNUP_BONUS_CREDITS,
        'action': 'signup_bonus',
        'description': f'新用户注册赠送 {SIGNUP_BONUS_CREDITS} 积分',
    }).execute()

    logger.info(f"新用户: {clerk_id} ({email}), 赠送 {SIGNUP_BONUS_CREDITS} 积分")


def _handle_user_updated(data: dict):
    """Update user email/name/avatar."""
    clerk_id = data.get('id')
    if not clerk_id:
        return

    supabase = get_client()

    existing = supabase.table('users').select('id').eq('id', clerk_id).execute()
    if not existing.data:
        _handle_user_created(data)
        return

    update_data = {}
    email = _extract_email(data)
    if email:
        update_data['email'] = email
    nickname = _extract_name(data)
    if nickname:
        update_data['nickname'] = nickname
    avatar = data.get('image_url', '')
    if avatar:
        update_data['avatar_url'] = avatar

    if update_data:
        supabase.table('users').update(update_data).eq('id', clerk_id).execute()

    logger.info(f"更新用户: {clerk_id}")


def _handle_user_deleted(data: dict):
    """Soft-delete user."""
    clerk_id = data.get('id')
    if not clerk_id:
        return

    supabase = get_client()
    supabase.table('users').update({'is_active': False}).eq('id', clerk_id).execute()
    logger.info(f"停用用户: {clerk_id}")
