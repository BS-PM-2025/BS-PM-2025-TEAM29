from functools import wraps

from django.shortcuts import redirect
from django.http import HttpResponseForbidden
def firebase_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('firebase_uid'):
            return redirect('login')  # Or return JsonResponse if it's an API
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = request.session.get('user_role')
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)
            elif role:
                return HttpResponseForbidden("🚫 Access denied: insufficient permissions.")
            else:
                return redirect('login')
        return wrapper
    return decorator
