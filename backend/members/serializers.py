from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Member, MobileWallet, Notification


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["id", "phone", "first_name", "last_name", "email", "nrc_number", "kyc_status", "is_staff",
                  "language", "sms_reminders", "price_alerts", "date_joined"]
        read_only_fields = ["id", "phone", "kyc_status", "is_staff", "date_joined"]

    def update(self, instance, validated_data):
        # A new or corrected NRC goes back to the queue for a staff check.
        if "nrc_number" in validated_data and validated_data["nrc_number"] != instance.nrc_number:
            instance.kyc_status = Member.KYC.PENDING
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Member
        fields = ["phone", "first_name", "last_name", "nrc_number", "password"]
        extra_kwargs = {"first_name": {"required": True}, "last_name": {"required": True}}

    def validate(self, attrs):
        validate_password(attrs["password"], Member(**{k: v for k, v in attrs.items() if k != "password"}))
        return attrs

    def create(self, validated_data):
        return Member.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        user = authenticate(self.context.get("request"), phone=attrs["phone"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Wrong phone number or password.")
        attrs["user"] = user
        return attrs


class MobileWalletSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="get_provider_display", read_only=True)
    provider = serializers.ChoiceField(choices=MobileWallet.Provider.choices, required=False)

    class Meta:
        model = MobileWallet
        fields = ["id", "provider", "provider_name", "number", "is_default", "created_at"]
        read_only_fields = ["is_default", "created_at"]
        # Duplicate numbers are reported by members.wallets.add_wallet with a clearer message.
        validators = []


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "link", "read_at", "created_at"]
