import os
import asyncio
from asyncio import subprocess as async_sub
import json
import re
import httpx
from openai import AsyncOpenAI
import google.generativeai as genai
import anthropic
from clients.base_client import BaseClient
from core.config import Config
from core.logger import Logger

class UniversalClient(BaseClient):
    def __init__(self):
        self.active_model = Config.DEFAULT_MODEL
        
        # Initialize OpenRouter (OpenAI Compatible)
        self.openrouter_client = None
        if Config.OPENROUTER_API_KEY:
            self.openrouter_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
            )
        
        # Initialize Gemini
        self.gemini_handler = None
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.gemini_handler = genai.GenerativeModel('gemini-2.0-flash')
            
        # Initialize Anthropic (Optional direct)
        self.anthropic_client = None
        if Config.CLAUDE_API_KEY:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=Config.CLAUDE_API_KEY)

        # Initialize DeepSeek Free (Local Proxy)
        self.deepseek_free_client = None
        if Config.DEEPSEEK_FREE_TOKEN:
            # We use httpx directly for deepseek-free to handle proxy response bugs
            self.free_http_client = httpx.AsyncClient(
                base_url=Config.DEEPSEEK_FREE_URL,
                timeout=httpx.Timeout(240.0, connect=15.0),
                headers={"Authorization": f"Bearer {Config.DEEPSEEK_FREE_TOKEN}"}
            )


    async def chat(self, messages):
        """Non-streaming version for backward compatibility or simple calls."""
        full_text = ""
        async for chunk in self.chat_stream(messages):
            full_text += chunk
        return full_text

    async def chat_stream(self, messages):
        """Asynchronous generator that yields response chunks."""
        model = self.active_model.lower()
        
        if "gemini-cli" in model:
            # Subprocess usually doesn't stream well without TTY, yield once
            yield await self._chat_gemini_cli(messages)
        elif "gemini" in model:
            async for chunk in self._stream_gemini(messages):
                yield chunk
        elif "claude" in model and self.anthropic_client:
            async for chunk in self._stream_claude(messages):
                yield chunk
        elif "deepseek-free" in model:
            async for chunk in self._stream_deepseek_free(messages):
                yield chunk
        else:
            async for chunk in self._stream_openrouter(messages):
                yield chunk

    async def _chat_gemini_cli(self, messages):
        """Implementasi integrasi via CLI Proxy (OpenClaw Standard)."""
        try:
            prompt_data = json.dumps(messages)
            cli_path = os.getenv("GEMINI_CLI_PATH", "gemini")
            
            process = await asyncio.create_subprocess_exec(
                cli_path, "-p", "",
                stdin=async_sub.PIPE,
                stdout=async_sub.PIPE,
                stderr=async_sub.PIPE
            )
            
            stdout, stderr = await process.communicate(input=prompt_data.encode())
            if process.returncode != 0:
                err_msg = stderr.decode() or stdout.decode()
                return f"Error Gemini CLI (Exit {process.returncode}): {err_msg}"
            return stdout.decode().strip()
        except Exception as e:
            return f"Error Gemini CLI Proxy: {str(e)}"

    async def _stream_openrouter(self, messages):
        try:
            if not self.openrouter_client:
                yield "Error: OPENROUTER_API_KEY tidak ditemukan."
                return
                
            stream = await self.openrouter_client.chat.completions.create(
                model=self.active_model,
                messages=messages,
                temperature=0.3,
                stream=True
            )
            sent_thought = False
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    if not sent_thought:
                        yield "<thought>"
                        sent_thought = True
                    yield delta.reasoning_content
                elif delta.content:
                    if sent_thought:
                        yield "</thought>"
                        sent_thought = False
                    yield delta.content
            if sent_thought:
                yield "</thought>"
        except Exception as e:
            yield f"Error OpenRouter Stream: {str(e)}"

    async def _stream_gemini(self, messages):
        try:
            if not self.gemini_handler:
                yield "Error: GEMINI_API_KEY tidak ditemukan."
                return
            
            history = []
            for m in messages[:-1]:
                role = "user" if m["role"] in ["user", "system"] else "model"
                history.append({"role": role, "parts": [m["content"]]})
            
            chat = self.gemini_handler.start_chat(history=history)
            response = await chat.send_message_async(messages[-1]["content"], stream=True)
            async for chunk in response:
                yield chunk.text
        except Exception as e:
            yield f"Error Gemini Stream: {str(e)}"

    async def _stream_claude(self, messages):
        try:
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            other_msgs = [m for m in messages if m["role"] != "system"]
            
            async with self.anthropic_client.messages.stream(
                model=self.active_model,
                max_tokens=4096,
                system=system_msg,
                messages=other_msgs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"Error Claude Stream: {str(e)}"

    async def _stream_deepseek_free(self, messages):
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "stream": True
            }
            
            async with self.free_http_client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    yield f"Error DeepSeek-Free Stream ({response.status_code})"
                    return
                
                line_count = 0
                sent_thought = False
                async for line in response.aiter_lines():
                    line_count += 1
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data:
                                delta = data["choices"][0]["delta"]
                                # reasoning_content is specific to DeepSeek R1 / some OpenRouter models
                                if delta.get("reasoning_content"):
                                    if not sent_thought:
                                        yield "<thought>"
                                        sent_thought = True
                                    yield delta["reasoning_content"]
                                elif delta.get("content"):
                                    if sent_thought:
                                        yield "</thought>"
                                        sent_thought = False
                                    yield delta["content"]
                        except:
                            continue
                
                if line_count == 0:
                    yield "Error: DeepSeek-Free returned an empty stream. This usually means the browser session/token has expired or the context limit was exceeded."
                if sent_thought:
                    yield "</thought>"
        except Exception as e:
            yield f"Error DeepSeek-Free Stream: {str(e)}"
