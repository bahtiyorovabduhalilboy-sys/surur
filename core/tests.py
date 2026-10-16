from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.models import *

class ERPAPITestCase(APITestCase):
    def setUp(self):
        self.director = User.objects.create_user(
            username='director',
            password='director123',
            email='director@example.com',
            role=User.Role.DIREKTOR,
            full_name='Director User',
            is_staff=True,
            is_superuser=True,
        )
        self.worker = User.objects.create_user(
            username='worker',
            password='worker123',
            email='worker@example.com',
            role=User.Role.MENEJER,
            full_name='Worker User',
        )

        self.director_client = APIClient()
        self.worker_client = APIClient()
        self.director_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.obtain_token(self.director)}')
        self.worker_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.obtain_token(self.worker)}')

        self.supplier = Supplier.objects.create(
            name='Supplier One',
            phone='+998901234567',
            address='Tashkent',
        )
        self.raw_material = RawMaterial.objects.create(
            name='Sugar',
            unit='kg',
            supplier=self.supplier,
        )
        self.raw_material_stock = RawMaterialStock.objects.create(
            raw_material=self.raw_material,
            quantity=Decimal('100.000'),
            purchase_price=Decimal('11.00'),
        )

        self.product = FinishedProduct.objects.create(
            name='Coca Cola',
            unit='pcs',
            cost_price=Decimal('8.00'),
            sale_price_uzs=Decimal('20.00'),
            sale_price_usd=Decimal('0.80'),
        )
        self.finished_product_stock = FinishedProductStock.objects.create(
            product=self.product,
            quantity=Decimal('100.000'),
        )

        self.client_obj = Client.objects.create(
            name='Client One',
            phone='+998909876543',
            address='Samarkand',
        )

        self.recipe = ProductRecipe.objects.create(
            product=self.product,
            raw_material=self.raw_material,
            quantity=Decimal('2.000'),
        )

    def obtain_token(self, user):
        password = 'director123' if user.username == 'director' else 'worker123'
        response = self.client.post(
            '/api/v1/token/',
            {'username': user.username, 'password': password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_authentication_and_permissions_for_director_and_worker(self):
        response = self.director_client.get('/api/v1/xodimlar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.worker_client.get('/api/v1/xodimlar/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_blacklists_refresh_token(self):
        refresh = self.client.post(
            '/api/v1/token/',
            {'username': 'director', 'password': 'director123'},
            format='json',
        ).data['refresh']

        response = self.director_client.post(
            '/api/v1/auth/logout/',
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        refresh_response = self.client.post(
            '/api/v1/token/refresh/',
            {'refresh': refresh},
            format='json',
        )
        self.assertIn(refresh_response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST])

    def test_raw_material_and_stock_can_be_created(self):
        payload = {'name': 'Flour', 'unit': 'kg', 'supplier': self.supplier.id}
        response = self.worker_client.post('/api/v1/homashyo/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        stock_payload = {
            'raw_material': response.data['id'],
            'quantity': '75.000',
            'purchase_price': '12.50',
        }
        stock_response = self.worker_client.post('/api/v1/homashyo-ombori/', stock_payload, format='json')
        self.assertEqual(stock_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(str(stock_response.data['quantity'])), Decimal('75.000'))

    def test_production_order_reduces_raw_material_stock_and_increases_finished_stock(self):
        self.raw_material_stock.quantity = Decimal('100.000')
        self.raw_material_stock.save(update_fields=['quantity'])

        response = self.worker_client.post(
            '/api/v1/ishlab-chiqarish-buyurtmalari/',
            {
                'product': self.product.id,
                'quantity': '10.000',
                'deadline': '2030-01-01T12:00:00Z',
                'status': 'tayyor',
                'comment': 'Production run',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.raw_material_stock.refresh_from_db()
        self.finished_product_stock.refresh_from_db()
        self.assertEqual(self.raw_material_stock.quantity, Decimal('80.000'))
        self.assertEqual(self.finished_product_stock.quantity, Decimal('110.000'))

    def test_sale_item_reduces_finished_stock(self):
        self.finished_product_stock.quantity = Decimal('100.000')
        self.finished_product_stock.save(update_fields=['quantity'])

        sale = Sale.objects.create(
            client=self.client_obj,
            payment_type='naqd',
            total_sum_uzs=Decimal('500.00'),
            total_sum_usd=Decimal('5.00'),
            comment='Daily sale',
        )

        response = self.worker_client.post(
            '/api/v1/sotuv-tarkibi/',
            {
                'sale': sale.id,
                'product': self.product.id,
                'quantity': '20.000',
                'price': '40.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.finished_product_stock.refresh_from_db()
        self.assertEqual(self.finished_product_stock.quantity, Decimal('80.000'))

    def test_insufficient_sale_stock_raises_value_error(self):
        self.finished_product_stock.quantity = Decimal('10.000')
        self.finished_product_stock.save(update_fields=['quantity'])

        sale = Sale.objects.create(
            client=self.client_obj,
            payment_type='plastik',
            total_sum_uzs=Decimal('100.00'),
            total_sum_usd=Decimal('1.00'),
        )

        with self.assertRaises(ValueError):
            SaleItem.objects.create(
                sale=sale,
                product=self.product,
                quantity=Decimal('15.000'),
                price=Decimal('50.00'),
            )

    def test_drabirka_reduces_finished_stock_when_status_is_broken(self):
        self.finished_product_stock.quantity = Decimal('30.000')
        self.finished_product_stock.save(update_fields=['quantity'])

        response = self.worker_client.post(
            '/api/v1/drabirka/',
            {
                'product': self.product.id,
                'status': 'yaroqsiz',
                'quantity': '10.000',
                'reason': 'packaging damage',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.finished_product_stock.refresh_from_db()
        self.assertEqual(self.finished_product_stock.quantity, Decimal('20.000'))

    def test_expense_can_be_created_and_summary_report_is_correct(self):
        Sale.objects.create(
            client=self.client_obj,
            payment_type='naqd',
            total_sum_uzs=Decimal('300.00'),
            total_sum_usd=Decimal('3.00'),
        )
        Sale.objects.create(
            client=self.client_obj,
            payment_type='transfer',
            total_sum_uzs=Decimal('200.00'),
            total_sum_usd=Decimal('2.00'),
        )
        Expense.objects.create(
            name='Rent',
            category='office',
            amount_uzs=Decimal('100.00'),
            amount_usd=Decimal('1.00'),
            payment_type='cash',
        )
        Expense.objects.create(
            name='Internet',
            category='office',
            amount_uzs=Decimal('50.00'),
            amount_usd=Decimal('0.50'),
            payment_type='transfer',
        )

        response = self.worker_client.get('/api/v1/reports/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['umumiy_savdo_summasi'])), Decimal('500.00'))
        self.assertEqual(Decimal(str(response.data['umumiy_xarajatlar'])), Decimal('150.00'))
        self.assertEqual(Decimal(str(response.data['sof_foyda'])), Decimal('350.00'))

    def test_main_crud_endpoints_return_expected_status_codes(self):
        create_payload = {
            'name': 'Test Supplier',
            'phone': '+998901000000',
            'address': 'Bukhara',
            'responsible_person': 'Test Person',
        }
        create_response = self.worker_client.post('/api/v1/taminotchilar/', create_payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        supplier_id = create_response.data['id']

        detail_url = f'/api/v1/taminotchilar/{supplier_id}/'
        list_response = self.worker_client.get('/api/v1/taminotchilar/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        update_payload = {'name': 'Updated Supplier', 'phone': '+998901111111', 'address': 'Andijan'}
        put_response = self.worker_client.put(detail_url, update_payload, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)

        delete_response = self.worker_client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_and_search_endpoints_work(self):
        Supplier.objects.create(name='Alpha Supplier', phone='+998900000001', address='Tashkent')
        Supplier.objects.create(name='Beta Supplier', phone='+998900000002', address='Fergana')

        search_response = self.worker_client.get('/api/v1/taminotchilar/?search=Alpha')
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['name'] == 'Alpha Supplier' for item in search_response.data))

        material_response = self.worker_client.get(f'/api/v1/homashyo/?supplier={self.supplier.id}')
        self.assertEqual(material_response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['supplier'] == self.supplier.id for item in material_response.data))

        production_response = self.worker_client.get('/api/v1/ishlab-chiqarish-buyurtmalari/?status=tayyor')
        self.assertEqual(production_response.status_code, status.HTTP_200_OK)

        sale_response = self.worker_client.get(f'/api/v1/sotuvlar/?client={self.client_obj.id}')
        self.assertEqual(sale_response.status_code, status.HTTP_200_OK)
