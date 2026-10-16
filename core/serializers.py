from rest_framework import serializers
from core.models import *
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):

  class Meta:
    model = User
    fields = [
        'id',
        'username',
        'email',
        'full_name',
        'role',
        'phone_number',
    ]


class EmployeeProfileSerializer(serializers.ModelSerializer):
  user = UserSerializer(read_only=True)

  class Meta:
    model = EmployeeProfile
    fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):

  class Meta:
    model = Supplier
    fields = '__all__'


class RawMaterialSerializer(serializers.ModelSerializer):

  class Meta:
    model = RawMaterial
    fields = '__all__'


class RawMaterialStockSerializer(serializers.ModelSerializer):

  class Meta:
    model = RawMaterialStock
    fields = '__all__'


class FinishedProductSerializer(serializers.ModelSerializer):

  class Meta:
    model = FinishedProduct
    fields = '__all__'


class FinishedProductStockSerializer(serializers.ModelSerializer):

  class Meta:
    model = FinishedProductStock
    fields = '__all__'


class PackagingStockSerializer(serializers.ModelSerializer):

  class Meta:
    model = PackagingStock
    fields = '__all__'


class ProductRecipeSerializer(serializers.ModelSerializer):

  class Meta:
    model = ProductRecipe
    fields = '__all__'


class ProductionOrderSerializer(serializers.ModelSerializer):

  class Meta:
    model = ProductionOrder
    fields = '__all__'


class DrabirkaSerializer(serializers.ModelSerializer):

  class Meta:
    model = Drabirka
    fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):

  class Meta:
    model = Client
    fields = '__all__'


class SaleItemSerializer(serializers.ModelSerializer):

  class Meta:
    model = SaleItem
    fields = '__all__'


class SaleSerializer(serializers.ModelSerializer):
  items = SaleItemSerializer(many=True, read_only=True)

  class Meta:
    model = Sale
    fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):

  class Meta:
    model = Expense
    fields = '__all__'


User = get_user_model()

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception as exc:
            raise serializers.ValidationError("Token yaroqsiz yoki allaqachon bekor qilingan.") from exc


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ushbu email bilan ro'yxatdan o'tgan xodim topilmadi.")
        return value

    def send_reset_email(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"http://127.0.0.1:8000/api/v1/auth/password-reset-confirm/{uid}/{token}/"

        subject = "Parolni tiklash - Surur ERP"
        message = (
            f"Salom {user.username},\n\n"
            "Parolingizni tiklash uchun quyidagi havolaga bosing:\n"
            f"{reset_link}\n\n"
            "Agar bu so'rovni siz yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring."
        )
        send_mail(subject, message, None, [email])


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def save_new_password(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Yaroqsiz UID")

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise serializers.ValidationError("Token yaroqsiz yoki muddati o'tgan")

        user.set_password(self.validated_data['new_password'])
        user.save()
        return user