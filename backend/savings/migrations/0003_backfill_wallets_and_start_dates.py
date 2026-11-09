"""Give existing members a default wallet and existing active groups a start date."""

from django.db import migrations

PREFIX_PROVIDER = {"96": "MTN", "76": "MTN", "97": "AIRTEL", "77": "AIRTEL", "95": "ZAMTEL"}


def forwards(apps, schema_editor):
    Member = apps.get_model("members", "Member")
    MobileWallet = apps.get_model("members", "MobileWallet")
    SavingsGroup = apps.get_model("savings", "SavingsGroup")

    for m in Member.objects.all():
        if not MobileWallet.objects.filter(member=m).exists():
            provider = PREFIX_PROVIDER.get(m.phone[4:6], "MTN") if m.phone.startswith("+260") else "MTN"
            MobileWallet.objects.create(member=m, provider=provider, number=m.phone, is_default=True)

    for g in SavingsGroup.objects.filter(started_at__isnull=True).exclude(status="OPEN"):
        g.started_at = g.created_at.date()
        g.save(update_fields=["started_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0002_contribution_provider_contribution_reference_and_more"),
        ("members", "0002_member_language_member_price_alerts_and_more"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
