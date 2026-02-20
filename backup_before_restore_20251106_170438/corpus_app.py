#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
from __future__ import annotations

import json
import re
from typing import Dict, Any, List, Tuple

import pymysql
from flask import request
from flask_login import login_required, current_user

from api import settings
from api.db.services.knowledgebase_service import KnowledgebaseService
from api.db.services.user_service import TenantService
from api.utils.api_utils import (
    get_json_result,
    get_data_error_result,
    server_error_response,
    validate_request,
)
from rag.nlp import search
from rag.utils.redis_conn import REDIS_CONN

# NOTE: "manager" blueprint is injected by api/apps/__init__.py during import


def _mask_password(pwd: str | None) -> str:
    if not pwd:
        return ""
    return "*" * 8


def _validate_identifier(name: str) -> bool:
    # Only allow simple MySQL identifiers: letters, digits and underscore
    return bool(re.fullmatch(r"[A-Za-z0-9_]+", name or ""))


def _mysql_connect(conf: Dict[str, Any]):
    return pymysql.connect(
        host=conf.get("host", "127.0.0.1"),
        port=int(conf.get("port", 3306)),
        user=conf.get("user", "root"),
        password=conf.get("password", ""),
        database=conf.get("database", None),
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
    )


def _redis_key(uid: str) -> str:
    return f"patient_db_config:{uid}"


@manager.route('/literature_stats', methods=['GET'])  # noqa: F821
@login_required
def literature_stats():
    try:
        tenants = TenantService.get_joined_tenants_by_user_id(current_user.id)
        tenant_ids = [m["tenant_id"] for m in tenants]
        kbs, _ = KnowledgebaseService.get_by_tenant_ids(
            tenant_ids, current_user.id, 0, 0, "create_time", True, "", None
        )
        items = [
            {"kb_id": kb["id"], "kb_name": kb["name"], "count": int(kb.get("doc_num", 0))}
            for kb in kbs
        ]
        total = sum(x["count"] for x in items)
        return get_json_result(data={"total": total, "items": items})
    except Exception as e:
        return server_error_response(e)


@manager.route('/vector_stats', methods=['GET'])  # noqa: F821
@login_required
def vector_stats():
    try:
        tenants = TenantService.get_joined_tenants_by_user_id(current_user.id)
        tenant_ids = [m["tenant_id"] for m in tenants]
        kbs, _ = KnowledgebaseService.get_by_tenant_ids(
            tenant_ids, current_user.id, 0, 0, "create_time", True, "", None
        )
        items = [
            {"kb_id": kb["id"], "kb_name": kb["name"], "count": int(kb.get("chunk_num", 0))}
            for kb in kbs
        ]
        total = sum(x["count"] for x in items)
        return get_json_result(data={"total": total, "items": items})
    except Exception as e:
        return server_error_response(e)


@manager.route('/kg_stats', methods=['GET'])  # noqa: F821
@login_required
def kg_stats():
    try:
        tenants = TenantService.get_joined_tenants_by_user_id(current_user.id)
        tenant_ids = [m["tenant_id"] for m in tenants]
        kbs, _ = KnowledgebaseService.get_by_tenant_ids(
            tenant_ids, current_user.id, 0, 0, "create_time", True, "", None
        )

        items: List[Dict[str, Any]] = []
        for kb in kbs:
            kb_id = kb["id"]
            _, kb_obj = KnowledgebaseService.get_by_id(kb_id)
            # Skip if index not exist
            if not settings.docStoreConn.indexExist(search.index_name(kb_obj.tenant_id), kb_id):
                items.append({"kb_id": kb_id, "kb_name": kb["name"], "count": 0})
                continue

            req = {"kb_id": [kb_id], "knowledge_graph_kwd": ["graph"]}
            sres = settings.retriever.search(req, search.index_name(kb_obj.tenant_id), [kb_id])
            count = 0
            if len(sres.ids):
                try:
                    doc_id = sres.ids[0]
                    content_json = json.loads(sres.field[doc_id]["content_with_weight"])  # type: ignore
                    nodes = content_json.get("nodes", [])
                    count = len(nodes)
                except Exception:
                    count = 0
            items.append({"kb_id": kb_id, "kb_name": kb["name"], "count": count})
        total = sum(x["count"] for x in items)
        return get_json_result(data={"total": total, "items": items})
    except Exception as e:
        return server_error_response(e)


@manager.route('/patient/config', methods=['GET'])  # noqa: F821
@login_required
def get_patient_db_config():
    try:
        raw = REDIS_CONN.get(_redis_key(current_user.id)) or b"{}"
        conf = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
        if conf.get("password"):
            conf["password"] = ""  # never expose password
        return get_json_result(data=conf)
    except Exception as e:
        return server_error_response(e)


@manager.route('/patient/config', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user")
def set_patient_db_config():
    try:
        req = request.json or {}
        # Keep previous password if empty
        cur_raw = REDIS_CONN.get(_redis_key(current_user.id)) or b"{}"
        cur_conf = json.loads(cur_raw if isinstance(cur_raw, str) else cur_raw.decode("utf-8"))
        password = req.get("password")
        if password in (None, ""):
            req["password"] = cur_conf.get("password", "")
        # Persist
        REDIS_CONN.set(_redis_key(current_user.id), json.dumps(req))
        data = {**req}
        data["password"] = ""
        return get_json_result(data=data)
    except Exception as e:
        return server_error_response(e)


@manager.route('/patient/test', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user")
def test_mysql_connection():
    try:
        req = request.json or {}
        conn = _mysql_connect(req)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                row = cur.fetchone()
        finally:
            conn.close()
        return get_json_result(data={"ok": True, "result": row})
    except Exception as e:
        return get_data_error_result(message=f"Connect failed: {e}")


@manager.route('/patient/list_databases', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user")
def list_databases():
    try:
        req = request.json or {}
        conn = _mysql_connect({k: req.get(k) for k in ["host", "port", "user", "password"]})
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW DATABASES")
                rows = cur.fetchall() or []
            dbs = [v for row in rows for v in row.values()]
        finally:
            conn.close()
        return get_json_result(data=dbs)
    except Exception as e:
        return get_data_error_result(message=f"List databases failed: {e}")


@manager.route('/patient/list_tables', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user", "database")
def list_tables():
    try:
        req = request.json or {}
        conn = _mysql_connect(req)
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                rows = cur.fetchall() or []
            tables = [v for row in rows for v in row.values()]
        finally:
            conn.close()
        return get_json_result(data=tables)
    except Exception as e:
        return get_data_error_result(message=f"List tables failed: {e}")


@manager.route('/patient/list_fields', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user", "database", "table")
def list_fields():
    try:
        req = request.json or {}
        table = req.get("table", "")
        if not _validate_identifier(table):
            return get_data_error_result(message="Invalid table name")
        conn = _mysql_connect(req)
        try:
            with conn.cursor() as cur:
                cur.execute(f"SHOW COLUMNS FROM `{table}`")
                rows = cur.fetchall() or []
            fields = [row.get("Field") or list(row.values())[0] for row in rows]
        finally:
            conn.close()
        return get_json_result(data=fields)
    except Exception as e:
        return get_data_error_result(message=f"List fields failed: {e}")


@manager.route('/patient/count', methods=['POST'])  # noqa: F821
@login_required
@validate_request("host", "port", "user", "database", "table", "field")
def patient_count():
    try:
        req = request.json or {}
        table = req.get("table", "")
        field = req.get("field", "")
        if not _validate_identifier(table) or not _validate_identifier(field):
            return get_data_error_result(message="Invalid table or field name")
        conn = _mysql_connect(req)
        try:
            with conn.cursor() as cur:
                sql = f"SELECT COUNT(DISTINCT `{field}`) AS cnt FROM `{table}` WHERE `{field}` IS NOT NULL AND `{field}`<>''"
                cur.execute(sql)
                row = cur.fetchone() or {"cnt": 0}
                cnt = int(row.get("cnt", 0))
        finally:
            conn.close()
        # Optionally persist chosen db/table/field into redis saved config
        raw = REDIS_CONN.get(_redis_key(current_user.id)) or b"{}"
        saved = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
        saved.update({
            "host": req.get("host"),
            "port": req.get("port"),
            "user": req.get("user"),
            "password": req.get("password", saved.get("password", "")),
            "database": req.get("database"),
            "table": req.get("table"),
            "field": req.get("field"),
        })
        REDIS_CONN.set(_redis_key(current_user.id), json.dumps(saved))
        return get_json_result(data={
            "count": cnt,
            "config": {k: saved.get(k) for k in ["host", "port", "database", "table", "field"]},
        })
    except Exception as e:
        return get_data_error_result(message=f"Count failed: {e}")

