import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestAuthentication:
    def setup_method(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        url = reverse('auth-register')
        data = {
            'email': 'janice@example.com',
            'name': 'Janice Shirley',
            'password': 'securepassword123'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'janice@example.com'
        assert response.data['name'] == 'Janice Shirley'
        assert 'password' not in response.data
        assert User.objects.filter(email='janice@example.com').exists()

    def test_user_login_success(self):
        User.objects.create_user(
            email='testuser@example.com',
            name='Test User',
            password='mysecretpassword'
        )
        url = reverse('auth-login')
        data = {
            'email': 'testuser@example.com',
            'password': 'mysecretpassword'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'testuser@example.com'

    def test_user_me_authenticated(self):
        user = User.objects.create_user(
            email='me@example.com',
            name='Me User',
            password='password123'
        )
        self.client.force_authenticate(user=user)
        url = reverse('auth-me')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'me@example.com'

    def test_user_me_unauthenticated_fails(self):
        url = reverse('auth-me')
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
