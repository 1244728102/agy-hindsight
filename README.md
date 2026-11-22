<h1 align="center">AGY Hindsight Memory · AGY 跨会话项目长期记忆系统</h1>

<p align="center"><b>Long-term project memory and structured knowledge graph for Google Antigravity (AGY): auto-distill past conversations, architectural decisions, and bugfix playbooks.</b></p>

<p align="center">🥇 <b>自动沉淀历史会话、架构决策与避坑记录的 Google Antigravity 跨会话项目长期记忆知识库插件。</b> 🥇</p>

<p align="center">
  <a href="./README.zh-CN.md">简体中文</a> ·
  <a href="./INSTALL.md">Install Guide</a> ·
  <a href="./CHANGELOG.md">Changelog</a> ·
  <a href="./LICENSE">License</a>
</p>

<p align="center">
  <a href="https://github.com/1244728102"><img src="https://img.shields.io/badge/author-1244728102%20(%E7%88%B1%E5%93%AD%E7%9A%84%E4%BC%8A%E8%95%BE%E5%A8%9C)-b69cf5?style=flat-square&logo=github" alt="Author"></a>
  <img src="https://img.shields.io/badge/version-0.1.0-e9c27a?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Google%20Antigravity%20(AGY)-6a56b8?style=flat-square" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
</p>

---

## ✨ Overview & Highlights

**AGY Hindsight Memory · AGY 跨会话项目长期记忆系统 (`agy-hindsight`)** — 适配 Antigravity 的项目长期记忆插件（Hindsight）：自动沉淀历史会话与项目决策，提供知识页检索、记录与跨会话记忆召回。

# AGY 长期记忆 (`agy-hindsight`)

使用 `agy-hindsight_memory` 工具管理项目长期记忆与知识页：

- `hindsight_open_ui`：打开 **长期记忆** 交互面板。
- `hindsight_list_pages` / `hindsight_search_pages` / `hindsight_read_page`：列出、检索、读取项目知识页（架构、约定、决策等）。
- `hindsight_ingest_document` / `hindsight_capture_initiative`：写入或更新项目知识页与正在进行的决策。
- `hindsight_recall`：按关键词召回历史记忆与已索引的 Antigravity 会话记录。
- `hindsight_ingest_conversations`：扫描并索引本地 `brain/` 历史会话到记忆库。


---

## 🚀 Quick Install

**Windows PowerShell**:
```powershell
git clone https://github.com/1244728102/agy-hindsight.git "$env:USERPROFILE\.gemini\config\plugins\agy-hindsight"
```

**macOS / Linux**:
```bash
git clone https://github.com/1244728102/agy-hindsight.git "$HOME/.gemini/config/plugins/agy-hindsight"
```

**Or hand the install to your AI agent**:
> Install and configure `agy-hindsight` following https://github.com/1244728102/agy-hindsight/blob/main/INSTALL.md

---

## 📂 Project Files (`14` files)

```text
agy-hindsight/
├── .gitignore
├── assets/logo.svg
├── CHANGELOG.md
├── INSTALL.md
├── LICENSE
├── mcp_config.json
├── plugin.json
├── README.md
├── rules/AGENTS.md
├── server/mcp_server.py
├── server/memory_bank.py
├── skills/agy-hindsight/SKILL.md
├── ui/app.html
├── ui/ext-apps.js
```

---

## 📜 License

MIT © [1244728102 (爱哭的伊蕾娜)](https://github.com/1244728102)
