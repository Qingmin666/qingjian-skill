# 轻笺 Skill

将当前工作整理为轻笺任务，规划每日工作，并在授权范围内同步项目关键节点与下一步。

## 安装

将 `skills/qingjian` 整个目录安装到客户端支持的技能目录。Codex Windows用户技能目录通常为 `%USERPROFILE%\.codex\skills\qingjian`；Claude Code通常为 `~/.claude/skills/qingjian`。其他客户端须支持SKILL.md或使用其正式导入方式，目录约定不代表已完成兼容测试。

先配置轻笺MCP，再重新加载客户端并调用qingjian_info。Skill不会自动赋予MCP权限。配置指南见技能内references/client-setup.md。不要上传个人令牌或软件数据。

## 使用

- “把我们正在讨论的分析加入轻笺。”
- “帮我规划明天，确认后写入轻笺。”
- “同步这个项目进度。”
- “这个项目做到哪了，下一步做什么？”

复杂结构先预览，删除二次确认。细节留在项目对话与交接文档。

## 验证范围

当前Windows客户端已完成轻笺MCP真实任务新增与回读。Skill本身的静态验证、脚本测试与模拟场景评估独立记录；不将接口验收等同于所有Skill分支或其他客户端已通过实测。仓库不包含软件本体，不自动开放远程访问。

## Windows 本机安装

在仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install-Skill.ps1 -Client codex
```

或用 `-Client claude-code` 安装到 Claude Code 技能目录。脚本不覆盖已有同名目录，也不修改 MCP 配置；自定义 `-Destination` 必须指向名为 qingjian 的目录。安装后重新加载客户端，再用 `$qingjian` 验证是否已加载。

Skill 指令本身兼容支持 SKILL.md 的 Agent；目录安装方式和 MCP 客户端功能须分别验收。软件接口、技能文件、客户端加载是三个不同的验证环节。
