#!/usr/bin/env python
import argparse
import logging
import os
import requests
from domino import Domino
from utils import read_config as read_config
from utils import parse_evn_var as parse_evn_var
from utils import parse_args as parse_args
import json

env_variables = {}


def get_owner_id(domino_url, user_api_key):
    logging.info(f"Getting Owner Id for the api key {user_api_key}")
    url = f"https://{domino_url}/v4/users/self"
    headers = {"X-Domino-Api-Key": user_api_key}
    response = requests.get(url, headers=headers)
    return response.json()


def get_project_id(domino_url, project_name, user_api_key):
    owner_id = get_owner_id(domino_url, user_api_key).get("id")
    logging.info(f"Getting project id for owner id: {owner_id}")
    url = f"https://{domino_url}/v4/projects"
    params = {"name": project_name, "ownerId": owner_id}
    headers = {"X-Domino-Api-Key": user_api_key}
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_hardware_tier_id(domino_url, user_api_key, hardware_tier_name):
    owner_id = get_owner_id(domino_url, user_api_key).get("id")
    logging.info(f"Getting hardware tier id for owner id: {owner_id}")
    url = f"https://{domino_url}/v4/hardwareTier"
    headers = {"X-Domino-Api-Key": user_api_key}
    hardware_tier_list = requests.get(url, headers=headers).json()
    tier_id = next(
        (
            tier["id"]
            for tier in hardware_tier_list.get("hardwareTiers")
            if tier["name"] == hardware_tier_name
        ),
        None,
    )
    return tier_id


def job_start(
    start_job_url,
    project_id,
    api_key,
    command,
    branch_name,
    hardware_tier,
    environment_id,
):


    headers = {
        'X-Domino-Api-Key': api_key, #api key
        'Content-Type': 'application/json'
    }

    payload = json.dumps({
        "projectId": project_id,
        "runCommand": command, 
        "mainRepoGitRef": {
        "refType": "branches",
        "value": branch_name,
        "hardwareTier": hardware_tier,
        "environmentId": environment_id
        }
    }
    )

    response = requests.request("POST", start_job_url, headers=headers, data=payload)
    print("job id :: ", response)


def job_stop(domino, job_id):
    domino.job_stop(job_id)


def main():
    inputs = parse_args()
    parse_evn_var(env_variables,inputs.DOMINO_ENV)

    logging.info(env_variables["DOMINO_PROJECT_NAME"])
    logging.info(inputs.DOMINO_USER_API_KEY)
    logging.info(env_variables["DOMINO_API_HOST"])
    domino_url = env_variables["DOMINO_API_HOST"]
    start_job_url = f"https://{domino_url}/api/jobs/v1/jobs"

    project = f"{env_variables['DOMINO_PROJECT_OWNER']}/{env_variables['DOMINO_PROJECT_NAME']}"
    domino = Domino(
        project,
        api_key=inputs.DOMINO_USER_API_KEY,
        host=f"https://{env_variables['DOMINO_API_HOST']}",
    )

    job_start(
            start_job_url,
            get_project_id(domino_url, env_variables["DOMINO_PROJECT_NAME"], inputs.DOMINO_USER_API_KEY),
            inputs.DOMINO_USER_API_KEY,
            env_variables["DOMINO_DATA_PREP_SCRIPT"],
            inputs.DOMINO_ENV.lower(),
            env_variables["DOMINO_HARDWARE_TIER"],
            env_variables["DOMINO_ENVIRONMENT_ID"],
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
