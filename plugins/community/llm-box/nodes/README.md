# 📦 llm-box Community Nodes

This directory holds **community-contributed nodes** that extend llm-box.
Each node is a self-contained folder with a `metadata.yaml` and an entry script.

> Want to add your own? See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Structure

```
nodes/
├── _template/      # copy this to start a new node
│   ├── metadata.yaml
│   └── main.py
├── echo/           # example node
│   ├── metadata.yaml
│   └── main.py
└── <your_node>/    # your new node
    ├── metadata.yaml
    └── main.<ext>
```

## Node Protocol

- **Input (stdin):** JSON `{"input": "text", "params": {...}}`
- **Output (stdout):** plain text
- **Error (stderr):** anything → reported as node failure
