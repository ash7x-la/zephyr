from agents.base_agent import BaseAgent
from utils.extractors import extract_json

class PlannerAgent(BaseAgent):
    async def create_plan(self, user_request):
        prompt = f"""Kamu adalah Tech Lead Agentic.
Diberikan tugas pengembangan: "{user_request}"

TUGASMU:
1. Analisis masalah dan lingkungan user.
2. Jelaskan rencanamu (Implementation Plan) kepada user menggunakan Markdown. Buat penjelasanmu menarik, taktis, dan jelaskan apa yang akan kamu lakukan.
3. Setelah rencana Markdown, wajib lampirkan blok JSON teknis yang berisi cetak biru spesifik.

Format JSON wajib:
```json
{{
    "project_name": "nama_folder_tanpa_spasi",
    "tech_stack": ["..."],
    "files": [{"path": "...", "desc": "..."}],
    "tasks": [{"id": 1, "desc": "...", "worker": "frontend|styling|debugger"}]
}}
```"""
        
        result = await self.client.chat(prompt)
        plan_data = extract_json(result)
        
        if "error" in plan_data or "tasks" not in plan_data:
            plan_data = {
                "project_name": "emergency_project",
                "tech_stack": ["HTML", "CSS"],
                "files": [{"path": "index.html", "desc": "Main UI"}],
                "tasks": [
                    {"id": 1, "desc": "Generate UI HTML", "worker": "frontend"},
                    {"id": 2, "desc": "Generate CSS UI", "worker": "styling"}
                ]
            }
        return plan_data
