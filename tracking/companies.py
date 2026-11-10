"""
Company registry.

Junaid is the original app (URLs without a prefix).  Alabama is served from the same views under the
/alabama/ URL prefix, but reads and writes its OWN tables (see models.py), so the two companies' data
can never mix.  Views ask `get_company(request)` which model set to use instead of naming
ItemMaster / Quotation / ... directly.
"""
from . import models as m


class Company:
    def __init__(self, key, name, profile_code, Item, Quotation, QuotationItem, Release, Shipment,
                 url_prefix='', pdf_brand='', footer_name='', logo_url='',
                 show_local_columns=True, show_sap_quoted=True, local_purchase_enabled=True, public_apis_enabled=True,
                 import_command='import_stock_api',
                 sap_quoted_url_setting='QUOTATION_TOTALS_API_URL', sap_quoted_key_setting='QUOTATION_API_KEY',
                 sap_quoted_cache_key='sap_quoted_qty_map_v1'):
        self.key = key
        self.name = name
        self.profile_code = profile_code          # value stored in UserProfile.company
        self.Item = Item
        self.Quotation = Quotation
        self.QuotationItem = QuotationItem
        self.Release = Release
        self.Shipment = Shipment
        self.url_prefix = url_prefix              # '' for Junaid, '/alabama' for Alabama
        self.pdf_brand = pdf_brand or name.upper()
        self.footer_name = footer_name or name
        self.logo_url = logo_url
        # Local Open Qty + Import+Local come from a Junaid-only system
        self.show_local_columns = show_local_columns
        # SAP Quoted Qty (Jul-Sep 2026): each company has its own endpoint/key/cache entry
        self.show_sap_quoted = show_sap_quoted
        self.sap_quoted_url_setting = sap_quoted_url_setting
        self.sap_quoted_key_setting = sap_quoted_key_setting
        self.sap_quoted_cache_key = sap_quoted_cache_key
        self.local_purchase_enabled = local_purchase_enabled
        self.public_apis_enabled = public_apis_enabled
        self.import_command = import_command

    def __str__(self):
        return self.name

    # templates use these
    @property
    def is_alabama(self):
        return self.key == 'alabama'


JUNAID = Company(
    key='junaid', name='Junaid', profile_code='JUNAID',
    Item=m.ItemMaster, Quotation=m.Quotation, QuotationItem=m.QuotationItem,
    Release=m.Release, Shipment=m.Shipment,
    url_prefix='', pdf_brand='JUNAID', footer_name='Junaid World',
    logo_url='https://sp-ao.shortpixel.ai/client/to_webp,q_glossy,ret_img,w_422/https://junaidworld.com/wp-content/uploads/2023/09/footer-logo.png.webp',
    show_local_columns=True, show_sap_quoted=True, local_purchase_enabled=True, public_apis_enabled=True,
    import_command='import_stock_api',
)

ALABAMA = Company(
    key='alabama', name='Alabama', profile_code='ALABAMA',
    Item=m.AlabamaItemMaster, Quotation=m.AlabamaQuotation, QuotationItem=m.AlabamaQuotationItem,
    Release=m.AlabamaRelease, Shipment=m.AlabamaShipment,
    url_prefix='/alabama', pdf_brand='ALABAMA', footer_name='Alabama', logo_url='',
    show_local_columns=False, show_sap_quoted=True, local_purchase_enabled=False, public_apis_enabled=False,
    import_command='import_alabama_stock',
    sap_quoted_url_setting='ALABAMA_QUOTATION_TOTALS_API_URL', sap_quoted_key_setting='ALABAMA_QUOTATION_API_KEY',
    sap_quoted_cache_key='sap_quoted_qty_map_v1_alabama',
)

COMPANIES = {c.key: c for c in (JUNAID, ALABAMA)}


def get_company(request):
    """The company this request is for (set by CompanyMiddleware; Junaid if the middleware did not run)."""
    return getattr(request, 'company', JUNAID)


def user_is_admin(user):
    """Same rule as the admin_required decorator: superuser or Admin role."""
    return bool(
        user.is_authenticated and user.is_active and
        (user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'ADMIN'))
    )


def user_company(user):
    """Company a (non-admin) user belongs to. Users without a profile are Junaid users (as before)."""
    profile = getattr(user, 'profile', None)
    code = getattr(profile, 'company', 'JUNAID') if profile else 'JUNAID'
    return ALABAMA if code == 'ALABAMA' else JUNAID
