from django.shortcuts import redirect
from django.http import HttpResponseForbidden

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
