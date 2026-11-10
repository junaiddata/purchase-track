from django.db import migrations

# Brands (ManufacturerName in the Alabama stock API) approved for the first Alabama rollout.
# More can be added later in the Django admin (Alabama brands) without any code change.
ALABAMA_BRANDS = [
    'AQUAVERA', 'ARISTON - BELGIUM', 'ARISTON - CHINA', 'ARISTON - ITALY', 'ARISTON-SOLAR',
    'FERROLI', 'FRESH', 'GF-HP', 'GF-UPVC', 'GROHE', 'HARDWARE', 'HOME CREATOR', 'JOFLEX',
    'JOMIX', 'JOMIX-PUMP', 'JOMIX-PVC', 'JOMIX-SANITARYWARE', 'JOMIX-VALVE', 'KLUDI',
    'LAMBORGINI', 'PPP', 'RAKTHERM', 'RAKTHERM ELECTRICAL DUCT', 'RAKTHERM PVC',
    'VERA SOLAR', 'VERA-CHINA', 'VERA-INDIA', 'VG/HC',
]


def seed(apps, schema_editor):
    AlabamaBrand = apps.get_model('tracking', 'AlabamaBrand')
    for name in ALABAMA_BRANDS:
        AlabamaBrand.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    AlabamaBrand = apps.get_model('tracking', 'AlabamaBrand')
    AlabamaBrand.objects.filter(name__in=ALABAMA_BRANDS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0018_alabama_tables'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
