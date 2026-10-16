from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
  class Role(models.TextChoices):
    DIREKTOR = 'direktor', 'Direktor'
    MENEJER = 'menejer', 'Menejer (Sotuv)'
    TEXNOLOG = 'texnolog', 'Texnolog'
    ISH_YURITUVCHI = 'ish_yurituvchi', 'Ish yurituvchi'
    OMBORCHI = 'omborchi', 'Omborchi'
    HAYDOVCHI = 'haydovchi', 'Haydovchi'

  role = models.CharField(
      max_length=50, choices=Role.choices, default=Role.MENEJER
  )
  phone_number = models.CharField(max_length=20, blank=True, null=True)
  full_name = models.CharField(max_length=150, blank=True, null=True)


class EmployeeProfile(models.Model):
  user = models.OneToOneField(
      User, on_delete=models.CASCADE, related_name='profile'
  )
  address = models.TextField(blank=True, null=True)
  birth_date = models.DateField(blank=True, null=True)
  parent_names = models.CharField(max_length=255, blank=True, null=True)
  parent_birth_date = models.DateField(blank=True, null=True)
  hire_date = models.DateField(auto_now_add=True)
  order_number = models.CharField(max_length=50, blank=True, null=True)
  comment = models.TextField(blank=True, null=True)
  base_salary = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  bonus_salary = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

  def __str__(self):
    return f'{self.user.username}'



class Supplier(models.Model):
  name = models.CharField(max_length=255)
  address = models.TextField(blank=True, null=True)
  phone = models.CharField(max_length=20, blank=True, null=True)
  bank_details = models.TextField(blank=True, null=True)
  responsible_person = models.CharField(max_length=150, blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name


class RawMaterial(models.Model):
  name = models.CharField(max_length=255)
  unit = models.CharField(max_length=50)
  supplier = models.ForeignKey(
      Supplier, on_delete=models.SET_NULL, null=True, blank=True
  )
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name


class RawMaterialStock(models.Model):
  raw_material = models.ForeignKey(
      RawMaterial, on_delete=models.CASCADE, related_name='stocks'
  )
  quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
  purchase_price = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  updated_at = models.DateTimeField(auto_now=True)


class FinishedProduct(models.Model):
  name = models.CharField(max_length=255)
  unit = models.CharField(max_length=50)
  cost_price = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  sale_price_uzs = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  sale_price_usd = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )

  def __str__(self):
    return self.name


class FinishedProductStock(models.Model):
  product = models.ForeignKey(
      FinishedProduct, on_delete=models.CASCADE, related_name='stocks'
  )
  quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
  updated_at = models.DateTimeField(auto_now=True)


class PackagingStock(models.Model):
  name = models.CharField(max_length=255)
  supplier = models.ForeignKey(
      Supplier, on_delete=models.SET_NULL, null=True, blank=True
  )
  quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
  updated_at = models.DateTimeField(auto_now=True)


class ProductRecipe(models.Model):
  product = models.ForeignKey(
      FinishedProduct, on_delete=models.CASCADE, related_name='recipes'
  )
  raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE)
  quantity = models.DecimalField(max_digits=12, decimal_places=3)

from decimal import Decimal
from django.db import models

class ProductionOrder(models.Model):
    class Status(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        TAYYORLANMOQDA = 'tayyorlanmoqda', 'Tayyorlanmoqda'
        TAYYOR = 'tayyor', 'Tayyor'

    product = models.ForeignKey('FinishedProduct', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    comment = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField()
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.YANGI
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            original = ProductionOrder.objects.get(pk=self.pk)
            if original.status != self.Status.TAYYOR and self.status == self.Status.TAYYOR:
                self.process_production()
        else:
            if self.status == self.Status.TAYYOR:
                super().save(*args, **kwargs)
                self.process_production()
                return

        super().save(*args, **kwargs)

    def process_production(self):
        recipes = ProductRecipe.objects.filter(product=self.product)

        for recipe in recipes:
            required_amount = recipe.quantity * self.quantity

            try:
                stock = RawMaterialStock.objects.get(raw_material=recipe.raw_material)
                if stock.quantity >= required_amount:
                    stock.quantity -= required_amount
                    stock.save()
                else:
                    raise ValueError(f"Omborda yetarli homashyo yo'q: {recipe.raw_material.name}")
            except RawMaterialStock.DoesNotExist:
                raise ValueError(f"Homashyo omborda topilmadi: {recipe.raw_material.name}")

        finished_stock, created = FinishedProductStock.objects.get_or_create(product=self.product)
        finished_stock.quantity += self.quantity
        finished_stock.save()

    def __str__(self):
        return f"{self.product} - {self.quantity} ({self.status})"


class Drabirka(models.Model):
    class Status(models.TextChoices):
        YAROQLI = 'yaroqli', 'Yaroqli'
        YAROQSIZ = 'yaroqsiz', 'Yaroqsiz'

    product = models.ForeignKey(FinishedProduct, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.Status.YAROQLI if hasattr(Status, 'Status') else Status.YAROQLI
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0.00)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Agar status yaroqsiz (brak) bo'lsa va bu yangi qo'shilayotgan bo'lsa
        if not self.pk and self.status == self.Status.YAROQSIZ:
            try:
                stock = FinishedProductStock.objects.get(product=self.product)
                if stock.quantity >= self.quantity:
                    stock.quantity -= self.quantity
                    stock.save()
                else:
                    raise ValueError(f"Omborda drabirka uchun yetarli tayyor mahsulot yo'q: {self.product.name}")
            except FinishedProductStock.DoesNotExist:
                raise ValueError(f"Tayyor mahsulot omborda topilmadi: {self.product.name}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} ({self.get_status_display()})"

class Client(models.Model):
  name = models.CharField(max_length=255)
  director_name = models.CharField(max_length=255, blank=True, null=True)
  phone = models.CharField(max_length=20, blank=True, null=True)
  address = models.TextField(blank=True, null=True)
  comment = models.TextField(blank=True, null=True)
  bank_account = models.CharField(max_length=50, blank=True, null=True)
  mfo = models.CharField(max_length=20, blank=True, null=True)
  inn = models.CharField(max_length=20, blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.name


class Sale(models.Model):
  client = models.ForeignKey(Client, on_delete=models.CASCADE)
  payment_type = models.CharField(max_length=50)
  total_sum_uzs = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  total_sum_usd = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  comment = models.TextField(blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)


class SaleItem(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('FinishedProduct', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                stock = FinishedProductStock.objects.get(product=self.product)
                if stock.quantity >= self.quantity:
                    stock.quantity -= self.quantity
                    stock.save()
                else:
                    raise ValueError(f"Omborda yetarli tayyor mahsulot yo'q: {self.product}")
            except FinishedProductStock.DoesNotExist:
                raise ValueError(f"Tayyor mahsulot omborda topilmadi: {self.product}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.quantity} ta"

class Expense(models.Model):
  name = models.CharField(max_length=255)
  category = models.CharField(max_length=100)
  amount_uzs = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  amount_usd = models.DecimalField(
      max_digits=12, decimal_places=2, default=0
  )
  payment_type = models.CharField(max_length=50)
  comment = models.TextField(blank=True, null=True)
  created_at = models.DateTimeField(auto_now_add=True)
