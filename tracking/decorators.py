from django.contrib.auth.decorators import user_passes_test

def admin_required(function=None, redirect_field_name='next', login_url='login'):
    '''
    Decorator for views that checks that the user is logged in and is an ADMIN.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_authenticated and (u.is_superuser or (hasattr(u, 'profile') and u.profile.role == 'ADMIN')),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def sales_required(function=None, redirect_field_name='next', login_url='login'):
    '''
    Decorator for views that checks that the user is logged in and is a SALESMAN (or Admin).
    Admins should generally be able to see everything, or restrict strictly.
    Let's allow Admins to see Sales views too for debugging/oversight.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_authenticated and (u.is_superuser or (hasattr(u, 'profile') and u.profile.role in ['SALESMAN', 'ADMIN'])),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
