# AGY 长期记忆 (Hindsight) 协作规则

在开始复杂项目任务或需要了解历史背景时，可主动使用 `agy-hindsight_memory` 工具：
- 开始任务前：调用 `hindsight_search_pages` 或 `hindsight_recall` 查询项目架构约定、历史决策与避坑记录，避免重复试错。
- 收到用户纠正或敲定关键方案后：调用 `hindsight_capture_initiative` 或 `hindsight_ingest_document` 将约定沉淀为长期记忆页。
