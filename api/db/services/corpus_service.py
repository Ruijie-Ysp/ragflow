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

from api.db import StatusEnum
from api.db.db_models import DB, CorpusDatabaseConfig
from api.db.services.common_service import CommonService
from api.utils import get_uuid


class CorpusDatabaseConfigService(CommonService):
    model = CorpusDatabaseConfig

    @classmethod
    @DB.connection_context()
    def get_by_tenant_id(cls, tenant_id):
        """Get database configuration by tenant ID"""
        try:
            config = cls.model.select().where(
                (cls.model.tenant_id == tenant_id) &
                (cls.model.status == StatusEnum.VALID.value)
            ).get()
            return config.to_dict()
        except Exception:
            return None

    @classmethod
    @DB.connection_context()
    def save_config(cls, tenant_id, config_data):
        """Save or update database configuration with 5 medical data types"""
        try:
            # Check if config exists
            existing = cls.model.select().where(
                (cls.model.tenant_id == tenant_id) &
                (cls.model.status == StatusEnum.VALID.value)
            ).first()

            update_data = {
                "host": config_data.get("host"),
                "port": config_data.get("port", 3306),
                "username": config_data.get("username"),
                "password": config_data.get("password"),
                "database": config_data.get("database"),
                # Patient data
                "patient_table": config_data.get("patientTable") or config_data.get("patient_table"),
                "patient_field": config_data.get("patientField") or config_data.get("patient_field"),
                # Medical order data
                "order_table": config_data.get("orderTable") or config_data.get("order_table"),
                "order_field": config_data.get("orderField") or config_data.get("order_field"),
                # Medical record data
                "record_table": config_data.get("recordTable") or config_data.get("record_table"),
                "record_field": config_data.get("recordField") or config_data.get("record_field"),
                # Examination report data
                "exam_table": config_data.get("examTable") or config_data.get("exam_table"),
                "exam_field": config_data.get("examField") or config_data.get("exam_field"),
                # Lab report data
                "lab_table": config_data.get("labTable") or config_data.get("lab_table"),
                "lab_field": config_data.get("labField") or config_data.get("lab_field"),
            }

            if existing:
                # Update existing config
                cls.model.update(**update_data).where(cls.model.id == existing.id).execute()
                return existing.id
            else:
                # Create new config
                config_id = get_uuid()
                update_data["id"] = config_id
                update_data["tenant_id"] = tenant_id
                cls.model.create(**update_data)
                return config_id
        except Exception as e:
            raise e

