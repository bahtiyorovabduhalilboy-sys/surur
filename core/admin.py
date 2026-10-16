from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(EmployeeProfile)
admin.site.register(Supplier)
admin.site.register(RawMaterial)
admin.site.register(RawMaterialStock)
admin.site.register(FinishedProduct)
admin.site.register(FinishedProductStock)
admin.site.register(PackagingStock)
admin.site.register(ProductRecipe)
admin.site.register(ProductionOrder)
admin.site.register(Drabirka)
admin.site.register(Client)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Expense)