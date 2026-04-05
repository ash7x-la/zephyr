import os
import asyncio
from asyncio import subprocess as async_sub
import json
import re
import httpx
from clients.base_client import BaseClient
from core.config import Config
from core.logger import Logger

class UniversalClient(BaseClient):
    def __init__(self):
        self.active_model = Config.DEFAULT_MODEL
        
        # Initialize Shared HTTP Client
        # We use a single persistent client for efficiency and connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=20.0),
            headers={"User-Agent": "Zephyr-Agent-Assistant/1.0"}
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
            async for chunk in self._stream_gemini_http(messages):
                yield chunk
        elif "claude" in model:
            async for chunk in self._stream_claude_http(messages):
                yield chunk
        elif "deepseek-free" in model:
            async for chunk in self._stream_deepseek_free(messages):
                yield chunk
        else:
            async for chunk in self._stream_openai_compatible(messages, "https://openrouter.ai/api/v1", Config.OPENROUTER_API_KEY):
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

    async def _stream_openai_compatible(self, messages, base_url, api_key):
        """Implementasi OpenAI SDK secara manual menggunakan raw HTTP streams."""
        try:
            if not api_key:
                yield "Error: API_KEY tidak ditemukan untuk model ini."
                return
                
            payload = {
                "model": self.active_model,
                "messages": messages,
                "temperature": 0.3,
                "stream": True
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/ash7x-la/zephyr",
                "X-Title": "Zephyr Agent"
            }
            
            async with self.http_client.stream("POST", f"{base_url}/chat/completions", json=payload, headers=headers) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield f"Error API ({response.status_code}): {err_body.decode()}"
                    return
                
                sent_thought = False
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            
                            # Support R1-style reasoning_content
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
                
                if sent_thought:
                    yield "</thought>"
        except Exception as e:
            yield f"Error OpenAI Stream: {str(e)}"

    async def _stream_gemini_http(self, messages):
        """Implementasi Gemini API secara manual tanpa Google SDK."""
        try:
            if not Config.GEMINI_API_KEY:
                yield "Error: GEMINI_API_KEY tidak ditemukan."
                return
            
            # Convert OpenAI format to Gemini format
            contents = []
            for m in messages:
                role = "user" if m["role"] in ["user", "system"] else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.active_model}:streamGenerateContent?alt=sse&key={Config.GEMINI_API_KEY}"
            payload = {"contents": contents}
            
            async with self.http_client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield f"Error Gemini ({response.status_code}): {err_body.decode()}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            text = data["candidates"][0]["content"]["parts"][0].get("text", "")
                            if text:
                                yield text
                        except:
                            continue
        except Exception as e:
            yield f"Error Gemini Stream: {str(e)}"

    async def _stream_claude_http(self, messages):
        """Implementasi Anthropic API secara manual tanpa SDK."""
        try:
            if not Config.CLAUDE_API_KEY:
                yield "Error: CLAUDE_API_KEY tidak ditemukan."
                return
            
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            other_msgs = [m for m in messages if m["role"] != "system"]
            
            payload = {
                "model": self.active_model,
                "max_tokens": 4096,
                "messages": other_msgs,
                "system": system_msg,
                "stream": True
            }
            
            headers = {
                "x-api-key": Config.CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            url = "https://api.anthropic.com/v1/messages"
            
            async with self.http_client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield f"Error Claude ({response.status_code}): {err_body.decode()}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data["type"] == "content_block_delta":
                                yield data["delta"]["text"]
                        except:
                            continue
        except Exception as e:
            yield f"Error Claude Stream: {str(e)}"

    async def _stream_deepseek_free(self, messages):
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "stream": True
            }
            
            # Use shared client for deepseek-free
            headers = {"Authorization": f"Bearer {Config.DEEPSEEK_FREE_TOKEN}"}
            async with self.http_client.stream("POST", f"{Config.DEEPSEEK_FREE_URL}/chat/completions", json=payload, headers=headers) as response:
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
