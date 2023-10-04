# Import statements and constants (unchanged)

async def remove_customer_spn_secret(key_id, object_id, token):
    # ... (unchanged)

async def get_customer_spn_secret_values(object_id, token):
    # ... (unchanged)

async def get_aks_onb_info(customer_client_id, customer_client_secret, customer_tenant_id,
                           subscription_id, resource_group_name, aks_cluster_name):
    # ... (unchanged)

async def get_object_and_app_id_for_customer_spn(customer_k8s_admin, token, subscription_name) -> Any | None:
    # ... (unchanged)

async def get_subscription_name_from_id(tenant_id, client_id, client_secret, subscription_id):
    # ... (unchanged)

async def get_token(tenant_id, client_id, client_secret, scope):
    # ... (unchanged)

async def get_managed_cluster(tenant_id, client_id, client_secret, subscription_id, resource_group_name,
                              aks_cluster_name):
    # ... (unchanged)

async def fetch_aks_onboarding_info(customer_tenant_id, comcd_client_id, comcd_client_secret,
                                    subscription_id, resource_group_name, aks_cluster_name,
                                    customer_k8s_admin, graph_token):
    try:
        # ... (unchanged)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # ComCD SPN credentials (unchanged)

    # Get parameters (unchanged)

    logging.info(f"Getting aks_onb_info for AKS {subscription_id}/{resource_group_name}/{aks_cluster_name}")

    try:
        graph_token = await get_token(customer_tenant_id, comcd_client_id, comcd_client_secret,
                                      https://graph.microsoft.com/.default)

        subscription_name = await get_subscription_name_from_id(customer_tenant_id, comcd_client_id,
                                                                comcd_client_secret, subscription_id)

        object_and_app_id, customer_spn_secret, onb_info = await fetch_aks_onboarding_info(
            customer_tenant_id, comcd_client_id, comcd_client_secret, subscription_id,
            resource_group_name, aks_cluster_name, customer_k8s_admin, graph_token
        )

        if onb_info and \
            json.loads(onb_info)['ca_cert'] and \
            json.loads(onb_info)['server'] and \
            json.loads(onb_info)['token']:
            return func.HttpResponse(onb_info, status_code=200)
        else:
            return func.HttpResponse(
                json.dumps({"error_message": f"[PART2] Onboarding info retrieval failed, Error: {error}"}),
                status_code=500
            )

    except Exception as e:
        error = e
        logging.error(json.dumps(
            {f"attempt_{attempt}_error_message": f"[PART2] Onboarding info retrieval failed, Error: {error}"}
        ))
        return func.HttpResponse(
            json.dumps({"error_message": f"[PART2] Onboarding info retrieval failed, Error: {error}"}),
            status_code=500
        )





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
        self.assertEqual(response.status_code, 500






                         
import json
import logging
import os
import time
import asyncio
from typing import Any
import aiohttp  # Import aiohttp library
import azure.functions as func
import requests
import yaml
from azure.identity import ClientSecretCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import CredentialResults

# Logging Level
if os.getenv("ENABLE_DEBUG_LOGGING", "FALSE") == "TRUE":
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)

async def remove_customer_spn_secret(key_id, object_id, token):
    url = f"https://graph.microsoft.com/v1.0/applications/{object_id}/removePassword"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    data = {
        "keyId": f"{key_id}"
    }
    async with aiohttp.ClientSession() as client:  # Create an aiohttp ClientSession
        async with client.post(url, headers=headers, data=json.dumps(data)) as response:
            if response.status == 204:
                logging.info(f"Customer secret with keyId {key_id} has been successfully removed.")
            else:
                raise RuntimeError(f"Failed to remove_customer_spn_secret with keyId {key_id}: {await response.text()}")

async def get_customer_spn_secret_values(object_id, token):
    url = f"https://graph.microsoft.com/v1.0/applications/{object_id}/addPassword"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    data = {
        "passwordCredential": {
            "displayName": "comcd-aks"
        }
    }
    async with aiohttp.ClientSession() as client:  # Create an aiohttp ClientSession
        async with client.post(url, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                result = json.loads(await response.text())
                response_data = {
                    "keyId": result['keyId'],
                    "secretText": result['secretText']
                }
                return json.dumps(response_data)
            else:
                raise RuntimeError(f"Failed to get_customer_spn_secret: {json.dumps(await response.json())}")

async def get_aks_onb_info(customer_credential, subscription_id, resource_group_name, aks_cluster_name):
    global server_id, server, ca_cert
    k8s_client = ContainerServiceClient(customer_credential, subscription_id)
    response: CredentialResults = await k8s_client.managed_clusters.list_cluster_user_credentials(resource_group_name, aks_cluster_name)
    if response and response.kubeconfigs:
        kubeconfig = response.kubeconfigs[0].value
        if kubeconfig:
            logging.info(kubeconfig.decode("utf-8"))
            kubeconfig_data = yaml.safe_load(kubeconfig.decode("utf-8"))
            kubeconfig_cluster = kubeconfig_data["clusters"][0]["cluster"]
            ca_cert = kubeconfig_cluster["certificate-authority-data"]
            server = kubeconfig_cluster["server"]
            args = kubeconfig_data["users"][0]["user"]["exec"]["args"]
            server_id_index = args.index("--server-id")
            server_id = args[server_id_index + 1]

    access_token = customer_credential.get_token(f"{server_id}/.default").token
    if server and access_token and ca_cert:
        response_data = {
            "server": server,
            "token": access_token,
            "ca_cert": ca_cert
        }
        result = json.dumps(response_data)
        return result
    else:
        raise RuntimeError(f"Failed to get_aks_onb_info for AKS {subscription_id}/{resource_group_name}/{aks_cluster_name}")

async def get_subscription_name_from_subscription_id(management_token, subscription_id) -> Any | None:
    url = f"https://management.azure.com/subscriptions/{subscription_id}?api-version=2022-09-01"
    async with aiohttp.ClientSession() as client:  # Create an aiohttp ClientSession
        async with client.get(url, headers={"Authorization": f"Bearer {management_token}"}) as response:
            if response.status == 200:
                result = json.loads(await response.text())
                return result['displayName']
            else:
                raise RuntimeError(f"Failed to get_subscription_name_from_subscription_id: {json.dumps(await response.json())}")

async def get_object_and_app_id_for_customer_spn(customer_k8s_admin, graph_token, subscription_name) -> Any | None:
    if customer_k8s_admin:
        azure_customer_spn_name = customer_k8s_admin
    else:
        parts = subscription_name.split('-', 2)
        azure_customer_spn_name = f"{parts[0]}-{parts[1]}comcd-{parts[2]}"
    logging.info('azure_customer_spn_name ' + azure_customer_spn_name)
    url = f"https://graph.microsoft.com/v1.0/applications?$filter=displayName%20eq%20%27{azure_customer_spn_name}%27"
    logging.info('url ' + url)
    async with aiohttp.ClientSession() as client:  # Create an aiohttp ClientSession
        async with client.get(url, headers={"Authorization": f"Bearer {graph_token}"}) as response:
            if response.status == 200:
                result = json.loads(await response.text())
                response_data = {
                    "object_id": result['value'][0]['id'],
                    "client_id": result['value'][0]['appId']
                }
                return json.dumps(response_data)
            else:
                raise RuntimeError(f"Failed to get_object_id_for_customer_spn: {json.dumps(await response.json())}")

async def main(req: func.HttpRequest) -> func.HttpResponse:
    # Init Variables
    global onb_info, customer_spn_secret, object_and_app_id, graph_token, error

    # ComCD SPN credentials
    comcd_client_id = os.getenv("AZURE_CLIENT_ID")
    comcd_client_secret = os.getenv("AZURE_CLIENT_SECRET")

    # Get parameters
    customer_tenant_id = req.params.get('tenant_id')
    subscription_id = req.params.get('subscription_id')
    resource_group_name = req.params.get('resource_group_name')
    aks_cluster_name = req.params.get('aks_cluster_name')
    customer_k8s_admin = req.params.get('customer_k8s_admin')

    logging.info(f"Getting aks_onb_info for AKS {subscription_id}/{resource_group_name}/{aks_cluster_name}")

    try:
        # ComCD SPN credential and tokens generation
        credential = ClientSecretCredential(customer_tenant_id, comcd_client_id, comcd_client_secret)
        management_token = credential.get_token("https://management.azure.com/.default").token
        graph_token = credential.get_token("https://graph.microsoft.com/.default").token

        # Get Subscription Name From Subscription ID
        subscription_name = await get_subscription_name_from_subscription_id(management_token, subscription_id)

        # Get Object ID From Customer SPN
        object_and_app_id = await get_object_and_app_id_for_customer_spn(customer_k8s_admin, graph_token, subscription_name)

        # Customer SPN credential and tokens generation
        customer_spn_secret = await get_customer_spn_secret_values(json.loads(object_and_app_id)['object_id'], graph_token)
        customer_credential = ClientSecretCredential(
            customer_tenant_id,
            json.loads(object_and_app_id)['client_id'],
            json.loads(customer_spn_secret)['secretText']
        )

    except Exception as e:
        error = e
        logging.error(f"[PART1] Onboarding info retrieval failed, Error: {error}")
        if json.loads(customer_spn_secret)['keyId']:
            await remove_customer_spn_secret(
                json.loads(customer_spn_secret)['keyId'],
                json.loads(object_and_app_id)['object_id'],
                graph_token
            )

        return func.HttpResponse(
            json.dumps({"error_message": f"[PART1] Onboarding info retrieval failed, Error: {error}"}),
            status_code=500
        )

    for attempt in range(10):
        try:
            onb_info = await get_aks_onb_info(
                customer_credential,
                subscription_id,
                resource_group_name,
                aks_cluster_name
            )
            if onb_info:
                break

        except Exception as e:
            error = e
            logging.error(json.dumps(
                {f"attempt_{attempt}_error_message": f"[PART2] Onboarding info retrieval failed, Error: {error}"}
            ))
        await asyncio.sleep(10)

    if json.loads(customer_spn_secret)['keyId']:
        await remove_customer_spn_secret(
            json.loads(customer_spn_secret)['keyId'],
            json.loads(object_and_app_id)['object_id'],
            graph_token
        )

    if json.loads(onb_info)['ca_cert'] and json.loads(onb_info)['server'] and json.loads(onb_info)['token']:
        return func.HttpResponse(onb_info, status_code=200)
    else:
        return func.HttpResponse(
            json.dumps({"error_message": f"[PART2] Onboarding info retrieval failed, Error: {error}"}),
            status_code=500
        )
```

This code incorporates `async` and `aiohttp` into all methods and provides a single code snippet for your Azure Function.
