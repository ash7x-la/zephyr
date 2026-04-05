import re
import json

def extract_code(text):
    pattern = re.compile(r'```(?:\w+\n)?(.*?)```', re.DOTALL)
    matches = pattern.findall(text)
    if matches:
        return "\n\n".join(matches)
    return text.strip()

def extract_json(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception as e:
        return {"error": str(e), "raw": text}
