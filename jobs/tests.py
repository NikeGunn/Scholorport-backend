"""
Jobs/Careers App Tests

Unit tests for job posting API endpoints.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from datetime import timedelta
import uuid

from .models import Job


class JobModelTests(TestCase):
    """Tests for the Job model."""

    def test_create_job(self):
        """Test creating a basic job."""
        job = Job.objects.create(
            title='Software Engineer',
            description='Test description',
            application_email='test@example.com'
        )
        self.assertEqual(job.title, 'Software Engineer')
        self.assertIsNotNone(job.id)
        self.assertTrue(job.is_active)

    def test_slug_auto_generation(self):
        """Test that slug is auto-generated from title."""
        job = Job.objects.create(
            title='Senior Software Engineer',
            description='Test description',
            application_email='test@example.com'
        )
        self.assertEqual(job.slug, 'senior-software-engineer')

    def test_unique_slug_generation(self):
        """Test that unique slugs are generated for same titles."""
        job1 = Job.objects.create(
            title='Software Engineer',
            description='Test description 1',
            application_email='test@example.com'
        )
        job2 = Job.objects.create(
            title='Software Engineer',
            description='Test description 2',
            application_email='test@example.com'
        )
        self.assertNotEqual(job1.slug, job2.slug)

    def test_is_expired_property(self):
        """Test the is_expired property."""
        # Not expired
        job = Job.objects.create(
            title='Test Job',
            description='Test',
            application_email='test@example.com',
            expires_at=timezone.now() + timedelta(days=30)
        )
        self.assertFalse(job.is_expired)

        # Expired
        job.expires_at = timezone.now() - timedelta(days=1)
        job.save()
        self.assertTrue(job.is_expired)

    def test_html_sanitization(self):
        """Test that HTML is sanitized on save."""
        job = Job.objects.create(
            title='Test Job',
            description='<p>Safe content</p><script>alert("xss")</script>',
            application_email='test@example.com'
        )
        # Script tags should be removed
        self.assertNotIn('<script>', job.description)
        self.assertIn('<p>Safe content</p>', job.description)


class PublicJobAPITests(APITestCase):
    """Tests for public job API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create active jobs
        self.active_job = Job.objects.create(
            title='Active Job',
            slug='active-job',
            department='Engineering',
            location='Remote',
            type='full-time',
            description='<p>Active job description</p>',
            application_email='careers@example.com',
            is_active=True,
            is_featured=True
        )

        # Create inactive job
        self.inactive_job = Job.objects.create(
            title='Inactive Job',
            slug='inactive-job',
            description='Inactive job description',
            application_email='careers@example.com',
            is_active=False
        )

        # Create expired job
        self.expired_job = Job.objects.create(
            title='Expired Job',
            slug='expired-job',
            description='Expired job description',
            application_email='careers@example.com',
            is_active=True,
            expires_at=timezone.now() - timedelta(days=1)
        )

    def test_list_jobs_returns_only_active(self):
        """Test that list jobs returns only active, non-expired jobs."""
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only contain active job
        results = response.data.get('results', response.data)
        slugs = [job['slug'] for job in results]
        self.assertIn('active-job', slugs)
        self.assertNotIn('inactive-job', slugs)
        self.assertNotIn('expired-job', slugs)

    def test_get_job_by_slug(self):
        """Test getting a job by slug."""
        response = self.client.get(f'/api/jobs/{self.active_job.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Active Job')

    def test_get_inactive_job_returns_404(self):
        """Test that inactive jobs return 404."""
        response = self.client.get(f'/api/jobs/{self.inactive_job.slug}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_expired_job_returns_404(self):
        """Test that expired jobs return 404."""
        response = self.client.get(f'/api/jobs/{self.expired_job.slug}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_department(self):
        """Test filtering jobs by department."""
        response = self.client.get('/api/jobs/', {'department': 'Engineering'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertTrue(len(results) > 0)
        for job in results:
            self.assertEqual(job['department'].lower(), 'engineering')

    def test_filter_by_type(self):
        """Test filtering jobs by type."""
        response = self.client.get('/api/jobs/', {'type': 'full-time'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        for job in results:
            self.assertEqual(job['type'], 'full-time')

    def test_search_jobs(self):
        """Test searching jobs."""
        response = self.client.get('/api/jobs/', {'search': 'Active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertTrue(len(results) > 0)


class AdminJobAPITests(APITestCase):
    """Tests for admin job API endpoints."""

    def setUp(self):
        """Set up test data and authentication."""
        self.client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

        # Create test job
        self.job = Job.objects.create(
            title='Test Job',
            slug='test-job',
            description='Test description',
            application_email='careers@example.com',
            is_active=True
        )

    def test_admin_list_requires_auth(self):
        """Test that admin list requires authentication."""
        response = self.client.get('/api/jobs/admin/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_list_with_auth(self):
        """Test admin list with authentication."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/jobs/admin/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_job(self):
        """Test creating a job via admin API."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New Job',
            'description': '<p>New job description</p>',
            'application_email': 'jobs@example.com',
            'department': 'Marketing',
            'type': 'full-time'
        }
        response = self.client.post('/api/jobs/admin/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Job')
        self.assertIsNotNone(response.data['slug'])

    def test_create_job_auto_generates_slug(self):
        """Test that creating a job auto-generates slug."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'Marketing Manager Position',
            'description': 'Test',
            'application_email': 'jobs@example.com'
        }
        response = self.client.post('/api/jobs/admin/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'marketing-manager-position')

    def test_update_job(self):
        """Test updating a job."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/jobs/admin/{self.job.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_delete_job(self):
        """Test deleting a job."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/jobs/admin/{self.job.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_get_job_by_id(self):
        """Test getting a job by ID (admin)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/jobs/admin/{self.job.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Job')

    def test_admin_can_see_inactive_jobs(self):
        """Test that admin can see inactive jobs."""
        self.client.force_authenticate(user=self.admin_user)

        # Create inactive job
        inactive = Job.objects.create(
            title='Inactive Admin Job',
            description='Test',
            application_email='test@example.com',
            is_active=False
        )

        response = self.client.get('/api/jobs/admin/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        slugs = [job['slug'] for job in results]
        self.assertIn(inactive.slug, slugs)
