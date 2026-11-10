"""
CompanyMiddleware

* Requests under /alabama/ are served by the same views as Junaid's, but flagged as the Alabama company.
  The prefix is removed before URL resolution and added back to every generated URL (reverse(),
  {% url %}, redirect('name')) through Django's script prefix, so templates and views need no changes.
* Requests without the prefix are Junaid's and behave exactly as before.
* Access rules: admins can open both companies; a non-admin user can only open their own company.
"""
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import get_script_prefix, set_script_prefix

from .companies import ALABAMA, JUNAID, user_company, user_is_admin

PREFIX = ALABAMA.url_prefix            # '/alabama'
# Paths that must never be treated as company pages
_NOT_COMPANY_PATHS = ('/admin/', '/media/')
# Paths an Alabama-only user may open without being redirected to the Alabama area
_SHARED_PATHS = ('/login/', '/logout/', '/admin/', '/media/')


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        base_prefix = get_script_prefix()                   # normally '/'
        request.base_prefix = base_prefix
        request.junaid_root = base_prefix
        request.alabama_root = base_prefix.rstrip('/') + PREFIX + '/'

        path = request.path_info
        company = JUNAID

        if path == PREFIX:                                  # '/alabama' -> '/alabama/'
            return HttpResponseRedirect(request.alabama_root)

        if path.startswith(PREFIX + '/') and not path[len(PREFIX):].startswith(_NOT_COMPANY_PATHS):
            company = ALABAMA
            request.path_info = path[len(PREFIX):]          # resolve the URL without the prefix
            set_script_prefix(request.alabama_root)         # ...and generate URLs with it

        request.company = company

        try:
            denied = self._check_access(request, company)
            if denied is not None:
                return denied
            return self.get_response(request)
        finally:
            set_script_prefix(base_prefix)

    @staticmethod
    def _check_access(request, company):
        user = request.user
        if not user.is_authenticated or user_is_admin(user):
            return None                                     # anonymous -> views ask to log in; admins see both
        own = user_company(user)
        if own is company:
            return None
        if own is ALABAMA and company is JUNAID:
            # An Alabama user landed on a Junaid URL (e.g. right after login): send them to their own area
            if request.method == 'GET' and not request.path_info.startswith(_SHARED_PATHS):
                return HttpResponseRedirect(request.alabama_root + request.get_full_path()[len(request.base_prefix):].lstrip('/'))
            return None if request.path_info.startswith(_SHARED_PATHS) else HttpResponseForbidden('Not allowed for your company.')
        # A Junaid user opened /alabama/...
        if request.path_info.startswith(_SHARED_PATHS):
            return None
        return HttpResponseForbidden('Not allowed for your company.')
