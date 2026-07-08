<div align="center">
  <img src="docs/logo.svg" alt="llm-box" width="200" />
  <h1>llm-box</h1>
  <p><strong>用自然语言构建终端工作流</strong></p>
<p>描述你想要什么，llm-box 生成 YAML 并执行它。</p>

  <p>
    <a href="https://github.com/alib8b8/llm-box/releases">
      <img src="https://img.shields.io/github/v/release/alib8b8/llm-box?display_name=tag&include_prereleases&style=flat-square" alt="release" />
    </a>
    <a href="https://golang.org/">
      <img src="https://img.shields.io/badge/Go-1.25+-00ADD8?style=flat-square" alt="Go" />
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="license" />
    </a>
    <a href="https://github.com/alib8b8/llm-box/actions/workflows/release.yml">
      <img src="https://github.com/alib8b8/llm-box/actions/workflows/release.yml/badge.svg" alt="CI status" />
    </a>
    <a href="https://goreportcard.com/report/github.com/alib8b8/llm-box">
      <img src="https://goreportcard.com/badge/github.com/alib8b8/llm-box" alt="Go Report Card" />
    </a>
  </p>

<p>
  <a href="README.md">English</a> |
  <strong>中文</strong> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.hi.md">हिन्दी</a>
</p>
</div>

---

## 🚀 快速开始

60 秒安装：

```bash
# Linux/macOS
curl -sL https://raw.githubusercontent.com/alib8b8/llm-box/main/install.sh -o install.sh
bash install.sh

# Windows
# 从 releases 下载: https://github.com/alib8b8/llm-box/releases/latest
Invoke-WebRequest -Uri "https://github.com/alib8b8/llm-box/releases/latest/download/llm-box-windows-amd64.exe" -OutFile llm-box.exe
```

创建并运行你的第一个工作流：

```bash
# 创建工作流
llm-box create "抓取 Hacker News 头条并保存到 stories.txt"

# 运行
llm-box run hn_workflow.yaml
```

---

## 💡 为什么选择 llm-box？

**不是又一个 AI 聊天机器人**

大多数工作流工具让开发者在以下选择中纠结：

| 方案 | 问题 |
|------|------|
| 复杂的 bash 脚本 | 难读、难维护、难分享 |
| 笨重的可视化构建器 | 慢、不透明、需要 GUI |
| 无尽的配置文件 | 学习曲线陡峭、语法冗长 |

**llm-box 不是 AI 助手 — 它是一个确定性执行引擎。**

- ✅ **可预测、可审计** — 工作流步骤确定可控
- ✅ **本地优先** — 你的数据永远不离开终端
- ✅ **透明、可复现** — 相同工作流产生相同结果
- ✅ **MIT 开源** — 无供应商锁定、无隐性壁垒

> 💡 我们用 AI 理解你的意图，但核心执行是确定性的代码。

---

## ✨ 特性

- **终端优先** - 原生 CLI，有终端就能用
- **自然语言工作流** - 定义你要什么，而不是怎么做
- **单二进制文件** - 零依赖，下载即用
- **工作流可复用** - 保存、版本化、分享你的工作流
- **多 LLM 支持** - Ollama（本地）、DeepSeek、智谱 GLM、Kimi、MiniMax、Qwen 等
- **可扩展节点系统** - 用任何语言构建自定义节点
- **MIT 许可** - 开源，自由使用
- **跨平台** - 支持 Linux、macOS、Windows
- **精美的 TUI** - 实时进度反馈

---

## 🔄 llm-box vs 其他方案

| 特性 | llm-box | Dify/n8n | Claude Code | CrewAI |
|------|---------|----------|-------------|--------|
| **界面** | 终端 + YAML | 可视化 GUI | 聊天 | 代码 |
| **执行方式** | 确定性 | AI 驱动 | AI 自主 | AI 编排 |
| **上手时间** | 60 秒 | 几小时 | 几分钟 | 几小时 |
| **透明度** | 100% | 中等 | 低 | 中等 |
| **可复现性** | 100% | 不确定 | 不确定 | 不确定 |
| **最适合** | 自动化 | 企业应用 | 编码 | 研究 |

**选择 llm-box 当你需要：** 可重复、可审计的工作流，在不失控的前提下获得 AI 辅助。

---

## 🎬 演示

![llm-box demo](docs/demo.svg)

> **生成你自己的演示**
> 运行 `vhs docs/demo.tape` 创建高质量 GIF。

---

## 🔧 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户（终端）                           │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   自然语言解析器                              │
│              "抓取 HN 头条并总结"                            │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     任务规划器                                │
│            将意图转换为可执行步骤                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  执行引擎                                    │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │fetch_url │ │transform  │ │execute_cmd │ │file_write│ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │ollama    │ │deepseek   │ │kimi        │ │glm        │ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌───────────┐ │
│  │qwen      │ │minimax    │ │coze        │ │自定义节点  │ │
│  └──────────┘ └───────────┘ └────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       输出                                  │
│                 （终端 / 文件 / 通知）                       │
└─────────────────────────────────────────────────────────────┘
```

**组件：**
1. **解析器** - 解释自然语言命令
2. **规划器** - 拆解为执行步骤
3. **引擎** - 依赖管理式执行
4. **节点** - 内置和可扩展的动作
5. **输出** - 格式化的结果

---

## 🤖 支持的 LLM

llm-box 开箱即用支持多种 LLM 提供商：

### DeepSeek（云端 API）

`deepseek` 节点调用 DeepSeek 官方 API。不想本地运行模型时的完美选择。

**设置：**
```bash
export DEEPSEEK_API_KEY="your-api-key"
```

**可用模型：**
- `deepseek-chat` - 通用聊天模型
- `deepseek-coder` - 代码生成模型
- `deepseek-reasoner` - 推理模型（R1）

### 智谱 GLM（云端 API）

`glm` 节点调用智谱 AI 的 GLM API（OpenAI 兼容）。原生中文支持。

**设置：**
```bash
export GLM_API_KEY="your-api-key"
```

**可用模型：**
- `glm-4` - 旗舰模型，推理能力强
- `glm-4v` - 视觉语言模型
- `glm-3-turbo` - 快速、高性价比
- `glm-4-plus` - 高智能、更长上下文

### Coze（云端 API）

`coze` 节点调用字节跳动的 Coze API（OpenAI 兼容）。中文任务表现优秀。

**设置：**
```bash
export COZE_API_KEY="your-api-key"
```

### Kimi（云端 API）

`kimi` 节点调用月之暗面的 Kimi API（OpenAI 兼容）。以超长上下文窗口著称。

**设置：**
```bash
export KIMI_API_KEY="your-api-key"
```

**可用模型：**
- `moonshot-v1-8k` - 8K 上下文，标准版
- `moonshot-v1-32k` - 32K 上下文，长文档
- `moonshot-v1-128k` - 128K 上下文，超大文件

### MiniMax（云端 API）

`minimax` 节点调用 MiniMax 的 API（OpenAI 兼容）。中文理解能力强。

**设置：**
```bash
export MINIMAX_API_KEY="your-api-key"
```

**可用模型：**
- `abab6.5s-chat` - 快速均衡
- `abab6.5t-chat` - 文本聚焦
- `abab7-chat` - 最新一代

### Qwen 通义千问（云端 API）

`qwen` 节点调用阿里云通义千问 API（OpenAI 兼容）。阿里云生态深度集成。

**设置：**
```bash
export QWEN_API_KEY="your-api-key"
```

**可用模型：**
- `qwen-turbo` - 快速、高性价比
- `qwen-plus` - 性能均衡
- `qwen-max` - 最强能力
- `qwen-long` - 长上下文（10M tokens）
- `qwen-vl-max` - 视觉语言模型

### Ollama（本地）

`ollama` 节点通过 Ollama 本地运行模型。注重隐私和离线使用的最佳选择。

**设置：**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh -o ollama-install.sh
sh ollama-install.sh

# 拉取模型
ollama pull llama3
```

### OpenAI 兼容（任何提供商）

`openai` 节点适用于**任何**遵循 OpenAI 格式的 API — 硅基流动、Together AI、腾讯混元，以及数百家更多。

**设置：**
```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.siliconflow.cn/v1"
```

**支持的平台：**
- 硅基流动 SiliconFlow - 30+ 模型
- 腾讯混元
- Together AI
- 任何 OpenAI 兼容的端点

---

## ❓ 常见问题

### 和 Bash 脚本有什么不同？
llm-box 增加了结构、可复用性和漂亮的 UI，同时不损失终端的威力。

### 我必须写 YAML 吗？
不用！用自然语言描述你想要什么，llm-box 会为你生成 YAML。

### 可以扩展吗？
当然！用任何语言构建自定义节点。

### 生产环境可用吗？
v0.1 是早期访问版本。v1.0（稳定版）计划于 2026 年 Q3 发布。

### 支持哪些平台？
完全支持 Linux、macOS 和 Windows。

### 在哪里可以获得帮助？
在 GitHub Discussion 发帖或提交 issue。

---

## 🗺️ 路线图

### v0.1 - 初始发布 ✓
- [x] 基础工作流创建
- [x] 执行引擎
- [x] 内置节点（fetch_url, file_write, ollama）
- [x] 终端 UI

### v0.2 - 多 LLM & 插件系统
- [x] DeepSeek API 节点支持
- [x] Coze API 节点支持
- [x] 智谱 GLM API 节点支持
- [x] Kimi API 节点支持
- [x] MiniMax API 节点支持
- [x] Qwen 通义千问 API 节点支持
- [x] 通用 OpenAI 兼容节点（任何提供商）
- [ ] 自定义节点插件系统
- [ ] 工作流模板库
- [ ] 通过 URL 分享工作流

### v0.3 - 团队特性
- [ ] 团队工作流仓库
- [ ] 工作流版本管理
- [ ] 云端同步（可选）

### v0.4 - 企业版
- [ ] 访问控制
- [ ] 审计日志
- [ ] 定时工作流

### v1.0 - 稳定版
- [ ] 生产就绪
- [ ] 完善的文档
- [ ] 长期支持

---

## 🤝 贡献

我们欢迎所有技术水平的贡献者！

### 贡献方式
- **Go 开发者** - 构建新节点，改进核心
- **文档** - 改进文档，编写教程
- **工作流设计师** - 分享你的工作流
- **社区建设者** - 在讨论区帮助他人

### 快速开始

```bash
git clone https://github.com/alib8b8/llm-box.git
cd llm-box
go mod download
go test ./...
go build -o llm-box ./cmd/llm-box
./llm-box help
```

---

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

---

<div align="center">
  <p>如果这个项目对你有帮助，请给个 ⭐</p>
  <p>
    <a href="https://github.com/alib8b8/llm-box/stargazers">
      <img src="https://api.star-history.com/svg?repos=alib8b8/llm-box&type=Timeline" alt="Star History" />
    </a>
  </p>
</div>
