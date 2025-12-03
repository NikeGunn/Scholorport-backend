"""
Admin API Tests
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class AdminAuthTestCase(TestCase):
    """Tests for admin authentication endpoints."""

    def setUp(self):
        self.client = APIClient()
        # Create a superuser
        self.admin_user = User.objects.create_superuser(
            username='testadmin',
            email='testadmin@scholarport.co',
            password='testpass123'
        )
        # Create a regular staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@scholarport.co',
            password='staffpass123',
            is_staff=True
        )
        # Create a regular (non-staff) user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@scholarport.co',
            password='regularpass123'
        )

    def test_admin_login_success(self):
        """Test successful admin login."""
        response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_admin_login_wrong_password(self):
        """Test login with wrong password."""
        response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'testadmin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_staff_cannot_login(self):
        """Test that non-staff users cannot login to admin."""
        response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'regularuser',
            'password': 'regularpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_current_user(self):
        """Test getting current user profile."""
        # Login first
        login_response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        token = login_response.data['access']

        # Get current user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/admin-panel/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], 'testadmin')


class AdminDashboardTestCase(TestCase):
    """Tests for admin dashboard endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='testadmin',
            email='testadmin@scholarport.co',
            password='testpass123'
        )
        # Login and get token
        login_response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        self.token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_dashboard_overview(self):
        """Test dashboard overview endpoint."""
        response = self.client.get('/api/admin-panel/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)

    def test_recent_activity(self):
        """Test recent activity endpoint."""
        response = self.client.get('/api/admin-panel/dashboard/activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_analytics_data(self):
        """Test analytics data endpoint."""
        response = self.client.get('/api/admin-panel/dashboard/analytics/?period=week')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class AdminUserManagementTestCase(TestCase):
    """Tests for admin user management endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='super@scholarport.co',
            password='superpass123'
        )
        self.regular_admin = User.objects.create_user(
            username='regularadmin',
            email='admin@scholarport.co',
            password='adminpass123',
            is_staff=True
        )
        # Login as superadmin
        login_response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'superadmin',
            'password': 'superpass123'
        })
        self.token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_users(self):
        """Test listing admin users."""
        response = self.client.get('/api/admin-panel/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_create_user_as_superadmin(self):
        """Test creating a new admin user as superadmin."""
        response = self.client.post('/api/admin-panel/users/create/', {
            'username': 'newadmin',
            'email': 'newadmin@scholarport.co',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_as_regular_admin_fails(self):
        """Test that regular admin cannot create users."""
        # Login as regular admin
        login_response = self.client.post('/api/admin-panel/auth/login/', {
            'username': 'regularadmin',
            'password': 'adminpass123'
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/admin-panel/users/create/', {
            'username': 'newadmin2',
            'email': 'newadmin2@scholarport.co',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
