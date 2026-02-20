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

from flask import request
from flask_login import login_required, current_user
from api.db.services.knowledgebase_service import KnowledgebaseService
from api.db.services.document_service import DocumentService
from api.db.services.user_service import TenantService
from api.db.services.corpus_service import CorpusDatabaseConfigService
from api.utils.api_utils import get_json_result, server_error_response
from api import settings
from rag.nlp import search
import pymysql
import json


@manager.route('/statistics', methods=['GET'])  # noqa: F821
@login_required
def get_corpus_statistics():
    """
    Get corpus statistics for all knowledge bases
    """
    try:
        # Get all knowledge bases for current user
        # In RAGFlow, current_user.id is the tenant_id
        tenant_id = current_user.id

        kbs, _ = KnowledgebaseService.get_by_tenant_ids(
            [tenant_id], current_user.id, 0, 0, "create_time", True, "", None
        )
        
        # Initialize statistics
        document_stats = []
        chunk_stats = []
        entity_stats = []
        graph_node_stats = []

        # Collect statistics for each knowledge base
        for kb in kbs:
            kb_id = kb["id"]
            kb_name = kb["name"]

            # Document count
            doc_count = kb.get("doc_num", 0)
            document_stats.append({
                "kb_id": kb_id,
                "kb_name": kb_name,
                "count": doc_count
            })

            # Chunk count
            chunk_count = kb.get("chunk_num", 0)
            chunk_stats.append({
                "kb_id": kb_id,
                "kb_name": kb_name,
                "count": chunk_count
            })

            # Entity count from knowledge graph
            try:
                entity_count = get_entity_count(tenant_id, kb_id)
                entity_stats.append({
                    "kb_id": kb_id,
                    "kb_name": kb_name,
                    "count": entity_count
                })
            except Exception:
                entity_stats.append({
                    "kb_id": kb_id,
                    "kb_name": kb_name,
                    "count": 0
                })

            # Graph node count from knowledge graph (B: count nodes from merged graph)
            try:
                graph_node_count = get_graph_node_count(tenant_id, kb_id)
                graph_node_stats.append({
                    "kb_id": kb_id,
                    "kb_name": kb_name,
                    "count": graph_node_count
                })
            except Exception:
                graph_node_stats.append({
                    "kb_id": kb_id,
                    "kb_name": kb_name,
                    "count": 0
                })

        # Get medical data counts from database config
        medical_counts = {
            "patient_count": 0,
            "order_count": 0,
            "record_count": 0,
            "exam_count": 0,
            "lab_count": 0
        }
        try:
            db_config = get_database_config_from_storage()
            if db_config:
                medical_counts = get_medical_data_counts(db_config)
        except Exception as e:
            pass

        graph_node_total = sum(item["count"] for item in graph_node_stats)

        return get_json_result(data={
            "patient_count": medical_counts["patient_count"],
            "order_count": medical_counts["order_count"],
            "record_count": medical_counts["record_count"],
            "exam_count": medical_counts["exam_count"],
            "lab_count": medical_counts["lab_count"],
            "document_stats": document_stats,
            "chunk_stats": chunk_stats,
            "entity_stats": entity_stats,
            "graph_node_stats": graph_node_stats,
            "graph_node_total": graph_node_total
        })
    except Exception as e:
        return server_error_response(e)


@manager.route('/database_config', methods=['GET'])  # noqa: F821
@login_required
def get_database_config():
    """
    Get database configuration
    """
    try:
        config = get_database_config_from_storage()
        return get_json_result(data=config or {})
    except Exception as e:
        return server_error_response(e)


@manager.route('/save_database_config', methods=['POST'])  # noqa: F821
@login_required
def save_database_config():
    """
    Save database configuration
    """
    try:
        req = request.json
        save_database_config_to_storage(req)
        return get_json_result(data={"message": "Configuration saved successfully"})
    except Exception as e:
        return server_error_response(e)


@manager.route('/test_connection', methods=['POST'])  # noqa: F821
@login_required
def test_database_connection():
    """
    Test database connection
    """
    try:
        req = request.json
        host = req.get("host")
        port = req.get("port", 3306)
        username = req.get("username")
        password = req.get("password")
        database = req.get("database", "")
        
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database if database else None,
            connect_timeout=5
        )
        connection.close()
        
        return get_json_result(data={"success": True, "message": "Connection successful"})
    except Exception as e:
        return get_json_result(
            data={"success": False, "message": str(e)},
            code=settings.RetCode.OPERATING_ERROR
        )


@manager.route('/database_list', methods=['POST'])  # noqa: F821
@login_required
def get_database_list():
    """
    Get list of databases
    """
    try:
        req = request.json
        host = req.get("host")
        port = req.get("port", 3306)
        username = req.get("username")
        password = req.get("password")
        
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        
        return get_json_result(data={"databases": databases})
    except Exception as e:
        return server_error_response(e)


@manager.route('/table_list', methods=['POST'])  # noqa: F821
@login_required
def get_table_list():
    """
    Get list of tables in a database
    """
    try:
        req = request.json
        host = req.get("host")
        port = req.get("port", 3306)
        username = req.get("username")
        password = req.get("password")
        database = req.get("database")
        
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        
        return get_json_result(data={"tables": tables})
    except Exception as e:
        return server_error_response(e)


@manager.route('/table_fields', methods=['POST'])  # noqa: F821
@login_required
def get_table_fields():
    """
    Get fields of a table
    """
    try:
        req = request.json
        host = req.get("host")
        port = req.get("port", 3306)
        username = req.get("username")
        password = req.get("password")
        database = req.get("database")
        table = req.get("table")
        
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        cursor.execute(f"DESCRIBE `{table}`")
        fields = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        
        return get_json_result(data={"fields": fields})
    except Exception as e:
        return server_error_response(e)


# Helper functions
def get_database_config_from_storage():
    """
    Get database configuration from storage
    """
    # In RAGFlow, current_user.id is the tenant_id
    tenant_id = current_user.id
    return CorpusDatabaseConfigService.get_by_tenant_id(tenant_id)


def save_database_config_to_storage(config):
    """
    Save database configuration to storage
    """
    # In RAGFlow, current_user.id is the tenant_id
    tenant_id = current_user.id
    CorpusDatabaseConfigService.save_config(tenant_id, config)


def get_medical_data_counts(db_config):
    """
    Get counts for all 5 types of medical data from configured database
    Returns: dict with patient_count, order_count, record_count, exam_count, lab_count
    """
    counts = {
        "patient_count": 0,
        "order_count": 0,
        "record_count": 0,
        "exam_count": 0,
        "lab_count": 0
    }

    try:
        connection = pymysql.connect(
            host=db_config.get("host"),
            port=int(db_config.get("port", 3306)),
            user=db_config.get("username"),
            password=db_config.get("password"),
            database=db_config.get("database"),
            connect_timeout=5
        )

        cursor = connection.cursor()

        # Get patient count
        patient_table = db_config.get("patient_table") or db_config.get("patientTable")
        patient_field = db_config.get("patient_field") or db_config.get("patientField")
        if patient_table and patient_field:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT `{patient_field}`) FROM `{patient_table}`")
                counts["patient_count"] = cursor.fetchone()[0]
            except Exception:
                pass

        # Get medical order count
        order_table = db_config.get("order_table") or db_config.get("orderTable")
        order_field = db_config.get("order_field") or db_config.get("orderField")
        if order_table and order_field:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT `{order_field}`) FROM `{order_table}`")
                counts["order_count"] = cursor.fetchone()[0]
            except Exception:
                pass

        # Get medical record count
        record_table = db_config.get("record_table") or db_config.get("recordTable")
        record_field = db_config.get("record_field") or db_config.get("recordField")
        if record_table and record_field:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT `{record_field}`) FROM `{record_table}`")
                counts["record_count"] = cursor.fetchone()[0]
            except Exception:
                pass

        # Get examination report count
        exam_table = db_config.get("exam_table") or db_config.get("examTable")
        exam_field = db_config.get("exam_field") or db_config.get("examField")
        if exam_table and exam_field:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT `{exam_field}`) FROM `{exam_table}`")
                counts["exam_count"] = cursor.fetchone()[0]
            except Exception:
                pass

        # Get lab report count
        lab_table = db_config.get("lab_table") or db_config.get("labTable")
        lab_field = db_config.get("lab_field") or db_config.get("labField")
        if lab_table and lab_field:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT `{lab_field}`) FROM `{lab_table}`")
                counts["lab_count"] = cursor.fetchone()[0]
            except Exception:
                pass

        cursor.close()
        connection.close()
        return counts
    except Exception as e:
        return counts


def get_entity_count(tenant_id, kb_id):
    """Get entity count from knowledge graph (number of entity documents)."""
    try:
        req = {
            "kb_id": [kb_id],
            "knowledge_graph_kwd": ["entity"],
            "size": 0,  # we only need total count
        }
        sres = settings.retriever.search(req, search.index_name(tenant_id), [kb_id])
        return getattr(sres, "total", 0) or 0
    except Exception:
        return 0


def get_graph_node_count(tenant_id, kb_id):
    """Get graph node count for a knowledge base.

    Definition B: count nodes from the merged knowledge graph document
    (knowledge_graph_kwd="graph"), using the `nodes` array length.
    """
    try:
        # Check index exists for this KB first (defensive, but cheap)
        if not settings.docStoreConn.indexExist(search.index_name(tenant_id), kb_id):
            return 0

        req = {
            "kb_id": [kb_id],
            "knowledge_graph_kwd": ["graph"],
            "size": 1,  # only need one merged graph document
        }
        sres = settings.retriever.search(req, search.index_name(tenant_id), [kb_id])
        # For retriever result, ids is usually a list/sequence
        if not getattr(sres, "ids", None):
            return 0
        doc_id = sres.ids[0]
        fields = getattr(sres, "field", {}) or {}
        doc_fields = fields.get(doc_id) or {}
        content = doc_fields.get("content_with_weight")
        if not content:
            return 0

        data = json.loads(content)
        nodes = data.get("nodes") or []
        return len(nodes)
    except Exception:
        return 0

