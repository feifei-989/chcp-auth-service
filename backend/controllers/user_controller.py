"""
User Controller - user profile and credit balance APIs.
All endpoints require Clerk authentication.
"""
import logging
from flask import Blueprint, request, jsonify
from utils.auth import require_auth
from db import get_client

logger = logging.getLogger(__name__)
user_bp = Blueprint('user', __name__)


@user_bp.route('/api/user/me', methods=['GET'])
@require_auth
def get_me():
    """Get current user profile + credit balance."""
    supabase = get_client()

    result = supabase.table('users').select('*').eq('id', request.user_id).execute()

    if not result.data:
        # Edge case: user exists in Clerk but webhook was missed
        logger.warning(f"用户 {request.user_id} 不在数据库中，自动创建")
        supabase.table('users').insert({
            'id': request.user_id,
            'email': request.user_email or 'unknown',
            'credits': 0,
        }).execute()
        result = supabase.table('users').select('*').eq('id', request.user_id).execute()

    user = result.data[0]
    return jsonify({'success': True, 'data': user})


@user_bp.route('/api/user/transactions', methods=['GET'])
@require_auth
def get_transactions():
    """Get credit transaction history."""
    limit = request.args.get('limit', 50, type=int)
    supabase = get_client()

    result = supabase.table('credit_transactions') \
        .select('*') \
        .eq('user_id', request.user_id) \
        .order('created_at', desc=True) \
        .limit(limit) \
        .execute()

    return jsonify({
        'success': True,
        'data': {'transactions': result.data}
    })
