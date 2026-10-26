# MCP 操作规范

## 工具映射

以运行时发现的 schema 为准；以下是轻笺 2.1 MCP 行为。工具前缀随客户端改变。

| 工具 | 用途与关键参数 |
|---|---|
| qingjian_info | localDate、timeZone、revision、sortMode |
| qingjian_list_tasks | date/done/parentId/query；limit最高200，offset分页 |
| qingjian_get_task | id；返回 task、children、revision |
| qingjian_add_task | title；可选date/parentId/dueAt/remindAt |
| qingjian_update_task | id；title/date/dueAt/remindAt，未提供字段保留 |
| qingjian_set_completed | id、done（显式布尔） |
| qingjian_set_pinned | id、pinned；仅主任务 |
| qingjian_move_task | id、parentId（移出为null），位置beforeId或afterId等 |
| qingjian_reorder_tasks | 完整分组ids；parentId/date/pinned界定分组 |
| qingjian_delete_task | id；删除目标和全部直接子任务 |

所有写工具另需 expectedRevision 与全局唯一 requestId（UUID）。日期为 YYYY-MM-DD；时间为带 Z 或明确UTC偏移的ISO8601，null显式清除。未指定字段与null不同。不可向 schema 添加 confirmed 等字段。不要通过标题偷偷编码软件不支持的字段。

## 读取与分组

list 必须处理 nextOffset，完整列出候选后判断唯一性、重复或分组，不能把第一页当全部。get 返回完整直接子任务。query是子串搜索，不等于精确唯一匹配。

排序须manual；reorder提供一个分组全部 ID（包括未变位置的条目）。置顶组可能跨日期，普通组按日期；子任务组按parentId。按服务端实际返回确认分组；不能经MCP自动更改sortMode。能力不满足时说明，不用删建模拟。

## 父子联动（写前必须核对）

- set_completed作用于父任务：全部子任务跟随其完成状态。未完成子节点无证据时，不能为关闭父任务而批量勾选；先列明未完成子任务，并确认它们是否确已完成且允许一并标记；仅“同意联动”不能替代完成事实。用户明确报告完成可作为来源注明的证据。
- 子任务重新打开：父任务也会重新打开。全部子任务完成可能自动完成父任务；info不暴露该设置，应预告这一可能影响并回读核对。普通子节点完成授权可涵盖软件固有的自动父完成；父目标另有验收未满足时，先讨论补验收节点，勿让联动虚报目标完成。
- 移动/重排父子结构：可能重新计算旧/新父任务完成状态；父日期变化会带动子日期。先get核对相关树，超出已知授权时确认。
- 仅一层子任务；有子节点的主任务不能直接当成另一个任务的子节点；不擅自展平或删除后重建。
- 删除前get读取目标和子任务，向用户列明影响取得确认。执行前再次比较；新增子项或对象/范围变化须重新确认。没有同范围变动不重复问。
- Skill管理的状态前缀：完成操作回读整个受影响树，移除已完成条目的三个受管前缀，保留正文。需要标题写入时读取最新revision；不要连带改动未授权的其他正文。

## 单个与批量写入

1. 根据最新读取确定ID、参数、授权及联动范围。
2. 为新操作生成UUID并保存完整请求；使用最新已观察到的revision。
3. 检查协议错误、isError和structuredContent中的业务错误，不能只看HTTP成功。
4. 成功后保存affectedIds与返回ID，回读受影响对象。成功回读的新revision可用于下一步；出现并发迹象时重新比较。
5. 创建树时先父后子，每一步用最新revision；创建历史已完成节点先建全树再按授权标完成，防止提前触发父完成；明确父目标验收节点。
6. 每一步都可部分失败。不要自动删父回滚，也不要整批重复执行；报告已成功、失败、待核实部分。

## 重试决策

| 结果 | 下一步 |
|---|---|
| 响应丢失/超时 | 先查询；完整原请求保存在本次会话操作记录（含工具、ID、全部参数、返回ID）中。无法证明回执仍在窗口内时不盲目重试；先核实对象，仍不明则停止并报告。只有窗口有效且原请求完整时可同ID同参数重试。 |
| CONFLICT | 重新读取并比较语义；仍获授权的新变更用新UUID，不只替换旧请求的revision。 |
| REQUEST_ID_REUSED | 停止该请求，检查本地记录，不盲目换ID重发。 |
| INVALID_ARGUMENT/OPERATION_FAILED | 核对schema和能力，必要时询问；不靠重复调用碰运气。 |
| 认证/网络失败 | 按连接指南排查，不切换直接数据文件写入。 |

成功回执仅保存最近128次写入，旧请求不能无限重试；很久以前的结果不明操作应先核实，不假定服务端仍能去重。删除回读NOT_FOUND仅验证目标消失；其他业务报错不算删除成功。结果不可核实时明确不确定。
