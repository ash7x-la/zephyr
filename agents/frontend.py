from agents.base_agent import BaseAgent
from utils.extractors import extract_code

class FrontendWorker(BaseAgent):
    async def work(self, task_desc, context=""):
        prompt = (
            f"KERJAKAN TUGAS MENGGUNAKAN HTML/JS: {task_desc}\n"
            f"Konteks Tambahan Singkat: {context}\n"
            f"Berikan RESULT hanya berupa RAW Code di dalam teks codeblock ```html ... ``` saja."
        )
        response = await self.client.chat(prompt)
        return extract_code(response)
