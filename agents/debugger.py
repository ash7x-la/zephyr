from agents.base_agent import BaseAgent
from utils.extractors import extract_code

class DebuggerWorker(BaseAgent):
    async def work(self, code, error_msg):
        prompt = (
            f"Analisa dan perbaiki error ini: {error_msg}\n"
            f"Target Kode: \n```\n{code}\n```\n"
            f"Berikan RESULT kode PERBAIKAN di dalam codeblock."
        )
        response = await self.client.chat(prompt)
        return extract_code(response)
