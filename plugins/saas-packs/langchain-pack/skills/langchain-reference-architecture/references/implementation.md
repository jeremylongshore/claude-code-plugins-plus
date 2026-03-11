# LangChain Reference Architecture - Detailed Implementation

## Layered Architecture Structure

```
src/
├── api/                    # API layer (FastAPI/Flask)
│   ├── __init__.py
│   ├── routes/
│   │   ├── chat.py
│   │   └── agents.py
│   └── middleware/
│       ├── auth.py
│       └── rate_limit.py
├── core/                   # Business logic layer
│   ├── __init__.py
│   ├── chains/
│   │   ├── __init__.py
│   │   ├── chat_chain.py
│   │   └── rag_chain.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── research_agent.py
│   └── tools/
│       ├── __init__.py
│       └── search.py
├── infrastructure/         # Infrastructure layer
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── vectorstore/
│   │   └── pinecone.py
│   └── cache/
│       └── redis.py
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py
└── main.py
```

## Provider Abstraction Pattern

```python
# infrastructure/llm/provider.py
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class LLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    def get_chat_model(self, **kwargs) -> BaseChatModel:
        pass

class OpenAIProvider(LLMProvider):
    def get_chat_model(self, model: str = "gpt-4o-mini", **kwargs) -> BaseChatModel:
        return ChatOpenAI(model=model, **kwargs)

class AnthropicProvider(LLMProvider):
    def get_chat_model(self, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> BaseChatModel:
        return ChatAnthropic(model=model, **kwargs)

class LLMFactory:
    """Factory for creating LLM instances."""

    _providers = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
    }

    @classmethod
    def create(cls, provider: str = "openai", **kwargs) -> BaseChatModel:
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")
        return cls._providers[provider].get_chat_model(**kwargs)

# Usage
llm = LLMFactory.create("openai", model="gpt-4o-mini")
```

## Chain Registry Pattern

```python
# core/chains/__init__.py
from typing import Dict, Type
from langchain_core.runnables import Runnable

class ChainRegistry:
    """Registry for managing chains."""

    _chains: Dict[str, Runnable] = {}

    @classmethod
    def register(cls, name: str, chain: Runnable) -> None:
        cls._chains[name] = chain

    @classmethod
    def get(cls, name: str) -> Runnable:
        if name not in cls._chains:
            raise ValueError(f"Chain '{name}' not found")
        return cls._chains[name]

    @classmethod
    def list_chains(cls) -> list:
        return list(cls._chains.keys())

# Register chains at startup
from core.chains.chat_chain import create_chat_chain
from core.chains.rag_chain import create_rag_chain

ChainRegistry.register("chat", create_chat_chain())
ChainRegistry.register("rag", create_rag_chain())

# Usage in API
@app.post("/invoke/{chain_name}")
async def invoke_chain(chain_name: str, request: InvokeRequest):
    chain = ChainRegistry.get(chain_name)
    return await chain.ainvoke(request.input)
```

## RAG Architecture

```python
# core/chains/rag_chain.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_pinecone import PineconeVectorStore

def create_rag_chain(
    llm: BaseChatModel = None,
    vectorstore: VectorStore = None
) -> Runnable:
    """Create a RAG chain with retrieval."""

    llm = llm or ChatOpenAI(model="gpt-4o-mini")
    vectorstore = vectorstore or PineconeVectorStore.from_existing_index(
        index_name="knowledge-base",
        embedding=OpenAIEmbeddings()
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    prompt = ChatPromptTemplate.from_template("""
    Answer the question based on the following context:

    Context:
    {context}

    Question: {question}

    Answer:
    """)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
    )

    return chain
```

## Multi-Agent Orchestration

```python
# core/agents/orchestrator.py
from langchain_core.runnables import RunnableLambda
from typing import Dict, Any

class AgentOrchestrator:
    """Orchestrate multiple specialized agents."""

    def __init__(self):
        self.agents = {}
        self.router = None

    def register_agent(self, name: str, agent: Runnable) -> None:
        self.agents[name] = agent

    def set_router(self, router: Runnable) -> None:
        self.router = router

    async def route_and_execute(self, input_data: Dict[str, Any]) -> Any:
        agent_name = await self.router.ainvoke(input_data)
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        agent = self.agents[agent_name]
        return await agent.ainvoke(input_data)

# Setup
orchestrator = AgentOrchestrator()
orchestrator.register_agent("research", research_agent)
orchestrator.register_agent("coding", coding_agent)
orchestrator.register_agent("general", general_agent)

router_prompt = ChatPromptTemplate.from_template("""
Classify this request into one of: research, coding, general

Request: {input}

Classification:
""")
orchestrator.set_router(router_prompt | llm | StrOutputParser())
```

## Configuration-Driven Design

```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class LLMSettings(BaseSettings):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 3

class VectorStoreSettings(BaseSettings):
    provider: str = "pinecone"
    index_name: str = "default"
    embedding_model: str = "text-embedding-3-small"

class Settings(BaseSettings):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vectorstore: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

settings = Settings()

llm = LLMFactory.create(
    settings.llm.provider,
    model=settings.llm.model,
    temperature=settings.llm.temperature
)
```

## Architecture Diagram

```
                    +------------------+
                    |   API Gateway    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
    +---------+------+ +-----+------+ +-----+---------+
    |  Chat Chain    | |  RAG Chain | | Agent System   |
    +-------+--------+ +-----+------+ +------+--------+
            |                |               |
            +----------------+---------------+
                             |
              +--------------+--------------+
              |              |              |
    +---------+------+ +-----+------+ +-----+---------+
    |  LLM Provider  | | VectorStore| |    Cache       |
    +----------------+ +------------+ +----------------+
```
