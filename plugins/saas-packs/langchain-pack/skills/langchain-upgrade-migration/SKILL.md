---
name: langchain-upgrade-migration
description: |
  Manage LangChain SDK upgrades and migrations.
  Use when upgrading LangChain versions, migrating from legacy patterns,
  or updating to new APIs after breaking changes.
  Trigger with phrases like "upgrade langchain", "langchain migration",
  "langchain breaking changes", "update langchain version", "langchain 0.3".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading LangChain versions safely with migration strategies for breaking changes.

## Prerequisites
- Existing LangChain application
- Version control with current code committed
- Test suite covering core functionality
- Staging environment for validation

## Instructions

### Step 1: Check Current Versions
```bash
set -euo pipefail
pip show langchain langchain-core langchain-openai langchain-community

# Output current requirements
pip freeze | grep -i langchain > langchain_current.txt
```

### Step 2: Review Breaking Changes
```python
# Key breaking changes by version:

# 0.1.x -> 0.2.x (Major restructuring)
# - langchain-core extracted as separate package
# - Imports changed from langchain.* to langchain_core.*
# - ChatModels moved to provider packages

# 0.2.x -> 0.3.x (LCEL standardization)
# - Legacy chains deprecated
# - AgentExecutor changes
# - Memory API updates

# Check migration guides:
# https://python.langchain.com/docs/versions/migrating_chains/
```

### Step 3: Update Import Paths
```python
# OLD (pre-0.2):
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# NEW (0.3+):
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Migration script
import re

def migrate_imports(content: str) -> str:
    """Migrate old imports to new pattern."""
    migrations = [
        (r"from langchain\.chat_models import ChatOpenAI",
         "from langchain_openai import ChatOpenAI"),
        (r"from langchain\.llms import OpenAI",
         "from langchain_openai import OpenAI"),
        (r"from langchain\.prompts import",
         "from langchain_core.prompts import"),
        (r"from langchain\.schema import",
         "from langchain_core.messages import"),
        (r"from langchain\.callbacks import",
         "from langchain_core.callbacks import"),
    ]
    for old, new in migrations:
        content = re.sub(old, new, content)
    return content
```

### Step 4: Migrate Legacy Chains to LCEL
```python
# OLD: LLMChain (deprecated)
from langchain.chains import LLMChain

chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input="hello")

# NEW: LCEL (LangChain Expression Language)
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "hello"})
```

### Step 5: Migrate Agents
```python
# OLD: initialize_agent (deprecated)
from langchain.agents import initialize_agent, AgentType

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# NEW: create_tool_calling_agent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### Step 6: Migrate Memory
```python
# OLD: ConversationBufferMemory
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

# NEW: RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

### Step 7: Upgrade Packages
```bash
set -euo pipefail
# Create backup of current environment
pip freeze > requirements_backup.txt

# Upgrade to latest stable
pip install --upgrade langchain langchain-core langchain-openai langchain-community

# Or specific version
pip install langchain==0.3.0 langchain-core==0.3.0

# Verify versions
pip show langchain langchain-core
```

### Step 8: Run Tests
```bash
# Run test suite
pytest tests/ -v

# Check for deprecation warnings
pytest tests/ -W error::DeprecationWarning

# Run type checking
mypy src/
```

## Migration Checklist
- [ ] Current version documented
- [ ] Breaking changes reviewed
- [ ] Imports updated
- [ ] LLMChain -> LCEL migrated
- [ ] Agent initialization updated
- [ ] Memory patterns updated
- [ ] Tests passing
- [ ] Staging validation complete

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| ImportError | Old import path | Update to new package imports |
| AttributeError | Removed method | Check migration guide for replacement |
| DeprecationWarning | Using old API | Migrate to new pattern |
| TypeErrror | Changed signature | Update function arguments |

## Resources
- [LangChain Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [LCEL Documentation](https://python.langchain.com/docs/concepts/lcel/)
- [Release Notes](https://github.com/langchain-ai/langchain/releases)
- [Deprecation Timeline](https://python.langchain.com/docs/versions/v0_3/)

## Next Steps
After upgrade, use `langchain-common-errors` to troubleshoot any issues.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Examples

**Basic usage**: Apply langchain upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain upgrade migration for production environments with multiple constraints and team-specific requirements.