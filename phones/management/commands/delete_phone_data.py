from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from allauth.socialaccount.models import SocialAccount

from phones.models import InboundContact, RealPhone, RelayNumber


@dataclass
class PhoneData:
    """Holds phone data for a user."""

    fxa: SocialAccount
    real_phone: RealPhone | None = None
    relay_phone: RelayNumber | None = None
    inbound_contact_count: int = 0

    @classmethod
    def from_fxa(cls, fxa_id: str) -> "PhoneData":
        """Initialize from an FxA ID."""
        fxa = SocialAccount.objects.get(provider="fxa", uid=fxa_id)

        try:
            real_phone = RealPhone.objects.get(user=fxa.user)
        except RealPhone.DoesNotExist:
            return cls(fxa=fxa)

        try:
            relay_phone = RelayNumber.objects.get(user=fxa.user)
            inbound_contact_count = InboundContact.objects.filter(
                relay_number=relay_phone
            ).count()
        except RelayNumber.DoesNotExist:
            return cls(fxa=fxa, real_phone=real_phone)

        return cls(
            fxa=fxa,
            real_phone=real_phone,
            relay_phone=relay_phone,
            inbound_contact_count=inbound_contact_count,
        )

    @property
    def has_data(self) -> bool:
        """Return True if the user has phone data to reset."""
        return self.real_phone is not None

    @property
    def real_number(self) -> str | None:
        """Get user's real phone number, if it exists."""
        if self.real_phone:
            return self.real_phone.number
        return None

    @property
    def relay_number(self) -> str | None:
        """Get user's Relay phone mask number, if it exists."""
        if self.relay_phone:
            return self.relay_phone.number
        return None

    def bullet_report(self) -> str:
        """Return a bulleted list of the user's data."""
        return (
            f"* FxA ID: {self.fxa.uid}\n"
            f"* User ID: {self.fxa.user_id}\n"
            f"* Email: {self.fxa.user.email}\n"
            f"* Real Phone: {self.real_number or '<NO REAL PHONE>'}\n"
            f"* Relay Phone: {self.relay_number or '<NO RELAY PHONE>'}\n"
            f"* Inbound Contacts: {self.inbound_contact_count}\n"
        )

    def reset(self) -> None:
        """Reset the user's phone data, so they can re-enroll with new numbers."""
        if self.relay_phone:
            if self.inbound_contact_count:
                InboundContact.objects.filter(relay_number=self.relay_phone).delete()
            self.relay_phone.delete()
        if self.real_phone:
            self.real_phone.delete()


class Command(BaseCommand):
    help = "Deletes phone data, so a user can re-enroll."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("fxa_id", help="The user's FxA ID")
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="Report but do not delete phone data",
        )

    def handle(self, *args: Any, **kwargs: Any) -> None | str:
        fxa_id: str = kwargs["fxa_id"]
        dry_run: bool = kwargs["dry_run"]

        try:
            data = PhoneData.from_fxa(fxa_id)
        except SocialAccount.DoesNotExist:
            raise CommandError(f"No user with FxA ID '{fxa_id}'.")

        report = f"Found a matching user:\n\n{data.bullet_report()}\n"
        self.stdout.write(report)

        if dry_run:
            if data.has_data:
                return "User has phone data to delete."
            return "User has no phone data to delete."

        if data.has_data:
            data.reset()
            return "Deleted user's phone data."
        return "No action taken, since the user has no phone data."
