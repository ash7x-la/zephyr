from agents.base_agent import BaseAgent
from utils.extractors import extract_code

class StylingWorker(BaseAgent):
    async def work(self, task_desc, html_code=""):
        prompt = (
            f"KERJAKAN TUGAS CSS: {task_desc}\n"
            f"HTML saat ini: \n```html\n{html_code}\n```\n"
            f"Berikan RESULT hanya berupa RAW CSS Code di dalam codeblock ```css ... ```."
        )
        response = await self.client.chat(prompt)
        return extract_code(response)
