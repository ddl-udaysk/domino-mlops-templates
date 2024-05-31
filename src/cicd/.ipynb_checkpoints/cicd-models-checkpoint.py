#!/usr/bin/env python
import argparse, os
import logging
from domino import Domino
import requests
from utils import read_config as read_config
from utils import parse_evn_var as parse_evn_var
from utils import parse_args as parse_args

env_variables = {}

def list_environments(domino):
    all_available_environments = domino.environments_list()
    global_environments = list(
        filter(
            lambda x: x.get("visibility") == "Global",
            all_available_environments["data"],
        )
    )
    print(
        "This Domino deployment has \
         {} global environments".format(
            len(global_environments)
        )
    )


def list_models(domino):
    logging.info(f"{domino.models_list()}")


def model_exist(domino, model_name):
    models = domino.models_list()
    for i in models["data"]:
        if i["name"] == model_name:
            return True


def get_owner_id(domino_url, user_api_key):
    logging.info(f"Getting Owner Id for the api key {user_api_key}")
    url = f"https://{domino_url}/v4/users/self"
    headers = {"X-Domino-Api-Key": user_api_key}
    response = requests.get(url, headers=headers)
    return response.json()


def get_user_id(domino, username_or_email):
    userid = domino.get_user_id(username_or_email)
    return userid


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


def model_start(
    start_job_url,
    project_id,
    model_name,
    model_desc,
    model_file,
    model_func,
    model_registered_name,
    model_registered_version,
    hardware_tier_id,
    environment_id,
    user_api_key,
    model_type,
    model_target_stage,
    model_reviewer,
    model_env,
    isAsync=False,
):
    print("model_start")
    payload = {
    "projectId": project_id,
    "name": model_name+"_"+model_env,
    "description": model_desc,
    "registeredModelName": model_registered_name,
    "registeredModelVersion": model_registered_version,
    "replicaCount": 1,
    "hardwareTierId": hardware_tier_id,
    "environmentId": environment_id,
    "environmentVariables": [],
    "logHttpRequestResponse": True,
    "isAsync": False,
    "strictNodeAntiAffinity": False
    }

    headers = {"X-Domino-Api-Key": user_api_key}
    response = requests.post(start_job_url, headers=headers, json=payload)
    print(response.text)


def create_model(domino, model_name, model_desc, model_file, model_func, model_ce):
    # Publish a brand new model
    published_model = domino.model_publish(
        file=model_file,
        function=model_func,
        environment_id=model_ce,
        name=model_name,
        description=model_desc,
    )
    published_model_id = published_model.get("data", {}).get("_id")
    logging.info("Model {} published, details below:".format(published_model_id))
    logging.info(published_model)


def publish_revision(
    domino,
    domino_url,
    user_api_key,
    project_id,
    environment_id,
    model_name,
    model_desc,
    model_file,
    model_func,
    model_registered_name,
    model_registered_version,
    model_type,
    target_stage,
    reviewer,
    model_env,
):
    models = domino.models_list()
    for i in models["data"]:
        if i["name"] == model_name:
            published_model_id = i["id"]

    payload = {
    "description": model_desc,
    "projectId": project_id,
    "environmentId": environment_id,
    "registeredModelName": model_registered_name,
    "registeredModelVersion": model_registered_version,
    "logHttpRequestResponse": True
    }


    headers = {"X-Domino-Api-Key": user_api_key}
    response = requests.post(f"https://{domino_url}/v1/models/{published_model_id}/versions", headers=headers, json=payload)
""" 
    if model_type == EXPERIMENT_MANAGEMENT_MODEL_TYPE:
        review_model(
            domino,
            domino_url,
            user_api_key,
            model_name,
            another_model_version,
            target_stage,
            reviewer,
        ) """


def review_model(
    domino, domino_url, user_api_key, model_name, model_version, target_stage, reviewer
):

    logging.info(f"review model with name: {model_name}")
    url = f"https://{domino_url}/api/registeredmodels/v1/{model_name}/versions/{model_version}/reviews"

    headers = {"X-Domino-Api-Key": user_api_key}
    reviewer_id = get_user_id(domino, reviewer)

    payload = {
        "targetStage": target_stage,
        "reviewers": [{"userId": reviewer_id}],
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.text)


EXPERIMENT_MANAGEMENT_MODEL_TYPE = "registry"
REGULAR_MODEL_TYPE = "regular"


def main():
    inputs = parse_args()
    parse_evn_var(env_variables,inputs.DOMINO_ENV)
    logging.info(env_variables["DOMINO_MODEL_NAME"])

    start_model_url = f"https://{env_variables['DOMINO_API_HOST']}/v1/models"
    domino_url = env_variables["DOMINO_API_HOST"]
    project = env_variables["DOMINO_PROJECT_OWNER"] + "/" + env_variables["DOMINO_PROJECT_NAME"]
    user_api_key = inputs.DOMINO_USER_API_KEY

    project_id = get_project_id(domino_url, env_variables["DOMINO_PROJECT_NAME"], user_api_key)
    print(project_id[0].get("id"))

    domino = Domino(
        project,
        api_key=inputs.DOMINO_USER_API_KEY,
        host=f"https://{env_variables['DOMINO_API_HOST']}",
    )

    hardware_tier_id = get_hardware_tier_id(domino_url, user_api_key, env_variables["DOMINO_HARDWARE_TIER_NAME"])
    if env_variables["DOMINO_MODEL_OP"] == "list":
        list_models(domino)
    elif env_variables["DOMINO_MODEL_OP"] == "create":
        model_start(
            start_model_url,
            project_id[0].get("id"),
            env_variables["DOMINO_MODEL_NAME"],
            env_variables["DOMINO_MODEL_DESC"],
            env_variables["DOMINO_MODEL_FILE"],
            env_variables["DOMINO_MODEL_FUNC"],
            env_variables["DOMINO_REGISTERED_MODEL_NAME"],
            env_variables["DOMINO_REGISTERED_MODEL_VERSION"],
            hardware_tier_id,
            env_variables["DOMINO_ENVIRONMENT_ID"],
            inputs.DOMINO_USER_API_KEY,
            env_variables["DOMINO_MODEL_TYPE"],
            env_variables["DOMINO_TARGET_STAGE"],
            env_variables["DOMINO_REVIEWER"],
            inputs.DOMINO_ENV,
        )
    elif env_variables["DOMINO_MODEL_OP"] == "update":
        publish_revision(
            domino,
            domino_url,
            user_api_key,
            project_id[0].get("id"),
            env_variables["DOMINO_ENVIRONMENT_ID"],
            env_variables["DOMINO_MODEL_NAME"],
            env_variables["DOMINO_MODEL_DESC"],
            env_variables["DOMINO_MODEL_FILE"],
            env_variables["DOMINO_MODEL_FUNC"],
            env_variables["DOMINO_REGISTERED_MODEL_NAME"],
            env_variables["DOMINO_REGISTERED_MODEL_VERSION"],
            env_variables["DOMINO_MODEL_TYPE"],
            env_variables["DOMINO_TARGET_STAGE"],
            env_variables["DOMINO_REVIEWER"],
            inputs.DOMINO_ENV,
        )

if __name__ == "__main__":
    main()
