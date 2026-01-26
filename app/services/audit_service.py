from app.core.supabase import get_supabase_admin
from typing import Any, Optional
from datetime import datetime

class AuditService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def log_action(
        self, 
        user_id: Optional[str], 
        action: str, 
        table_name: Optional[str] = None, 
        record_id: Optional[str] = None, 
        old_data: Any = None, 
        new_data: Any = None,
        ip_address: Optional[str] = None
    ):
        """Logs a critical action to the audit_logs table"""
        try:
            self.supabase.table("audit_logs").insert({
                "user_id": user_id,
                "action": action,
                "table_name": table_name,
                "record_id": record_id,
                "old_data": old_data,
                "new_data": new_data,
                "ip_address": ip_address
            }).execute()
        except Exception as e:
            # Fallback to local logging if DB logging fails
            print(f"FAILED TO LOG AUDIT: {e}")

audit_service = AuditService()
