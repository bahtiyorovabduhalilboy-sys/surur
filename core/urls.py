from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'xodimlar', UserViewSet)
router.register(r'xodimlar-profili', EmployeeProfileViewSet)
router.register(r'taminotchilar', SupplierViewSet)
router.register(r'homashyo', RawMaterialViewSet)
router.register(r'homashyo-ombori', RawMaterialStockViewSet)
router.register(r'tayyor-mahsulotlar', FinishedProductViewSet)
router.register(r'tayyor-mahsulot-ombori', FinishedProductStockViewSet)
router.register(r'qadoqlar-ombori', PackagingStockViewSet)
router.register(r'retseptlar', ProductRecipeViewSet)
router.register(r'ishlab-chiqarish-buyurtmalari', ProductionOrderViewSet)
router.register(r'drabirka', DrabirkaViewSet)
router.register(r'mijozlar', ClientViewSet)
router.register(r'sotuvlar', SaleViewSet)
router.register(r'sotuv-tarkibi', SaleItemViewSet)
router.register(r'xarajatlar', ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reports/summary/', ERPReportView.as_view(), name='erp_report'),
]