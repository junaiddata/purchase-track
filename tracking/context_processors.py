from .companies import ALABAMA, JUNAID, get_company, user_is_admin


def company(request):
    """Makes the active company available to every template as `company`.

    `company_switch` is set only for admins (the only users who can open both companies): the link to the
    other company's home page.
    """
    c = get_company(request)
    ctx = {'company': c}
    user = getattr(request, 'user', None)
    if user is not None and user_is_admin(user):
        other = JUNAID if c is ALABAMA else ALABAMA
        root = getattr(request, 'junaid_root', '/') if other is JUNAID else getattr(request, 'alabama_root', '/alabama/')
        ctx['company_switch'] = {'name': other.name, 'url': root}
    return ctx
