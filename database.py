"""
EY Incubator – Supabase Database Client
=========================================
Handles all persistent storage to Supabase:
- Company and Sector hierarchy
- Uploaded Reports metadata
- Row-level report raw & classified data
- Bot Code Configurations for tracking changes
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: Supabase URL or Key is missing from .env")

class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # --- Hierarchy ---
    def get_or_create_company(self, name: str) -> str:
        """Fetch existing company by name or create a new one."""
        resp = self.supabase.table("companies").select("id").eq("name", name).execute()
        if resp.data:
            return resp.data[0]["id"]
        
        # Create
        resp = self.supabase.table("companies").insert({"name": name}).execute()
        return resp.data[0]["id"]

    def get_or_create_sector(self, company_id: str, name: str) -> str:
        """Fetch existing sector by name in a company or create a new one."""
        resp = self.supabase.table("sectors").select("id").eq("company_id", company_id).eq("name", name).execute()
        if resp.data:
            return resp.data[0]["id"]
        
        # Create
        resp = self.supabase.table("sectors").insert({"company_id": company_id, "name": name}).execute()
        return resp.data[0]["id"]

    # --- Reports ---
    def create_report(self, sector_id: str, filename: str) -> str:
        """Create a new report upload session."""
        resp = self.supabase.table("reports").insert({
            "sector_id": sector_id,
            "filename": filename,
            "status": "processing"
        }).execute()
        return resp.data[0]["id"]

    def complete_report(self, report_id: str):
        """Mark a report as successfully processed."""
        self.supabase.table("reports").update({"status": "completed"}).eq("id", report_id).execute()

    def fail_report(self, report_id: str):
        """Mark a report processing as failed."""
        self.supabase.table("reports").update({"status": "failed"}).eq("id", report_id).execute()

    # --- Data ---
    def insert_report_data(self, report_id: str, raw_data_list: list[dict], classified_data_list: list[dict]):
        """Bulk insert the row-level data and LLM classifications."""
        if len(raw_data_list) != len(classified_data_list):
            raise ValueError("Mismatched data lengths between raw and classified.")

        payloads = []
        for raw, classified in zip(raw_data_list, classified_data_list):
            payloads.append({
                "report_id": report_id,
                "raw_data": raw,
                "classified_data": classified
            })

        # Insert in batches if very large, but Supabase handles thousands easily
        # We can chunk to be safe
        chunk_size = 500
        for i in range(0, len(payloads), chunk_size):
            chunk = payloads[i:i + chunk_size]
            self.supabase.table("report_data").insert(chunk).execute()

    # --- Bot Configurations ---
    def save_bot_configuration(self, version_name: str, system_prompt: str, is_active: bool = True, sector_id: str = None) -> str:
        """Save a new version of the bot configuration, tracking code changes."""
        
        # If becoming active, deactivate others for this sector
        if is_active:
            if sector_id:
                self.supabase.table("bot_configurations").update({"is_active": False}).eq("sector_id", sector_id).execute()
            else:
                self.supabase.table("bot_configurations").update({"is_active": False}).is_("sector_id", "null").execute()

        payload = {
            "version_name": version_name,
            "system_prompt": system_prompt,
            "is_active": is_active
        }
        if sector_id:
            payload["sector_id"] = sector_id

        resp = self.supabase.table("bot_configurations").insert(payload).execute()
        return resp.data[0]["id"]
        
    def get_active_bot_configuration(self, sector_id: str = None) -> dict:
        """Fetch the currently active bot prompt configuration."""
        query = self.supabase.table("bot_configurations").select("*").eq("is_active", True)
        if sector_id:
             query = query.eq("sector_id", sector_id)
        else:
             query = query.is_("sector_id", "null")
             
        resp = query.execute()
        if resp.data:
            return resp.data[0]
        return None

if __name__ == "__main__":
    print("Testing Supabase connection (requires tables to be created first!)")
    db = Database()
    print("Successfully instantiated Database client.")
