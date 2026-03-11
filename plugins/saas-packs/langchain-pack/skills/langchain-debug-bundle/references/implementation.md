# LangChain Debug Bundle - Detailed Implementation

## Environment Collection

```python
import sys, platform, subprocess

def collect_environment():
    info = {"python_version": sys.version, "platform": platform.platform(), "packages": {}}
    packages = ["langchain", "langchain-core", "langchain-community", "langchain-openai", "langchain-anthropic", "openai", "anthropic"]
    for pkg in packages:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", pkg], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    info["packages"][pkg] = line.split(":")[1].strip()
        except:
            info["packages"][pkg] = "not installed"
    return info
```

## Debug Callback

```python
from langchain_core.callbacks import BaseCallbackHandler
from datetime import datetime

class DebugCallback(BaseCallbackHandler):
    def __init__(self):
        self.logs = []

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.logs.append({"event": "llm_start", "time": datetime.now().isoformat(), "prompts": prompts})

    def on_llm_end(self, response, **kwargs):
        self.logs.append({"event": "llm_end", "time": datetime.now().isoformat(), "response": str(response)})

    def on_llm_error(self, error, **kwargs):
        self.logs.append({"event": "llm_error", "time": datetime.now().isoformat(), "error": str(error)})

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.logs.append({"event": "tool_start", "time": datetime.now().isoformat(), "tool": serialized.get("name"), "input": input_str})

    def on_tool_error(self, error, **kwargs):
        self.logs.append({"event": "tool_error", "time": datetime.now().isoformat(), "error": str(error)})
```

## Minimal Reproduction Template

```python
"""Minimal reproduction script for LangChain issue. Run with: python minimal_repro.py"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

os.environ["OPENAI_API_KEY"] = "sk-..."  # Redact in report

def reproduce_issue():
    try:
        llm = ChatOpenAI(model="gpt-4o-mini")
        prompt = ChatPromptTemplate.from_template("Test: {input}")
        chain = prompt | llm
        result = chain.invoke({"input": "test"})
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce_issue()
```

## Debug Bundle Generator

```python
import json
from datetime import datetime
from pathlib import Path

def create_debug_bundle(error_description, logs):
    bundle = {
        "created_at": datetime.now().isoformat(),
        "description": error_description,
        "environment": collect_environment(),
        "trace_logs": logs,
        "steps_to_reproduce": [
            "1. Install packages: pip install langchain langchain-openai",
            "2. Set OPENAI_API_KEY environment variable",
            "3. Run: python minimal_repro.py"
        ]
    }
    output_path = Path("debug_bundle.json")
    output_path.write_text(json.dumps(bundle, indent=2))
    print(f"Debug bundle saved to: {output_path}")
    return bundle
```

## Checklist Before Submitting
- [ ] API keys redacted from all files
- [ ] Minimal reproduction script works independently
- [ ] Error message and stack trace included
- [ ] Package versions documented
- [ ] Expected vs actual behavior described
