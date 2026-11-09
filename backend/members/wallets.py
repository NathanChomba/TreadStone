"""Mobile money numbers on a member's account."""

from django.db import transaction

from config.errors import DomainError

from .models import MobileWallet, provider_for


class WalletError(DomainError):
    pass


def ensure_wallet(member):
    """Every member has at least their login phone as a default wallet."""
    if not member.wallets.exists():
        MobileWallet.objects.create(member=member, provider=provider_for(member.phone), number=member.phone, is_default=True)


@transaction.atomic
def add_wallet(member, *, number, provider=None, make_default=False):
    if member.wallets.filter(number=number).exists():
        raise WalletError("That number is already on your account")
    if member.wallets.count() >= 5:
        raise WalletError("You can keep up to 5 numbers")
    first = not member.wallets.exists()
    if make_default or first:
        member.wallets.update(is_default=False)
    return MobileWallet.objects.create(
        member=member, number=number, provider=provider or provider_for(number), is_default=make_default or first,
    )


@transaction.atomic
def set_default(member, wallet_id):
    wallet = member.wallets.filter(pk=wallet_id).first()
    if wallet is None:
        raise WalletError("That number isn't on your account")
    member.wallets.update(is_default=False)
    wallet.is_default = True
    wallet.save(update_fields=["is_default"])
    return wallet


@transaction.atomic
def remove_wallet(member, wallet_id):
    wallet = member.wallets.filter(pk=wallet_id).first()
    if wallet is None:
        raise WalletError("That number isn't on your account")
    if wallet.is_default:
        raise WalletError("Choose another default number before removing this one")
    wallet.delete()
