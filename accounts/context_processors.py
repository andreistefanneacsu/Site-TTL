from lms.models import Users

def current_user(request):
    """Make the logged-in user object available in all templates."""
    user_id = request.session.get('user_id')
    account_type = request.session.get('account_type', '')
    user = None
    if user_id:
        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            pass
    return {
        'current_user': user,
        'account_type': account_type,
    }
