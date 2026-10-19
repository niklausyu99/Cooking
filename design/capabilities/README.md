# 项目级设计能力安装报告

核验日期：2026-10-19。当前 CLI：`codex-cli 0.159.2`。只安装到此仓库，未更改全局配置。

## 结果与运行时状态

- 新增 14 个完整 skill 目录；保留原有 `mobile-kitchen`，没有覆盖已有能力。
- 仅转换并注册指定的 10 个设计 agent，未安装 Agency 的其他 agent。
- Skills 按 SKILL.md 中的实际 name 命名，安装在 `.agents/skills/`。
- Agent 原文保存在 `.agents/design-agent-sources/`，Codex 配置层在 `.codex/agents/`，由 `.codex/config.toml` 的 `[agents.<role>]` 显式注册。角色配置只包含完整 `developer_instructions`；不带 Claude color、emoji、tools 等字段，也不覆写当前模型或工具权限。
- 完整目录、SHA-256、元数据名称、角色正文无损转换和注册路径已验证；项目配置与 10 个角色配置均通过官方 Codex JSON Schema 校验。
- **当前会话的自动发现／命名 agent 调用未验证成功。** 独立 Codex app-server 在当前只读主目录中无法完成启动；暂存 SQLite 与日志后仍遇到只读文件系统，诊断还指出祖先 `/workspace` 的项目配置需要可信项目状态。Skills 安装位置符合项目发现约定，但不能因此宣称本聊天已重新加载。
- 本聊天的 agent 工具没有命名 role 选择参数，所以这里可直接阅读并应用相关设计指导，不能冒称已经调用原生设计 agent。支持项目级配置的 Codex 在信任并重新加载仓库后方可验证激活；无需把 Markdown 改名当原生 agent。

## Skills 明细

所有目录均完整复制，包括原有 references、assets、scripts、demos（若存在）。版本以精确 Git commit 固定，不把浮动 main 当版本号。完整 SHA 和逐文件校验值见 `capabilities.lock.json`。

| 实际名称 | 来源 | 固定版本 | 项目路径 | 发现状态 |
|---|---|---|---|---|
| `design-taste-frontend` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/taste-skill) | `b9ca2fd8047f` | `.agents/skills/design-taste-frontend` | 文件与元数据已验证；当前会话热加载未确认 |
| `gpt-taste` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/gpt-tasteskill) | `b9ca2fd8047f` | `.agents/skills/gpt-taste` | 文件与元数据已验证；当前会话热加载未确认 |
| `high-end-visual-design` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/soft-skill) | `b9ca2fd8047f` | `.agents/skills/high-end-visual-design` | 文件与元数据已验证；当前会话热加载未确认 |
| `minimalist-ui` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/minimalist-skill) | `b9ca2fd8047f` | `.agents/skills/minimalist-ui` | 文件与元数据已验证；当前会话热加载未确认 |
| `industrial-brutalist-ui` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/brutalist-skill) | `b9ca2fd8047f` | `.agents/skills/industrial-brutalist-ui` | 文件与元数据已验证；当前会话热加载未确认 |
| `stitch-design-taste` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/b9ca2fd8047f4c72d7da90ebc1c1203e57c72cd2/skills/stitch-skill) | `b9ca2fd8047f` | `.agents/skills/stitch-design-taste` | 文件与元数据已验证；当前会话热加载未确认 |
| `imagegen-frontend-web` | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills/tree/beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e/skills/imagegen-frontend-web) | `beb16b0d0f4d` | `.agents/skills/imagegen-frontend-web` | 文件与元数据已验证；当前会话热加载未确认 |
| `imagegen-frontend-mobile` | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills/tree/beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e/skills/imagegen-frontend-mobile) | `beb16b0d0f4d` | `.agents/skills/imagegen-frontend-mobile` | 文件与元数据已验证；当前会话热加载未确认 |
| `brandkit` | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills/tree/beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e/skills/brandkit) | `beb16b0d0f4d` | `.agents/skills/brandkit` | 文件与元数据已验证；当前会话热加载未确认 |
| `image-to-code` | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills/tree/beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e/skills/image-to-code) | `beb16b0d0f4d` | `.agents/skills/image-to-code` | 文件与元数据已验证；当前会话热加载未确认 |
| `huashu-design` | [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design/tree/798c4235ebff03d5c45e3c8affdf5e9d18f9dfa7/.) | `3.0.0 / 798c4235ebff` | `.agents/skills/huashu-design` | 文件与元数据已验证；当前会话热加载未确认 |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/frontend-design) | `dbd4588f9e10` | `.agents/skills/frontend-design` | 文件与元数据已验证；当前会话热加载未确认 |
| `web-artifacts-builder` | [anthropics/skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/web-artifacts-builder) | `dbd4588f9e10` | `.agents/skills/web-artifacts-builder` | 文件与元数据已验证；当前会话热加载未确认 |
| `algorithmic-art` | [anthropics/skills](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/algorithmic-art) | `dbd4588f9e10` | `.agents/skills/algorithmic-art` | 文件与元数据已验证；当前会话热加载未确认 |

`gpt-taste`、`high-end-visual-design`、`minimalist-ui`、`industrial-brutalist-ui`、`stitch-design-taste` 为上游 opt-in 能力；按任务选用，避免互相冲突的风格规则同时主导。没有从 taste-skill 重复安装已迁移的生图占位 skill。

## Agents 明细

共同来源：[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)，固定 commit `652b2692f8d8ec2b1f1a38e559073e287dfdc469`。所有状态均为：**Codex 项目注册与配置格式已验证，当前宿主是否加载未确认**。

| 实际注册名称 | 原始显示名称 | Codex 项目路径 |
|---|---|---|
| `design-brand-guardian` | Brand Guardian | `.codex/agents/design-brand-guardian.toml` |
| `design-ui-designer` | UI Designer | `.codex/agents/design-ui-designer.toml` |
| `design-ux-architect` | UX Architect | `.codex/agents/design-ux-architect.toml` |
| `design-ux-researcher` | UX Researcher | `.codex/agents/design-ux-researcher.toml` |
| `design-ui-finish-gate-reviewer` | UI Finish-Gate Reviewer | `.codex/agents/design-ui-finish-gate-reviewer.toml` |
| `design-persona-walkthrough` | Persona Walkthrough Specialist | `.codex/agents/design-persona-walkthrough.toml` |
| `design-visual-storyteller` | Visual Storyteller | `.codex/agents/design-visual-storyteller.toml` |
| `design-image-prompt-engineer` | Image Prompt Engineer | `.codex/agents/design-image-prompt-engineer.toml` |
| `design-inclusive-visuals-specialist` | Inclusive Visuals Specialist | `.codex/agents/design-inclusive-visuals-specialist.toml` |
| `design-whimsy-injector` | Whimsy Injector | `.codex/agents/design-whimsy-injector.toml` |

## 未安装与原因

- `design-taste-frontend-v1`, `design-taste-frontend-v2-experimental`, `redesign-existing-projects`：Legacy/retired variants excluded for this new project.
- `react-artifact-builder`, `visual-art-canvas`, `website-intelligence`：Private local directory on /Users/wyh is absent in this cloud machine; no public source guessed.
- `council-rams`：Optional council plugin, not installed as a standalone skill.
- `tailwind-design-system`, `web-design-guidelines`, `visual-style`, `threejs-*`：Optional embedded references/3D modules not needed by this offline HTML app; no OpenMontage system installed.

本项目暂不需要 3D；OpenMontage 的参考条目没有启用，也没有安装其视频生产系统。私有的 3 个目录可在取得原文件后做完整目录安装，不猜测来源。

## 使用与依赖边界

- 主实现使用 `design-taste-frontend` 的 app-screen 路由和 `frontend-design`；其他 skill 是可调用选项，非所有规则叠加。
- 设备上已具备 Node 24、Python、Chromium、Python Playwright。主 taste skill 的 draw/lint/inspect 脚本可在此运行，无需包安装。
- imagegen 工具在当前聊天可用；安装生图 skill 不等于已生成设计图。
- Google Stitch MCP、Firecrawl MCP、Council 插件没有因此获得；没有声明它们可用。
- web-artifacts-builder 与 algorithmic-art 的框架／生成工具按将来实际调用的项目再安装依赖。当前离线 HTML 不引入 React、GSAP CDN 或 p5.js。
- `huashu-design` 完整保留上游 3.0.0 目录；未注册它附带的 hooks 或自动执行上游安装脚本。

## 复核

```bash
python3 scripts/verify_design_capabilities.py
```

只核验安装完整性与转换正确性，不把它当成真实 agent 执行验证。见 `runtime-discovery.json` 的实际探针结果。许可证原文存放在 `licenses/`；各 skill 内的独立许可证也已保留。
