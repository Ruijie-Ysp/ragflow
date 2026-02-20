#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#


import logging

from flask import request
from flask_login import current_user, login_required
from langfuse import Langfuse

from api.db.db_models import DB
from api.db.services.langfuse_service import TenantLangfuseService
from api.utils.api_utils import get_error_data_result, get_json_result, server_error_response, validate_request


@manager.route("/api_key", methods=["POST", "PUT"])  # noqa: F821
@login_required
@validate_request("secret_key", "public_key", "host")
def set_api_key():
    req = request.get_json()
    secret_key = req.get("secret_key", "")
    public_key = req.get("public_key", "")
    host = req.get("host", "")

    logging.info(f"[LANGFUSE CONFIG] Attempting to save Langfuse config for tenant {current_user.id}, host: {host}")

    if not all([secret_key, public_key, host]):
        logging.error(f"[LANGFUSE CONFIG] Missing required fields")
        return get_error_data_result(message="Missing required fields")

    langfuse_keys = dict(
        tenant_id=current_user.id,
        secret_key=secret_key,
        public_key=public_key,
        host=host,
    )

    # Validate Langfuse connection and credentials
    try:
        logging.info(f"[LANGFUSE CONFIG] Testing connection to Langfuse...")
        langfuse = Langfuse(public_key=langfuse_keys["public_key"], secret_key=langfuse_keys["secret_key"], host=langfuse_keys["host"])
        auth_result = langfuse.auth_check()
        logging.info(f"[LANGFUSE CONFIG] Auth check result: {auth_result}")
        if not auth_result:
            logging.error(f"[LANGFUSE CONFIG] Auth check returned False")
            return get_error_data_result(message="Invalid Langfuse keys")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"[LANGFUSE CONFIG] Connection test failed: {error_msg}", exc_info=True)
        if "Connection refused" in error_msg or "ConnectError" in str(type(e)):
            return get_error_data_result(message=f"Cannot connect to Langfuse host: {host}. Please check the host address and ensure Langfuse is accessible from the RAGFlow container.")
        elif "Unauthorized" in error_msg or "401" in error_msg:
            return get_error_data_result(message="Invalid Langfuse credentials. Please check your Public Key and Secret Key.")
        else:
            return get_error_data_result(message=f"Failed to connect to Langfuse: {error_msg}")

    try:
        langfuse_entry = TenantLangfuseService.filter_by_tenant(tenant_id=current_user.id)
        if not langfuse_entry:
            logging.info(f"[LANGFUSE CONFIG] Creating new Langfuse config entry")
            TenantLangfuseService.save(**langfuse_keys)
        else:
            logging.info(f"[LANGFUSE CONFIG] Updating existing Langfuse config entry")
            TenantLangfuseService.update_by_tenant(tenant_id=current_user.id, langfuse_keys=langfuse_keys)
        logging.info(f"[LANGFUSE CONFIG] Successfully saved Langfuse config")
        return get_json_result(data=langfuse_keys)
    except Exception as e:
        logging.error(f"[LANGFUSE CONFIG] Failed to save to database: {e}", exc_info=True)
        return server_error_response(e)


@manager.route("/api_key", methods=["GET"])  # noqa: F821
@login_required
@validate_request()
def get_api_key():
    langfuse_entry = TenantLangfuseService.filter_by_tenant_with_info(tenant_id=current_user.id)
    if not langfuse_entry:
        return get_json_result(message="Have not record any Langfuse keys.")

    langfuse = Langfuse(public_key=langfuse_entry["public_key"], secret_key=langfuse_entry["secret_key"], host=langfuse_entry["host"])
    try:
        if not langfuse.auth_check():
            return get_error_data_result(message="Invalid Langfuse keys loaded")

        # In Langfuse SDK v3, project info is not available through the SDK
        # We'll just return the basic config without project_id and project_name
        # Users can view their project in the Langfuse UI
    except Exception as e:
        logging.error(f"[LANGFUSE CONFIG] Error checking Langfuse keys: {e}", exc_info=True)
        return get_json_result(message=f"Error from Langfuse: {str(e)}")

    return get_json_result(data=langfuse_entry)


@manager.route("/api_key", methods=["DELETE"])  # noqa: F821
@login_required
@validate_request()
def delete_api_key():
    langfuse_entry = TenantLangfuseService.filter_by_tenant(tenant_id=current_user.id)
    if not langfuse_entry:
        return get_json_result(message="Have not record any Langfuse keys.")

    with DB.atomic():
        try:
            TenantLangfuseService.delete_model(langfuse_entry)
            return get_json_result(data=True)
        except Exception as e:
            return server_error_response(e)
