<div align="center">
  <h1>aflare</h1>
  <p>
    <strong>中文</strong> ·
    <a href="README.en.md">English</a>
  </p>
  <p><strong>让 AI 告别聊天，开始执行</strong></p>
  <p><em>个人优先 · 数据不出本地 · 连接你自己的 LLM / 文件 / 笔记 / 数据库</em></p>
  <p>AI 与你的数据之间「确定且安全」的控制层</p>

  <p>
    <a href="https://github.com/alib8b8/aflare/actions/workflows/ci.yml">
      <img src="https://img.shields.io/github/actions/workflow/status/alib8b8/aflare/ci.yml?branch=main&style=flat-square&label=CI" alt="CI 状态" />
    </a>
    <a href="https://github.com/alib8b8/aflare/releases">
      <img src="https://img.shields.io/github/v/release/alib8b8/aflare?display_name=tag&include_prereleases&style=flat-square" alt="发布版本" />
    </a>
    <a href="https://golang.org/">
      <img src="https://img.shields.io/badge/Go-1.26+-00ADD8?style=flat-square" alt="Go" />
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-AGPL%20v3.0-blue.svg?style=flat-square" alt="许可证" />
    </a>
  </p>
</div>

---

## 快速开始

### 安装

**macOS / Linux** —— 一键安装(自动检测平台与架构,含校验和验证):

```bash
curl -fsSL https://raw.githubusercontent.com/alib8b8/aflare/main/install.sh | bash
```

**Windows** —— PowerShell 一键安装(自动检测架构并加入用户 PATH):

```powershell
irm https://raw.githubusercontent.com/alib8b8/aflare/main/install.ps1 | iex
```

<details>
<summary><b>其他安装方式</b>(手动下载 / deb · rpm)</summary>

```bash
# 手动下载二进制
#   GitHub:  https://github.com/alib8b8/aflare/releases
#   国内加速: https://ghproxy.com/https://github.com/alib8b8/aflare/releases
```

- `deb` / `rpm` 包见每个 Release 的附件。
- 国内网络下安装脚本会自动切换到镜像加速下载。

</details>

> **可选**:安装 bubblewrap 以获得完整沙箱隔离(`code_interpreter` 节点需要)
> - Ubuntu/Debian: `sudo apt install bubblewrap`
> - macOS:        `brew install bubblewrap`
> - Fedora:       `sudo dnf install bubblewrap`

```bash
# 1. 环境自检（零配置，立即可跑）
aflare doctor

# 2. 零配置示例：读取 post.md → 转 HTML → 写 post.html
aflare run examples/content-processor.yaml

# 3. 配置 LLM（交互式向导，本地 Ollama 或云厂商二选一）
aflare init

# 4. 关键词生成工作流（无需 LLM，纯模板匹配；加 --ai 用 LLM 生成更复杂的）
aflare create "每 10 分钟检查贵州茅台 600519 股价，超过 1400 发飞书通知"
# 输出: 工作流已生成 → 股价监控工作流（腾讯行情接口取价，A 股 6 位代码自动识别沪/深交易所）
# 通知渠道支持：飞书 / 钉钉 / 企业微信群机器人（官方 webhook，见「金融场景与合规说明」）
aflare run stock-monitor.yaml

# 5. 交互式 AI Agent 对话（ReAct Agent）
aflare chat
# 或者: aflare chat -p deepseek -m deepseek-chat

# 守护进程式 Agent（融合 stdin + 定时任务） + 可插拔能力
aflare agent -c reflection,planning,utility
```

---

## 项目状态

aflare 当前 **v0.11.0**，目标用户**先做个人**——个人数据在本机（文件、笔记库、个人 SQLite 库），aflare 做 AI 与这些数据之间「确定且安全」的控制层。

- **已交付**：核心 Runtime（DAG 调度、WAL 崩溃恢复、Saga 事务补偿、幂等、重试/熔断，CI 验证）；v0.9 国密算法（SM3 审计链 / SM4 密钥存储，opt-in）与 MCP 一键安装；v0.10 MemHarness 记忆批判-重构、步骤级类型化输出契约、水印部署溯源（含一轮安全自检修复）；v0.11 **Agent 互联与指挥**（CLI/A2A 双通道，aflare 指挥和监督其他 Agent）、**Connector API**（命名数据源连接）、webhook 事件驱动入口、守护进程稳定性基建（soak + nightly）
- **边界声明**：国产芯片（昇腾/寒武纪/海光）经 OpenAI 兼容接口接入本地推理（非原生 SDK），持续完善；硬件设备控制（机器人等）不在内置范围，可经自定义节点或 MCP Server 自行接入，数据不出内网

---

## 这是什么？

aflare 是一个**本地优先的自动化 Agent**，也是**确定性工作流执行引擎**，更是 **AI 与你的数据之间「确定且安全」的控制层**——你显式授权哪些数据（目录、笔记库、个人数据库），AI 在权限天花板内确定性地干活。两种模式共用同一核心：

```
对话式 Agent                    声明式工作流
─────────────────              ─────────────────
aflare chat                    aflare create
  ↓                              ↓
ReAct Agent 思考              关键词匹配生成
  ↓                              ↓
调用节点工具                     YAML 工作流
  ↓                              ↓
工具执行 → 反思 → 优化           DAG 调度执行
```

**Agent 模式**：通过 `aflare chat` 或 `aflare agent` 启动。内置 ReAct 推理循环，支持 6 类可插拔能力（反思、人机协同、效用驱动、记忆等）。

**工作流模式**：`aflare create` 通过关键词匹配将描述转为 YAML 工作流。YAML 确定了每一步做什么、依赖谁、失败怎么办。Runtime 负责 DAG 调度、WAL 崩溃恢复、Saga 事务补偿、熔断、审计——所有操作可追溯、可回放、可验证。

---

## 三层模型

```
L0: Agent        —  "帮我监控贵州茅台 600519，跌 5% 通知我"
                    ├── ReAct 推理循环（思考 → 调工具 → 观察 → 回答）
                    └── 6 类可插拔能力（反思/HITL/效用驱动等）
                       ↓
L1: Workflow     —  YAML 确定性工作流（schedule → get_price → condition → feishu）
                       ↓
L2: Runtime      —  确定性执行层
                    ├── DAG 并行调度
                    ├── Checkpoint / Resume（WAL 崩溃恢复）
                    ├── Session 持久化（跨轮次上下文保持）
                    ├── Saga 事务补偿
                    ├── Idempotency（幂等）
                    ├── Retry / Rate Limit / Circuit Breaker
                    ├── HMAC 审计链
                    └── Secret 脱敏
```

---

## 项目优势

aflare 面向个人用户优先（企业内网 / 本地优先场景同样适用），服务对数据隐私与安全敏感的你。核心优势：

**个人数据连接器（Connector API）** — 用 `aflare connector add` 显式授权本地目录、笔记库、个人数据库，工作流只引用连接器名：`files` / `notes` 目录连接器把 workdir 沙箱的遏制规则（禁绝对路径、禁穿越、symlink 逃逸无条件拒绝、扩展名白名单、字节数上限）应用到 `~/notes`、`~/Documents` 等你授权的根；`sqlite` / `mysql` / `postgres` 数据库连接器凭据只存 secrets store / 环境变量，SQLite 只读模式纵深防御（DSN 强制 `mode=ro`）。连接器声明的权限天花板（只读、行数、字节）节点只能收紧、不能放宽——AI 的能力边界由你定义。

**本地优先，数据不出本地** — 单二进制零运行时依赖，约 10–30MB 内存即可运行；工作流、执行历史、记忆、密钥均落本地磁盘；API Key 走环境变量或系统 keyring 注入，`config.yaml` 不存明文；离线全链路可用（离线安装、`aflare doctor --offline` 离线自检、WebUI Mermaid 离线回退）。

**连接你自己的 LLM** — Ollama / vLLM / LM Studio / DeepSeek 本地部署 / 任何 OpenAI 兼容 endpoint，loopback 地址（127.0.0.1 / localhost）免 API Key 接入。有本地 LLM 时由 LLM 做意图理解与动态生成工作流（`--ai` / `chat`），无 LLM 时关键词匹配兜底，离线仍可用。

**连接你自己的数据库与知识库** — SQL Query 节点直连你的数据库，RAG 节点 + 向量存储 + 文档解析接入你的知识库，MCP 协议连接外部服务，自定义节点用 Go 写任意集成。aflare 不回传你的数据，遥测可关闭——只干活，不外传。

**确定性执行保障** — YAML 声明式工作流：每一步做什么、依赖谁、失败怎么办全部确定。DAG 并行调度（TLA+ 形式化验证）、WAL 崩溃恢复 + Checkpoint（`--resume` 从中断处恢复）、Session 跨轮次持久化、Saga 事务补偿、幂等（Idempotency-Key + 跨进程锁）、重试 / 限流 / 熔断。所有操作可追溯、可回放、可验证。

**Agent 与工作流双模式** — 对话式 Agent（`aflare chat`，ReAct 推理循环）与守护进程式 Agent（`aflare agent`，stdin + 定时任务 + 文件监听多源融合）共用同一核心；6 类可插拔能力（反思 / 人机协同 / 效用驱动 / 记忆 / 规划 / 工作流）；Agent 可降级为确定性工作流，灵活性与确定性兼得。

**安全合规** — HMAC 哈希链审计日志（防篡改）、AES-GCM 加密 + PBKDF2（600K 迭代）、Secret 自动脱敏（10+ 种模式：AWS/GitHub/JWT/私钥）、SSRF 防护 / Path Traversal / Command Injection 白名单、出站数据量异常监控 + 熔断器自动隔离、四级安全等级（L0-L3）按需收紧。

**一键上手，离线丝滑** — `aflare doctor` 环境自检、`aflare init` 交互式配置向导、未知命令智能提示（did-you-mean）、零配置示例立即可跑。

**可扩展生态** — 自定义节点（Go）、MCP Server / Client（`aflare mcp install` 一键安装内置社区 server）、插件系统（社区 `.so`）。

**工程质量** — 表达式引擎（字节码 IR + 向量化批量求值）、Prometheus 指标端点、CI 双架构验证（x86-64 + ARM64）、国产芯片本地推理接入（昇腾 / 寒武纪 / 海光，经 OpenAI 兼容接口）。

---

## 核心能力

### 功能矩阵

| 功能 | 状态 | 验证状态 |
|------|------|----------|
| **ReAct Agent 对话** (`aflare chat`) | ✅ | 有测试 |
| **守护进程式 Agent** (`aflare agent`) | ✅ | 有测试 |
| **Agent 互联与指挥**（`@agent` 真实委派 / `cli_agent` / `a2a_agent` 节点） | ✅ | 有测试 |
| **6 类可插拔能力**（反思/HITL/效用驱动等） | ✅ | 有测试 |
| **多源输入融合**（stdin + 定时任务 + 文件监听） | ✅ | 有测试 |
| DAG 并行调度 | ✅ | 有测试 + TLA+ 形式化验证 |
| WAL 崩溃恢复 + Session 持久化 | ✅ | 有测试 |
| Saga 事务补偿 | ✅ | 有测试 |
| Idempotency（幂等） | ✅ | 有测试 |
| Retry / Rate Limit / Circuit Breaker | ✅ | 有测试 |
| HMAC 审计链 | ✅ | 有测试 |
| Secret 脱敏 | ✅ | 有测试 |
| 表达式引擎（字节码 IR + 向量化） | ✅ | 有测试 |
| 关键词匹配生成工作流 | ✅ | 有测试 |
| MCP 协议支持（Server/Client） | ✅ | 有测试 |
| **MemHarness 记忆批判-重构**（`harness_search` + 会话批判注入） | ✅ | 有测试 |
| **Connector API**（`files`/`notes`/`sqlite`/`mysql`/`postgres` 命名连接器，凭据隔离 + 权限天花板 + 根目录遏制） | ✅ | 有测试 |
| **步骤级输出契约 `output_schema`** | ✅ | 有测试 |
| **有界预览输入 `preview_input`**（16KiB） | ✅ | 有测试 |
| LLM 节点（18 家内置提供商，任意 OpenAI 兼容模型可用） | ✅ | 有测试 |
| 安全等级（L0-L3） | ✅ | 有测试 |

> 实验性功能见下方 [实验性支持](#实验性支持) 章节。

### Agent 能力（对话式 + 守护进程式）

- **ReAct 推理循环** — 思考 → 调用工具 → 观察结果 → 回答，支持 native function calling 和 JSON fallback
- **统一事件循环** — 对话式（`aflare chat`）和守护进程式（`aflare agent`）共用同一 `AgentLoop` 核心，支持 stdin / 定时任务 / 文件监听多源输入融合
- **6 类可插拔能力** — 按需启用，映射完整 Agent 类型分类学：

| 能力 | 类型 | 说明 |
|------|------|------|
| `reflection` | 反思/自我批评 | 每轮执行后自动评估输出质量，触发自我修正 |
| `human-in-loop` | 人机协同 | 关键操作暂停，请求人类确认后继续 |
| `utility` | 效用驱动 | 6 维度评分（正确性/完整性/效率/安全/清晰/可操作），优化决策 |
| `memory` | 有状态 | 跨会话长期记忆 + MemHarness 批判注入：记忆带来源状态标注（记录日期/类别）注入，超 30 天未复用自动丢弃，模型先判断适用性再使用 |
| `planning` | 规划式 | 行动前生成计划，逐步执行 |
| `workflow` | 工作流/管道式 | 优先使用已有模板，稳定可预测 |

### Agent 互联与指挥（aflare 作为上位指挥者）

aflare 不是以 skill / 插件形式嵌入其他 Agent，而是反过来：**用户安装 aflare 后，由 aflare 指挥和监督其他 Agent 工作**。两条互联通道：

- **CLI 通道** — 把本地 Agent CLI（`codex` / `claude` / `gemini` 内置预设，或任意通用 CLI）作为受管子进程运行：参数白名单校验、超时控制、输出捕获
- **A2A 通道** — 通过 [A2A 协议](https://a2a-protocol.org/) 连接远程 Agent：Agent Card 自动发现、任务提交、状态轮询、Bearer 认证（密钥走环境变量，不落盘）

**注册外部 Agent**（`~/.config/aflare/config.yaml`）：

```yaml
agents:
  codex:                      # 内置预设，开箱即用
    driver: cli
    description: 代码实现与工程任务
  research-a2a:               # 任意 A2A 远程 Agent
    driver: a2a
    url: http://127.0.0.1:8080/
    api_key_env: MY_AGENT_KEY # Bearer token 从该环境变量读取
    description: 深度调研
  my-tool:                    # 任意通用 CLI
    driver: cli
    profile: generic
    binary: /usr/local/bin/my-agent
    args: ["--json"]
```

```bash
aflare agent list    # 查看已注册、可指挥的外部 Agent
```

**指挥方式**（三种，均带监督）：

1. **supervisor 节点真实委派** — `specialists` 中以 `@` 前缀引用注册的 Agent，aflare 用 LLM 规划子任务、并行委派（`max_parallel` 限流，默认 4 / 上限 16）、汇总结果：

```yaml
- id: orchestrate
  node: supervisor
  params:
    specialists: "@codex,@research-a2a"   # 混搭 CLI 与 A2A Agent
    max_parallel: "2"                      # 背压：并发委派上限
```

2. **`cli_agent` / `a2a_agent` 节点** — 工作流中单步直接委派：`cli_agent` 支持 `model` / `sandbox` / `approval_policy` / `max_turns` / `timeout`，`a2a_agent` 支持 `agent` / `url` / `api_key_env` / `timeout`
3. **失败隔离** — 单个 Agent 失败只记录该次结果，不拖垮整批委派；A2A 轮询对瞬时 5xx/网络抖动自动重试（提交阶段仅重试"未送达"的连接错误，避免重复执行）

> 安全约束：所有委派经 fail-closed 审计钩子（审计失败即拒绝执行）、prompt 长度上限、超时硬边界；CLI Agent 的 prompt 永远作为单个 argv 参数传递，不参与 flag 解析，杜绝命令注入。

### Runtime 保障（确定性执行）
- **DAG 并行调度** — 拓扑排序依赖调度，无依赖步骤并发执行
- **WAL 崩溃恢复 + Session 持久化** — append-only 持久化 + CRC32 校验，`--resume` 从中断处恢复；Session 跨轮次保持上下文
- **Saga 事务补偿** — 多步骤写入失败自动反向回滚
- **Idempotency** — Idempotency-Key + 原子占位 + 跨进程锁，防重复执行
- **Retry / Rate Limit / Circuit Breaker** — 指数退避 + 令牌桶 + 熔断器状态机

### 安全与合规
- HMAC 哈希链审计日志（防篡改）
- AES-GCM 加密 + PBKDF2（600K 迭代）
- Secret 自动脱敏（10+ 种模式：AWS/GitHub/JWT/私钥）
- SSRF 防护 / Path Traversal / Command Injection 白名单
- 出站数据量异常监控 + 熔断器自动隔离

### 工作流生成
- 关键词匹配生成 YAML 工作流（`aflare create`，见 [`generator.go`](internal/workflow/generator.go)）

### LLM 节点（工作流中调用 LLM API）
- 18 家内置提供商（OpenAI / DeepSeek / Qwen / GLM / Kimi / Anthropic / Gemini / Mistral / Ollama 等），任意 OpenAI 兼容模型可用
- 完全离线运行（Ollama 本地 LLM）
- LLM 智能路由（EWMA 延迟预测 + 帕累托成本排序）

### MCP 协议支持
- 内置 MCP Server，可被任何 MCP 客户端（Claude、VS Code、Cursor 等）连接
- 提供工作流运行、验证、节点查询、代码图谱等工具
- 内置 MCP Client，工作流中可直接调用外部 MCP 服务
- `aflare mcp install <name>` 一键安装 8 个内置社区 server
- 也可通过 [DeepSeek Harness (DSH) 集成](docs/dsh.md) 将 aflare 工具暴露给 DSH 智能体（MCP 桥接零代码接入，或原生 [Cordis 插件](integrations/dsh-plugin)）

### Connector API（个人数据接入主线）

命名连接器 = 你显式授权的数据源 + 策略天花板。工作流只写连接器名，凭据永不进 YAML：

```bash
# 授权笔记目录（默认只读，symlink 逃逸无条件拒绝）
aflare connector add my-notes --type notes --root ~/notes

# 授权文档目录（只允许 md/txt，显式开启写入）
aflare connector add my-docs --type files --root ~/Documents --include '*.md' --include '*.txt' --writable

# 个人 SQLite 库（DSN 强制 mode=ro 只读）
aflare connector add my-library --type sqlite --database ~/calibre/metadata.db

# 远程数据库（凭据存 secrets store，spec 只有引用）
aflare connector add my-pg --type postgres --host db.example.com --database analytics \
  --username readonly --credential-group connectors
```

- **五类连接器**：`files` / `notes`（目录，`file_read`/`file_write`/`files_list` 节点）+ `sqlite` / `mysql` / `postgres`（数据库，`sql_query` 节点）
- **凭据隔离**：workflow 只引用连接器名；凭据只存 secrets store（`aflare secrets set`）或环境变量
- **权限天花板**：连接器声明只读 / max_rows / max_bytes / 扩展名白名单 / 超时——节点参数只能收紧、不能放宽
- **根目录遏制**：workdir 沙箱的同一套规则（禁绝对路径、禁穿越）应用到授权根，符号链接逃逸**无条件拒绝**；SQLite 只读模式纵深防御
- 详细设计见 [docs/connector-api.md](docs/connector-api.md)

### 记忆批判-重构（MemHarness 模式）
- memory 节点 `harness_search` 操作：检索候选记忆时携带完整来源状态（类型/层级/置信度/记录时间/相关度），生成自包含批判 prompt；LLM 批判（keep/rewrite/discard）作为显式可重试的工作流步骤执行，无适用记忆输出 `<EMPTY>` 而非编造
- Agent 会话注入走确定性批判：陈旧且从未复用的记忆直接丢弃，幸存记忆带来源标注注入
- 完整示例见 `examples/real-world/memharness-critique/`

### 步骤级类型化输出契约与有界预览
- `output_schema`：任意节点输出按 JSON Schema（draft-07 子集）强制校验，违规按步骤失败处理并报出首个违规位置，自然流入 retry / on_error / capture_error
- `preview_input: true`：超 16KiB 的输入替换为头尾样本有界预览，完整值保留在工作流状态、原样传给其他步骤——LLM 看样本，确定性节点操作完整数据

### 工程能力
- 表达式引擎：字节码 IR + 向量化批量求值
- DAG 调度器经 TLA+ 形式化验证（spec 见 [`docs/tla/dag_scheduler.tla`](docs/tla/dag_scheduler.tla)，Go 测试 `dag_formal_test.go` 可执行有界模型检查）
- Prometheus 指标端点
- 单二进制部署，零运行时依赖
- CI 双架构验证（x86-64 + ARM64）

### 实验性支持
- 昇腾 / 寒武纪 / 海光上的本地推理服务接入（通过 OpenAI 兼容接口，非原生 SDK 集成，持续完善中）
- 硬件设备控制通过自定义节点 / MCP Server 接入（aflare 不内置特定硬件驱动，避免绑定单一厂商）

---

## 架构

```
┌──────────────────────────────────────────────────────┐
│                    aflare                             │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Agent Layer (L0)                                  │ │
│  │                                                    │ │
│  │  aflare chat / aflare agent                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ ReAct    │  │ 节点工具  │  │ 6 类可插拔      │  │ │
│  │  │ 推理循环  │  │ 工具调用  │  │ 能力            │  │ │
│  │  └──────────┘  └──────────┘  └────────────────┘  │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │ AgentLoop 统一事件循环                         │ │ │
│  │  │ stdin · scheduler · filewatch · MCP · HTTP   │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────┘ │
│                        ↓                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │
│  │ Intent   │──▶│ Workflow │──▶│ Deterministic     │  │
│  │ (描述)   │   │ (YAML)   │   │ Executor          │  │
│  └──────────┘   └──────────┘   │                    │  │
│                                 │ • DAG Scheduler   │  │
│                                 │ • WAL / Checkpoint│  │
│                                 │ • Session 持久化   │  │
│                                 │ • Saga / Retry    │  │
│                                 │ • Circuit Breaker │  │
│                                 │ • Audit / HMAC    │  │
│                                 └──────────────────┘  │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 执行目标                                          │ │
│  │ Software (API/Web/DB/文件)                         │ │
│  │ 外部设备（经自定义节点/MCP 接入，实验性）             │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 路线图

| 版本 | 状态 | 重点 |
|------|------|------|
| v0.6 | 已完成 | Agent 记忆基础设施、语音 AI 工具链、WAL 持久化、TLA+ 验证 |
| v0.7 | 已完成 | 金融场景增强（Saga / 幂等 / 审计链）、ReAct Agent 对话、6 类可插拔能力、Agent 统一事件循环 |
| v0.8 | 已完成 | 离线/内网首选项体验、隐私安全硬化、本地 LLM 丝滑接入、CLI 体验优化（智能命令提示）、CI 提速 |
| **v0.8.1** | **已完成** | 发布审计修复：国内安装 404、`aflare mcp` 子命令、execute 白名单错误定位、govulncheck 漏洞清零 |
| **v0.9** | **已完成** | 国密算法支持（SM3/SM4，opt-in）、审计链安全硬化（随机 HMAC 密钥、跨进程锁、bundle 防截断伪造）、`aflare mcp install` 一键安装、供应链场景包、loong64 |
| **v0.10** | **已完成** | MemHarness 记忆批判-重构、步骤级输出契约与有界预览、水印部署溯源、安全自检修复 |
| **v0.11** | **已完成** | **Agent 互联与指挥**（CLI/A2A 双通道、supervisor 真实委派、背压与瞬时重试）、**Connector API**（命名数据源连接）、webhook 事件驱动入口（GitHub HMAC 签名）、守护进程稳定性基建（soak + nightly + goleak）、daemon 信号死锁修复 |
| **main** | **进行中** | Agent 互联深化（更多通道与监督策略）、个人笔记软件连接器、国产芯片适配完善 |
| v1.0 | 计划中 | 稳定 API、LTS |

详情见 [CHANGELOG.md](CHANGELOG.md)

---

## 安全

aflare 内置多层安全防护，支持四级安全等级（`--security-level`）：

| 等级 | 说明 |
|------|------|
| **L0** | 宽松：允许所有节点，沙箱降级时仅警告 |
| **L1** | 标准：沙箱降级时警告，启发式拦截 |
| **L2** | 严格：无 bwrap 沙箱时拒绝执行 code_interpreter，命令白名单校验 |
| **L3** | 极严：禁用 code_interpreter 节点，最大安全策略 |

其他防护：SSRF 防护、Path Traversal 防御、Command Injection 白名单、AES-GCM 加密、Secret 脱敏、HMAC 审计链、熔断器、出站监控。CI 自动运行 `gofmt` / `go vet` / `gosec` / `govulncheck`。

[安全指南 →](SECURITY.md)

---

## 金融场景与合规说明

aflare 提供的是**数据处理与自动化执行能力**，金融场景（股价监控、行情提醒、复盘报告等）只是工作流的一种应用。使用前请阅读以下说明：

### 数据来源

- `aflare create` 生成的股价监控工作流使用**腾讯行情公开接口**（`web.ifzq.gtimg.cn`）获取 A 股行情，数据可能有延迟，仅供个人学习与研究参考，不保证实时性与准确性。
- 其他**公开行情接口**（东方财富、新浪财经等）可通过 `http_request` 节点直接调用，覆盖 A 股 / 港股 / 美股 / 基金等品种。
- 任何第三方数据源（腾讯、东方财富、新浪等）的合规使用责任由使用者承担，商用前请确认数据授权。

### 通知渠道

行情提醒等通知通过 `notify` 节点发送，国内合规渠道均为各平台**官方群机器人 webhook**：

| 渠道 | channel | 说明 |
|------|---------|------|
| 飞书 | `feishu` | 群设置 → 群机器人 → 自定义机器人，复制 webhook 地址 |
| 钉钉 | `dingtalk` | 群设置 → 智能群助手 → 自定义机器人，复制 webhook 地址 |
| 企业微信 | `wecom` | 群右键 → 添加群机器人，复制 webhook 地址 |
| 终端 / 自定义 | `stdout` / `webhook` | 本地输出或任意 HTTPS webhook |

- 个人微信与 QQ **没有官方机器人推送接口**，为实现合规推送，微信生态请使用企业微信群机器人（`wecom`）。
- 生成工作流时在描述中写明渠道即可，如 `aflare create "每 10 分钟检查贵州茅台 600519 股价，超过 1400 发飞书通知"`，运行前用 `--set feishu_webhook_url=<你的 webhook 地址>` 传入。

### 定位边界

| 场景 | 可行性 | 说明 |
|------|--------|------|
| **行情监控 / 阈值提醒** | ✅ 完全支持 | 定时取价 → 条件判断 → 通知，`aflare create` 一句话生成 |
| **复盘助手（研究工具）** | ✅ 支持 | 拉取历史行情 + LLM 生成复盘报告，输出仅供个人研究参考 |
| **量化研究 / 回测** | ⚠️ 部分支持 | 数据获取、指标计算、定时调度可由工作流承担；策略回测与模拟盘需自行接入（如券商仿真接口或开源回测框架）；**实盘下单必须通过持牌券商的合规接口（如 QMT/PTrade）并自行评估风险** |
| **投资顾问 / 荐股** | ❌ 不提供 | 证券投资咨询在中国属于持牌业务。aflare 不构成、也不提供任何投资建议；生成内容均为客观数据整理，不预测涨跌、不推荐买卖 |

### 免责声明

> 本项目及其生成的任何数据、报告、通知**均不构成投资建议**，不承诺任何收益，不承担因使用本项目产生的任何直接或间接损失。行情数据可能存在延迟或错误，请以交易所官方披露为准。投资者应独立判断并自担风险，必要时咨询持牌投资顾问。

---

## 文档

- [入门指南](docs/getting-started.md) · [教程](docs/tutorial.md) · [YAML 语法](docs/getting-started.md#workflow-configuration)
- [数据流](docs/dataflow.md) · [调度](docs/scheduling.md) · [MCP](docs/mcp.md) · [插件](docs/plugins.md) · [连接器](docs/connector-api.md)
- [Web UI](docs/webui.md) · [可视化](docs/visualizer.md) · [自定义节点](docs/custom-nodes.md)
- [API 文档](docs/api.md) · [节点参考](docs/nodes-reference.md)
- [部署指南](docs/deployment.md) · [Docker](docs/docker.md) · [多租户](docs/tenants.md)
- [故障排除](docs/troubleshooting.md)

---

## 贡献

欢迎社区贡献！

[贡献指南 →](CONTRIBUTING.md)

---

## 许可证

GNU Affero General Public License v3.0 — [LICENSE](LICENSE)

---

<div align="center">
  <p>
    <a href="https://github.com/alib8b8/aflare">GitHub</a>
    ·
    <a href="https://github.com/alib8b8/aflare/issues">Issues</a>
    ·
    <a href="https://github.com/alib8b8/aflare/discussions">Discussions</a>
  </p>
</div>