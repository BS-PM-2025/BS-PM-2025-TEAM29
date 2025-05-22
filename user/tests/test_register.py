import unittest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from user.views import register_view

class RegisterViewTest(unittest.TestCase):

    @patch('user.views.auth.create_user')
    @patch('user.views.firestore.client')
    def test_register_view_success(self, mock_firestore_client, mock_create_user):
        # Setup mock Firebase Auth
        mock_user = MagicMock()
        mock_user.uid = 'testuid123'
        mock_create_user.return_value = mock_user

        # Setup mock Firestore
        mock_firestore = MagicMock()
        mock_firestore_client.return_value = mock_firestore

        # Simulate POST request
        factory = RequestFactory()
        request = factory.post('/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        })

        response = register_view(request)

        # Assert redirection to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

        # Check Firestore called with correct data
        mock_firestore.collection.assert_called_with('Users')
        mock_firestore.collection().document.assert_called_with('testuid123')
        mock_firestore.collection().document().set.assert_called_with({
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'user',
            'id': 'testuid123'
        })

    @patch('user.views.auth.create_user')
    def test_password_mismatch(self, mock_create_user):
        factory = RequestFactory()
        request = factory.post('/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pass1',
            'confirm_password': 'pass2'
        })

        response = register_view(request)

        # Should redirect back to register with error
        self.assertEqual(response.status_code, 302)
        self.assertIn('/register', response.url)
        mock_create_user.assert_not_called()

if __name__ == '__main__':
    unittest.main()
