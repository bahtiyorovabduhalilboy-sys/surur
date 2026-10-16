from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import *
from core.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    search_fields = ['username', 'first_name', 'last_name']


class EmployeeProfileViewSet(viewsets.ModelViewSet):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user']


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'phone']


class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['supplier']
    search_fields = ['name']


class RawMaterialStockViewSet(viewsets.ModelViewSet):
    queryset = RawMaterialStock.objects.all()
    serializer_class = RawMaterialStockSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['raw_material']


class FinishedProductViewSet(viewsets.ModelViewSet):
    queryset = FinishedProduct.objects.all()
    serializer_class = FinishedProductSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']


class FinishedProductStockViewSet(viewsets.ModelViewSet):
    queryset = FinishedProductStock.objects.all()
    serializer_class = FinishedProductStockSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product']


class PackagingStockViewSet(viewsets.ModelViewSet):
    queryset = PackagingStock.objects.all()
    serializer_class = PackagingStockSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']


class ProductRecipeViewSet(viewsets.ModelViewSet):
    queryset = ProductRecipe.objects.all()
    serializer_class = ProductRecipeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product', 'raw_material']


class ProductionOrderViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrder.objects.all()
    serializer_class = ProductionOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'product']
    search_fields = ['comment']
    ordering_fields = ['created_at', 'deadline']


class DrabirkaViewSet(viewsets.ModelViewSet):
    queryset = Drabirka.objects.all()
    serializer_class = DrabirkaSerializer
    permission_classes = [IsAuthenticated]


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'phone']


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['client']
    ordering_fields = ['created_at']


class SaleItemViewSet(viewsets.ModelViewSet):
    queryset = SaleItem.objects.all()
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['sale', 'product']


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['created_at', 'amount_uzs']

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Muvaffaqiyatli tizimdan chiqildi."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.send_reset_email()
            return Response({"message": "Parolni tiklash havolasi email manzilingizga yuborildi."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save_new_password(uidb64, token)
            return Response({"message": "Parol muvaffaqiyatli yangilandi!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ERPReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_sales = Sale.objects.aggregate(total=Sum('total_sum_uzs'))['total'] or 0
        total_expenses = Expense.objects.aggregate(total=Sum('amount_uzs'))['total'] or 0
        net_profit = total_sales - total_expenses

        raw_stock_total = RawMaterialStock.objects.aggregate(total=Sum('quantity'))['total'] or 0
        product_stock_total = FinishedProductStock.objects.aggregate(total=Sum('quantity'))['total'] or 0

        report_data = {
            "umumiy_savdo_summasi": total_sales,
            "umumiy_xarajatlar": total_expenses,
            "sof_foyda": net_profit,
            "homashyo_umumiy_miqdori": raw_stock_total,
            "tayyor_mahsulot_umumiy_miqdori": product_stock_total,
        }
        return Response(report_data)