import unittest
from unittest.mock import patch, MagicMock
from main import process_webhook
from flask import Flask, request

class TestProcessWebhook(unittest.TestCase):
    def setUp(self):
        # Create a Flask test client
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('main.copy_image')  # Mock the copy_image function
    def test_valid_payload_created_action(self, mock_copy_image):
        # Create a mock JSON payload with a CREATED action
        mock_payload = {
            'timestamp': '2023-09-05T12:00:00.000+0000',
            'action': 'CREATED',
            'component': {
                'name': 'test-image',
                'version': '1.0.0',
            },
        }

        # Mock the copy_image function to return success
        mock_copy_image.return_value = (True, 'Image copied successfully')

        # Simulate a POST request with the mock payload
        response = self.client.post('/', json=mock_payload)

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check if the response contains the success message
        self.assertEqual(response.json['message'], 'Image copied successfully')

        # Ensure that copy_image was called with the correct arguments
        mock_copy_image.assert_called_once_with(
            'nexus_url', 'harbor_url', 'nexus_username', 'nexus_password',
            'harbor_username', 'harbor_password', 'test-image', '1.0.0'
        )

    def test_invalid_json_payload(self):
        # Send an invalid JSON payload
        response = self.client.post('/', data='invalid_json_payload')

        # Check the response status code (expecting 400 for invalid JSON)
        self.assertEqual(response.status_code, 400)

    def test_non_created_action(self):
        # Create a mock JSON payload with a non-CREATED action
        mock_payload = {
            'timestamp': '2023-09-05T12:00:00.000+0000',
            'action': 'DELETED',  # Example of a non-CREATED action
            'component': {
                'name': 'test-image',
                'version': '1.0.0',
            },
        }

        # Simulate a POST request with the mock payload
        response = self.client.post('/', json=mock_payload)

        # Check the response status code (expecting 200 with a message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Action is not CREATED, skipping')

    @patch('main.copy_image')  # Mock the copy_image function
    def test_copy_image_error(self, mock_copy_image):
        # Create a mock JSON payload with a CREATED action
        mock_payload = {
            'timestamp': '2023-09-05T12:00:00.000+0000',
            'action': 'CREATED',
            'component': {
                'name': 'test-image',
                'version': '1.0.0',
            },
        }

        # Mock the copy_image function to return an error
        mock_copy_image.return_value = (False, 'Failed to copy image')

        # Simulate a POST request with the mock payload
        response = self.client.post('/', json=mock_payload)

        # Check the response status code (expecting 500 for an error)
        self.assertEqual(response.status_code, 500)

        # Check if the response contains the error message
        self.assertEqual(response.data.decode('utf-8'), 'Failed to copy image')

if __name__ == '__main__':
    unittest.main()