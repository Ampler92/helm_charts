import os
import sys
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

artifact_id = 16024
repo_path = None
artifact_name = "jindra69"
artifact_version = None
dasy_namespace = "com.commerzbank.comcd"
customer_coria = "01-49-81"
pr_id = "196"

def make_request(url, method, headers, payload=None, verify=False):
    try:
        response = requests.request(method, url, headers=headers, json=payload, verify=verify)

        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            data = None

        if 200 <= response.status_code < 300:
            return data
        elif response.status_code == 403:
            logging.error(f"Request failed due to permissions: {data}")
            raise requests.exceptions.RequestException(data)
        else:
            error = f'Request failed: {data.get("status", response.status_code)} - ' \
                    f'{data.get("message", ">")}, ' \
                    f'{data.get("reason", response.content)}'
            raise requests.exceptions.RequestException(error)

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error occurred: {e}")
        raise

def upload_to_dasy(artifact_name_param, dasy_namespace_param, customer_coria_param, artifact_version_param,
                   repo_path_param):
    url = "https://comcd-dasy-service-dev.apps.cloud.internal/api/dasy/artifacts/repos"

    payload = {
        "name": artifact_name_param,
        "namespace": dasy_namespace_param,
        "productCoria": customer_coria_param,
        "reference": repo_path_param,
        "targetRepository": "dasy",
        "version": artifact_version_param,
        "repoPath": repo_path_param
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ZGFzeS11c2VyOnFuZmw2OCVjbmZm'
    }

    logging.info(f"Uploading artifact: '{payload}'")

    data = make_request(url, "POST", headers, payload)

    response_artifact_id = data.get("id")
    logging.info(f"Artifact with ID '{response_artifact_id}' has been successfully uploaded!")

    return response_artifact_id

def download_from_dasy(artifact_id_param, save_path_param):
    url = f"https://comcd-dasy-service-dev.apps.cloud.internal/api/dasy/artifacts/{artifact_id_param}/download"

    headers = {
        'Content-Type': 'application/octet-stream',
        'Authorization': 'Basic ZGFzeS11c2VyOnFuZmw2OCVjbmZm'
    }

    logging.info(f"Downloading artifact: '{artifact_id_param}'")

    make_request(url, "GET", headers, verify=False)

    with open(save_path_param, mode="wb") as file:
        file.write(response.content)

try:
    if artifact_id is not None:
        pass
    elif repo_path is not None and artifact_version is not None:
        artifact_id = upload_to_dasy(artifact_name, dasy_namespace, customer_coria, artifact_version, repo_path)
    else:
        raise ValueError("Either 'artifactId' or 'repoPath and artifactVersion' has to be provided!")

    file_path = os.path.join(os.getcwd(), 'artifact.zip')
    download_from_dasy(artifact_id, file_path)
    logging.info(f"Artifact has been successfully downloaded to: {file_path}")
    sys.exit(0)
except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")
    sys.exit(1)