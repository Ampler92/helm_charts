import unittest
from unittest.mock import Mock, patch
from azure.functions import HttpRequest
from your_function_module import comcd_aks_onboarding

class TestYourAzureFunction(unittest.TestCase):

    def setUp(self):
        # Initialize any required environment variables or test data
        pass

    def tearDown(self):
        # Clean up after each test if needed
        pass

    @patch("your_function_module.get_certificate_credential")
    @patch("your_function_module.get_subscription_name_from_id")
    @patch("your_function_module.get_application_by_display_name")
    @patch("your_function_module.iterate_fetch_aks_onb_info")
    @patch("your_function_module.GraphServiceClient")
    def test_comcd_aks_onboarding(self, MockGraphServiceClient, MockIterateFetch,
                                  MockGetAppByName, MockGetSubName, MockGetCertCred):

        # Prepare mock objects and data
        mock_graph_client = Mock()
        MockGraphServiceClient.return_value = mock_graph_client

        mock_cert_creds = Mock()
        MockGetCertCred.return_value = mock_cert_creds

        mock_subscription_name = "TestSubscription"
        MockGetSubName.return_value = mock_subscription_name

        mock_app = Mock()
        MockGetAppByName.return_value = mock_app

        mock_onb_info = '{"server": "https://example.com", "token": "test_token", "ca_cert": "test_cert"}'
        MockIterateFetch.return_value = mock_onb_info

        # Create an HTTP request with required parameters
        request = HttpRequest(
            method='GET',
            url='http://localhost/api/comcd_aks_onboarding',
            params={
                'tenant_id': 'test_tenant',
                'subscription_id': 'test_subscription',
                'resource_group_name': 'test_resource_group',
                'aks_cluster_name': 'test_cluster',
                'customer_k8s_admin': 'test_admin'
            }
        )

        # Call your Azure Function
        response = comcd_aks_onboarding(request)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_body().decode(), mock_onb_info)

        # Verify that your function was called with the expected parameters
        MockGetCertCred.assert_called_once_with('test_tenant', 'test_client_id')
        MockGraphServiceClient.assert_called_once_with(credentials=mock_cert_creds)
        MockGetSubName.assert_called_once_with(mock_cert_creds, 'test_subscription')
        MockGetAppByName.assert_called_once_with(mock_graph_client, 'test_admin', mock_subscription_name)
        MockIterateFetch.assert_called_once_with(mock_cert_creds, 'test_subscription', 'test_resource_group', 'test_cluster')

if __name__ == '__main__':
    unittest.main()




import json
import os
import subprocess
from flask import Flask, jsonify, abort, request

app = Flask(__name__)

def copy_image(nexus_url, harbor_url, nexus_username, nexus_password, harbor_username, harbor_password, image_name, image_version):
    try:
        # Authenticate with Nexus
        nexus_auth_cmd = f"./crane auth login {nexus_url} --username {nexus_username} --password {nexus_password}"
        nexus_auth_result = subprocess.run(nexus_auth_cmd, shell=True, capture_output=True, text=True)
        if nexus_auth_result.returncode != 0:
            raise Exception(f"Failed to authenticate with Nexus: {nexus_auth_result.stderr}")

        # Authenticate with Harbor
        harbor_auth_cmd = f"./crane auth login {harbor_url} --username {harbor_username} --password {harbor_password}"
        harbor_auth_result = subprocess.run(harbor_auth_cmd, shell=True, capture_output=True, text=True)
        if harbor_auth_result.returncode != 0:
            raise Exception(f"Failed to authenticate with Harbor: {harbor_auth_result.stderr}")

        # Copy the image from Nexus to Harbor
        source_image = f"{nexus_url}/{image_name}:{image_version}"
        destination_image = f"{harbor_url}/{image_name}:{image_version}"
        copy_cmd = f"./crane copy {source_image} {destination_image}"
        copy_result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)
        if copy_result.returncode != 0:
            raise Exception(f"Failed to copy image with 'crane': {copy_result.stderr}")

        return True, f"Image copied successfully: {source_image}"

    except Exception as e:
        return False, str(e)

@app.route('/', methods=['POST'])
def process_webhook():
    # Ensure the request is a POST request
    if request.method != 'POST':
        return abort(405)

    try:
        payload = request.get_json()

        # Check if the payload is valid JSON
        if not payload:
            return abort(400, 'Invalid JSON payload')

        timestamp = payload.get('timestamp')
        action = payload.get('action')
        component = payload.get('component')

        # Check if the action is 'CREATED'
        if action != 'CREATED':
            return jsonify({'message': 'Action is not CREATED, skipping'}), 200

        name = component.get('name')
        version = component.get('version')

        # Get environment variables
        nexus_url = os.getenv("NEXUS_URL")
        harbor_url = os.getenv("HARBOR_URL")
        nexus_username = os.getenv("NEXUS_USERNAME")
        nexus_password = os.getenv("NEXUS_PASSWORD")
        harbor_username = os.getenv("HARBOR_USERNAME")
        harbor_password = os.getenv("HARBOR_PASSWORD")

        # Copy the image
        success, message = copy_image(nexus_url, harbor_url, nexus_username, nexus_password, harbor_username, harbor_password, name, version)

        if success:
            return jsonify({'message': message}), 200
        else:
            return abort(500, message)

    except Exception as e:
        return abort(500, str(e))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
