# Claude Code 阶段化 AI Harness V4 — 最终方案

> 最终收敛版。本文档作为后续实施的唯一权威基线。

---

## 一、文档定位

本文档是所有前序方案文档的最终收敛。

核心决策：**stage-harness 是一个一体化的 Claude Code 插件**。用户只安装这一个插件，即可获得从模糊需求到可用交付物的端到端闭环能力。

stage-harness 在设计和实现层面**参考复用**以下成熟组件的思路与代码：

| 参考来源 | 内化什么 | 不做什么 |
|---------|---------|---------|
| **Flow-Next** | epic/task 模型、flowctl CLI、plan scouts、worker subagent、re-anchor、跨模型 review、Ralph 自治循环、memory | 不要求用户另装 Flow-Next |
| **Superpowers** | brainstorming 澄清方法、TDD/review 方法纪律 | 不要求用户另装 Superpowers |
| **ECC** | security-reviewer、audit、safety gate 的设计思路 | 不要求用户另装 ECC |

**一个插件，一条命令安装，满足所有诉求。**

---

## 二、最终主张

> **stage-harness** 是一个自包含的 Claude Code 插件，在接收到模糊需求后，自动完成需求澄清、规格定义、计划生成、开发执行、验证审查、交付发布的全流程推进。整个过程中只把极少数关键决策点交给人，其余全部自主完成。

核心特征：

1. **一个插件满足所有诉求**——安装 stage-harness 即获得完整能力
2. **接住模糊输入**——brainstorming + interview 自动澄清
3. **AI 自主判断**——决策分类机制区分"必须问人 / 可先假设 / 可延后"
4. **端到端交付**——从需求到代码 + 测试 + 交付包
5. **多角色议会**——4 类分层议会做多视角质量保障
6. **自治运行**——Ralph 模式支持 overnight 无人推进
7. **经验沉淀**——memory + 学习治理，可复用可复制

---

## 三、不可替换的机制层

以下机制是整个体系的骨架，不随实现方式变化：

### 3.1 PLAN 是后半程控制中心

后半程主链：`PLAN → EXECUTE → VERIFY → FIX → DONE`

硬规则：
- EXECUTE 发现切分失效 → 必须回流 PLAN
- EXECUTE 发现依赖不成立 → 必须回流 PLAN
- 不允许"计划之外的临场扩写"静默混入

### 3.2 Decision Bundle + 决策分类

在关键阶段出口收束决策。AI 主动判断哪些可先假设推进，只把真正无法自主决策的问题交给人。

| 分类 | 处理方式 | 示例 |
|------|---------|------|
| **must_confirm** | 阻断，等人拍板 | 目标用户是内部还是外部？ |
| **assumable** | AI 假设推进，记录依据，**不阻断** | 数据库默认用 PostgreSQL |
| **deferrable** | 不阻塞当前阶段，标记后续确认 | 日志格式的具体字段定义 |

自动放行规则：
- Decision Bundle 全部为 assumable / deferrable → **自动放行**
- Decision Bundle 有 must_confirm → 阻断
- 议会 verdict = GO / PASS / READY / RELEASE_READY → **自动放行**
- 议会 verdict = REVISE / HOLD / BLOCK → 阻断

### 3.3 分层议会（不可降级的核心机制）

| 议会类型 | 阶段 | 规模 | 关注重点 |
|---------|------|------|---------|
| 轻议会 | SPEC | 3~5 | 漏项、冲突、隐含假设 |
| 计划议会 | PLAN | 5~7 | 覆盖、切分、依赖、风险 |
| 验收议会 | VERIFY | 5~7 | 代码质量、安全、测试 |
| 发布议会 | DONE | 3~4 | 交付完整性、安全签署 |

### 3.4 阶段门禁 + 可审查 / 可阻断 / 可回退

每个阶段出口有结构化检查，不合格则阻断，出问题可回退。

---

## 四、架构 — 一体化插件

```
┌────────────────────────────────────────────────────────────────────┐
│                     stage-harness（一体化插件）                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  阶段编排引擎                                                  │  │
│  │  状态机 · 阶段门禁 · Decision Bundle · 决策分类 · 自动放行       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  需求澄清（参考 Superpowers）                                  │  │
│  │  brainstorming skill · interview skill · 决策分类引擎          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  计划与执行引擎（参考 Flow-Next）                               │  │
│  │  epic/task 模型 · flowctl CLI · plan(scouts) · work(worker)   │  │
│  │  · re-anchor · 依赖图 · evidence · 原子提交                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  分层议会引擎                                                  │  │
│  │  轻议会 · 计划议会 · 验收议会 · 发布议会                         │  │
│  │  reviewer agent 并行调度 · 裁决汇总 · 动态规模控制               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Review 引擎（参考 Flow-Next + ECC）                           │  │
│  │  跨模型技术 review · 安全扫描 · spec compliance 审查            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  自治引擎（参考 Ralph）                                        │  │
│  │  自治循环 · hooks guard · receipts · 可暂停/恢复               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  学习与沉淀                                                    │  │
│  │  memory（pitfalls/conventions/decisions） · 经验提名 · 晋升治理 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  底座：Claude Code 原生能力                                        │
│  hooks · subagents · agent teams · rules / skills / MCP            │
└────────────────────────────────────────────────────────────────────┘
```

### 与前序方案的差异

| 维度 | V3 | V4 前版 | V4 本版 |
|------|-----|--------|--------|
| 用户需要安装 | stage-harness + Flow-Next + Superpowers + ECC | Flow-Next + Superpowers（MVP-0），stage-harness（MVP-1+） | **stage-harness 一个插件** |
| stage-harness 定位 | 编排外壳 | 治理增强层 | **一体化插件**（内化全部能力） |
| Flow-Next 的角色 | 目标态优先主干 | 全流程执行引擎 | **参考来源**（内化其设计） |
| Superpowers 的角色 | 前半程方法学 | CLARIFY 主力 | **参考来源**（内化其方法） |
| ECC 的角色 | 治理精选子集 | 安全与质量层 | **参考来源**（内化安全审查） |

---

## 五、参考复用策略

### 5.1 从 Flow-Next 内化什么

Flow-Next（v0.26.1）是一个高度成熟的系统。stage-harness 参考其设计和实现，内化以下能力：

| 能力 | Flow-Next 原实现 | stage-harness 内化方式 |
|------|-----------------|---------------------|
| **epic/task 模型** | `.flow/` 目录 + flowctl CLI | 复用 epic/task JSON 格式 + 自建或 fork flowctl |
| **plan 生成** | `/flow-next:plan`（并行 scouts 调研） | 内化为 `/harness:plan` skill，保留 scouts 并行机制 |
| **任务执行** | `/flow-next:work`（worker subagent + re-anchor） | 内化为 `/harness:work` skill，保留 worker 隔离 + re-anchor |
| **跨模型 review** | impl-review / plan-review（RepoPrompt/Codex/Export） | 内化为 `/harness:review` skill |
| **interview** | `/flow-next:interview`（深度 Q&A） | 内化为 `/harness:interview` skill |
| **依赖管理** | `flowctl dep` / `ready` / `next` | 直接复用 flowctl 或内建等价 CLI |
| **自治循环** | Ralph（hooks + guard + receipts） | 内化为 `/harness:auto` skill，保留 guard + receipts |
| **memory** | `flowctl memory`（pitfalls/conventions/decisions） | 直接复用或内建等价能力 |
| **worktree** | `worktree.sh`（多分支隔离） | 复用脚本 |

### 5.2 从 Superpowers 内化什么

| 能力 | Superpowers 原实现 | stage-harness 内化方式 |
|------|-------------------|---------------------|
| **brainstorming** | brainstorming skill（发散式探索） | 内化为 `/harness:clarify` skill 的前半段 |
| **TDD 方法纪律** | TDD + review 方法约束 | 内化为 EXECUTE 阶段的 skill 规则 |
| **执行纪律** | plan discipline | 内化为 PLAN/EXECUTE 的 skill 规则 |

### 5.3 从 ECC 内化什么

| 能力 | ECC 原实现 | stage-harness 内化方式 |
|------|----------|---------------------|
| **安全审查** | security-reviewer agent | 内化为验收议会的安全 reviewer 角色 |
| **audit** | 审计记录能力 | 内化为 `.harness/` 的结构化审计日志 |
| **safety gate** | 安全门禁 | 内化为阶段门禁的安全检查项 |

---

## 六、stage-harness 插件结构

```
stage-harness/
├── .claude-plugin/
│   └── plugin.json                      # 插件 manifest
│
├── commands/                            # slash 命令入口
│   ├── harness-start.md                 # 启动全流程（从模糊需求开始）
│   ├── harness-clarify.md               # 需求澄清
│   ├── harness-spec.md                  # 规格定义
│   ├── harness-plan.md                  # 计划生成
│   ├── harness-work.md                  # 开发执行
│   ├── harness-review.md                # 审查（技术 + 议会）
│   ├── harness-auto.md                  # 自治模式（类 Ralph）
│   ├── harness-status.md                # 查看当前状态
│   └── harness-done.md                  # 交付与沉淀
│
├── agents/                              # subagent 定义
│   ├── brainstormer.md                  # 需求澄清（参考 Superpowers）
│   ├── interviewer.md                   # 深度 Q&A（参考 Flow-Next interview）
│   ├── repo-scout.md                    # 代码库调研（参考 Flow-Next）
│   ├── docs-scout.md                    # 文档调研（参考 Flow-Next）
│   ├── practice-scout.md                # 最佳实践调研（参考 Flow-Next）
│   ├── context-scout.md                 # 上下文聚合（参考 Flow-Next）
│   ├── worker.md                        # 任务执行器（参考 Flow-Next worker）
│   ├── plan-sync.md                     # 计划同步（参考 Flow-Next）
│   ├── spec-reviewer.md                 # 轻议会 reviewer
│   ├── plan-reviewer.md                 # 计划议会 reviewer
│   ├── code-reviewer.md                 # 验收议会 - 代码质量
│   ├── logic-reviewer.md                # 验收议会 - 业务逻辑
│   ├── security-reviewer.md             # 验收议会 - 安全（参考 ECC）
│   ├── test-reviewer.md                 # 验收议会 - 测试质量
│   ├── impact-reviewer.md               # 验收议会 - 影响范围
│   ├── release-reviewer.md              # 发布议会 reviewer
│   └── quality-auditor.md               # 质量审计（参考 Flow-Next）
│
├── skills/                              # 技能定义
│   ├── clarify/SKILL.md                 # 需求澄清流程
│   ├── spec/SKILL.md                    # 规格生成流程
│   ├── plan/SKILL.md                    # 计划生成流程（含 scouts 并行）
│   │   ├── steps.md
│   │   └── examples.md
│   ├── work/SKILL.md                    # 执行流程（worker + re-anchor）
│   │   └── phases.md
│   ├── council/SKILL.md                 # 议会调度与裁决汇总
│   ├── review/SKILL.md                  # 技术 review（跨模型）
│   ├── decision-bundle/SKILL.md         # 决策分类与 bundle 管理
│   ├── stage-gate/SKILL.md              # 阶段门禁规则
│   ├── auto/SKILL.md                    # 自治循环管理
│   ├── memory/SKILL.md                  # 经验沉淀与检索
│   └── worktree/SKILL.md               # 工作树隔离
│
├── hooks/
│   ├── hooks.json                       # Hook 事件注册
│   ├── stage-init.sh                    # SessionStart：加载状态
│   ├── stage-gate-check.sh              # Stop：阶段门禁检查
│   ├── stage-reminder.sh                # UserPromptSubmit：阶段提醒
│   └── auto-guard.py                    # 自治模式 guard（参考 Ralph）
│
├── scripts/
│   ├── flowctl                          # CLI 工具（复用/fork Flow-Next flowctl）
│   ├── flowctl.py                       # CLI 实现
│   ├── council-runner.sh                # 议会启动与汇总
│   ├── decision-bundle.sh               # Decision Bundle 生成
│   └── verify-artifacts.sh              # 产物完整性检查
│
├── templates/
│   ├── epic-spec.md                     # Epic spec 模板
│   ├── task-spec.md                     # Task spec 模板
│   ├── decision-bundle.json             # Decision Bundle 模板
│   ├── council-verdict.json             # 议会裁决模板
│   ├── delivery-summary.md              # 交付总结模板
│   └── release-notes.md                 # 发布说明模板
│
└── docs/
    ├── quick-start.md                   # 快速开始指南
    └── flowctl.md                       # CLI 参考
```

---

## 七、命令体系

| 命令 | 功能 | 阶段 |
|------|------|------|
| `/harness:start {模糊需求}` | 从模糊需求启动全流程，自动走 CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → DONE | 全流程 |
| `/harness:clarify {模糊需求}` | 需求澄清（brainstorming + interview + 决策分类） | CLARIFY |
| `/harness:spec {epic-id}` | 规格定义（epic 创建 + 精炼 + 轻议会） | SPEC |
| `/harness:plan {epic-id}` | 计划生成（scouts 并行调研 + task 图谱 + 计划议会） | PLAN |
| `/harness:work {epic-id 或 task-id}` | 开发执行（worker + re-anchor + 原子提交） | EXECUTE |
| `/harness:review {epic-id}` | 审查（跨模型技术 review + 验收议会） | VERIFY |
| `/harness:auto {epic-id}` | 自治模式（自动循环 plan → work → review → done） | 全流程自治 |
| `/harness:status` | 查看当前 epic/task 状态、阶段进度、Decision Bundle 状态 | 任意 |
| `/harness:done {epic-id}` | 交付（发布议会 + 交付包 + 经验沉淀） | DONE |

**`/harness:start` 是核心入口**——用户丢进一段模糊需求，插件自动走完全流程。等同于依次调用 clarify → spec → plan → work → review → done，中间只在 must_confirm 的 Decision Bundle 处暂停等人。

---

## 八、状态机与阶段流转

### 8.1 主状态机

```
IDEA → CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE
                                       ↑        │
                                       └────────┘
```

### 8.2 状态管理

stage-harness 自己管理全部状态，使用内化的 flowctl 作为 CLI 工具：

```
.harness/
├── config.json                     # 全局配置
├── features/{epic-id}/
│   ├── state.json                  # 阶段状态（currentStage + 历史）
│   ├── handoff.md                  # Session 接力摘要（进度 + 下一步 + 关键上下文）
│   ├── decision-bundles/           # 各阶段 Decision Bundle
│   ├── councils/                   # 议会报告与裁决
│   ├── risk-assessment.json        # 风险评估
│   └── eval/metrics.json           # 量化指标
├── epics/{epic-id}.json            # epic 元数据
├── specs/{epic-id}.md              # epic 规格
├── tasks/{epic-id}.{n}.json        # task 元数据（依赖、状态、evidence）
├── tasks/{epic-id}.{n}.md          # task 规格
├── memory/                         # 经验沉淀
│   ├── pitfalls.md
│   ├── conventions.md
│   └── decisions.md
└── templates/                      # 模板
```

### 8.3 Session 恢复与 Handoff

长流程必然跨越多个 Claude Code session（token 耗尽、网络中断、手动退出）。stage-harness 必须支持断点续做：

**自动恢复**：`stage-init.sh`（SessionStart hook）检测 `.harness/features/` 是否有进行中的 epic，如果有则：
1. 读取 `handoff.md` 恢复上下文
2. 提示用户当前进度（"Epic fn-3 处于 EXECUTE 阶段，已完成 4/7 个 task"）
3. 询问是否继续

**自动保存**：每个阶段完成时自动写入 `handoff.md`：

```markdown
## 当前状态
- Epic: fn-3-user-auth
- 阶段: EXECUTE
- 进度: 4/7 tasks 完成

## 下一步
- 执行 task fn-3.5（用户权限校验）

## 关键上下文
- 使用 JWT + RBAC 方案（Decision D-CLARIFY-02 已确认）
- 数据库用 PostgreSQL（假设推进，未被推翻）
```

### 8.4 上下文窗口管理

全流程产物量大，不可能全部加载到 LLM 上下文中。每个阶段只加载当前相关 artifacts：

| 阶段 | 加载 | 不加载 |
|------|------|--------|
| CLARIFY | 原始需求文本 | 无 |
| SPEC | clarification-notes + decision-bundle | 上游对话 |
| PLAN | epic spec（specs/*.md） | 原始需求、CLARIFY 细节 |
| EXECUTE | 当前 task spec + epic spec 摘要 | 其他 task、议会报告 |
| VERIFY | epic spec + 全量 diff + task evidence | 执行过程细节 |
| DONE | verification.json + delivery-summary 模板 | 执行过程 |

**原则**：每个阶段的输入是上一阶段的 artifacts，不是完整对话上下文。re-anchor 机制从 EXECUTE 扩展到所有阶段——每进入新阶段都重新锚定相关上下文。

---

## 九、各阶段设计

### 9.0 需求入口标准化

模糊需求直接作为 `/harness:start` 或 `/harness:clarify` 的输入。插件内部自动做格式化：

> 将输入整理为：1. 一句话目标；2. 已知约束；3. 期望交付物。信息不足标注"待澄清"。

### 9.1 CLARIFY — 需求澄清

| 项目 | 内容 |
|------|------|
| **工作流** | 1. brainstorming（发散探索）→ 2. interview（收敛精炼）→ 3. 决策分类 → 4. Decision Bundle |
| **产物** | `clarification-notes.md`、`decision-bundle.json` |
| **出口** | must_confirm 项已拍板；assumable 项已记录假设依据 |

**决策分类判断规则**（AI 凭什么判断一个决策属于哪个分类）：

| 条件 | 分类 | 依据 |
|------|------|------|
| 涉及业务方向选择（to B / to C / 定价 / 目标客群） | must_confirm | 业务决策不能由 AI 代拍 |
| 涉及合规 / 法律 / 安全红线 | must_confirm | 风险不可逆 |
| 涉及不可逆的技术选型（如主语言 / 主框架） | must_confirm | 变更成本极高 |
| 有行业惯例 + 项目上下文支撑 + 后续可纠正 | assumable | 可假设推进 |
| 属于实现细节 + 不影响架构 + 后续可改 | deferrable | 不阻塞主线 |
| AI 对分类没有信心时 | must_confirm | **宁可多问一次，也不偷偷拍板** |

Decision Bundle 结构：

```json
{
  "id": "D-CLARIFY-01",
  "question": "数据库选型",
  "classification": "assumable",
  "assumption": "默认 PostgreSQL",
  "assumption_basis": "团队现有技术栈 + 无特殊性能要求",
  "override_needed_by": "PLAN",
  "human_decision": null
}
```

**典型场景暂停次数预估**（用户最关心的"我到底会被打断几次"）：

| 风险等级 | 预估暂停次数 | 暂停位置 |
|---------|-----------|---------|
| 低风险 | **0~1 次** | 可能仅在 VERIFY→DONE 做最终确认 |
| 中风险 | **1~2 次** | PLAN→EXECUTE + VERIFY→DONE |
| 高风险 | **2~3 次** | CLARIFY + PLAN→EXECUTE + VERIFY→DONE |

### 9.2 SPEC — 规格定义

| 项目 | 内容 |
|------|------|
| **工作流** | 1. epic 创建 → 2. 写入规格（epic spec） → 3. interview 精炼 → 4. 轻议会审查 → 5. Decision Bundle |
| **产物** | `.harness/specs/{epic-id}.md`、`decision-bundle.json` |
| **出口** | 轻议会 verdict = GO + Decision Bundle 已处理 |

Epic spec 模板：

```markdown
# {Epic Title}

## Goal & Context
## Architecture & Data Models
## API Contracts
## Edge Cases & Constraints
## Acceptance Criteria
## Boundaries
## Decision Context
## Test Strategy
## Risk Register
```

### 9.3 PLAN — 实施计划

| 项目 | 内容 |
|------|------|
| **工作流** | 1. 并行 scouts 调研（repo-scout + docs-scout + practice-scout + context-scout）→ 2. 生成 task 图谱（依赖排序）→ 3. 技术 plan-review → 4. 计划议会 → 5. Decision Bundle |
| **产物** | `.harness/tasks/*.json + *.md`（task 图谱）、`plan-council-verdict.json` |
| **出口** | plan-review 通过 + 计划议会 verdict ≠ BLOCK + Decision Bundle 已处理 |

### 9.4 EXECUTE — 开发执行

| 项目 | 内容 |
|------|------|
| **工作流** | 1. 获取可执行 task（依赖排序）→ 2. worker subagent 在 re-anchor 后实现 → 3. 原子提交 + evidence 记录 → 4. 循环直到全部完成 |
| **产物** | 代码、测试、evidence（commits / tests / PRs）、git 原子提交 |
| **内循环** | re-anchor → 实现 → 测试 → 提交 → 下一个 task |

### 9.5 VERIFY — 验证与审查

| 项目 | 内容 |
|------|------|
| **工作流** | 1. 跨模型技术 review → 2. spec compliance 审查 → 3. 安全审查 → 4. 验收议会 |
| **产物** | review 结果、`verification.json`、安全报告 |
| **出口** | 技术 review SHIP + 验收议会 PASS |

三层 review：

| 层 | 关注 | 方式 |
|----|------|------|
| 技术 review | 代码质量、逻辑正确性 | 跨模型（Claude 实现 → GPT 审查） |
| Spec compliance | 实现与规格的一致性 | 自动 |
| 治理 review | 安全、团队标准、影响范围 | 多角色验收议会（5~7 reviewer） |

### 9.6 FIX — 问题修复

review → fix 循环。最多 3 轮，超出升级人工。

### 9.7 DONE — 交付与沉淀

| 项目 | 内容 |
|------|------|
| **工作流** | 1. 发布议会 → 2. 生成交付包 → 3. 经验提名 → 4. 人工审核后晋升 |
| **产物** | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` |
| **出口** | 发布议会 verdict = RELEASE_READY |

---

## 十、分层议会详细设计

分层议会是**不可降级的核心机制**。

### A 类：轻议会（SPEC 出口）

| 项目 | 内容 |
|------|------|
| **规模** | 3~5 reviewer subagent |
| **角色** | 规格完整性、一致性、可落地性、可测试性（可选）、安全约束（按需） |
| **裁决** | `GO` / `REVISE` / `HOLD` |
| **输出** | `spec-council-report.md`、`spec-council-verdict.json` |

### B 类：计划议会（PLAN 出口）

| 项目 | 内容 |
|------|------|
| **规模** | 5~7 reviewer subagent |
| **角色** | 覆盖性、任务切分、依赖路径、测试策略、架构承接、安全风险、回滚（按需） |
| **核心问题** | 需求全覆盖？task 边界清晰？依赖无循环？高风险有缓解？冷启动可执行？ |
| **裁决** | `READY` / `READY_WITH_CONDITIONS` / `BLOCK` |
| **输出** | `plan-council-report.md`、`plan-council-verdict.json` |

### C 类：验收议会（VERIFY 出口）

| 项目 | 内容 |
|------|------|
| **规模** | 5~7 reviewer subagent |
| **角色** | 代码质量、业务逻辑、安全、测试质量、nil/null safety、影响范围、死代码 |
| **裁决** | `PASS` / `FAIL` |
| **输出** | `review-report.md`、`test-report.md`、`verification.json` |

### D 类：发布议会（DONE 出口）

| 项目 | 内容 |
|------|------|
| **规模** | 3~4 reviewer subagent |
| **角色** | Release readiness、Security signoff、Delivery/docs、Learning governance |
| **裁决** | `RELEASE_READY` / `RELEASE_WITH_CONDITIONS` / `NOT_READY` |
| **输出** | `release-council-report.md`、`release-council-verdict.json` |

### 裁决汇总逻辑

| 策略 | 适用 | 规则 |
|------|------|------|
| 多数决 | 轻议会、发布议会 | >50% 同意则放行 |
| 一票否决 | 安全相关 | 安全 reviewer FAIL 则整体 FAIL |
| 加权多数 | 计划议会、验收议会 | 覆盖性/安全权重 2x，其他 1x |

---

## 十一、动态强度控制

根据风险等级调整流程重量——**议会始终存在**，只调规模：

| 控制维度 | 低风险 | 中风险 | 高风险 |
|---------|-------|-------|-------|
| CLARIFY | 可跳过 brainstorming | brainstorming + interview | 完整 brainstorming + 深度 interview |
| 轻议会 | 3 reviewer | 3 reviewer | 5 reviewer |
| Plan depth | short | standard | deep |
| 计划议会 | 3 reviewer | 5 reviewer | 7 reviewer |
| EXECUTE 模式 | 自治（auto） | worker + review | worker + review + 人工检查点 |
| 验收议会 | 3 reviewer | 5 reviewer | 7 reviewer |
| 发布议会 | 2 reviewer | 3 reviewer | 4 reviewer |
| Decision Bundle | 仅 PLAN→EXECUTE | 全部触发点 | 全部触发点 + 额外检查点 |

---

## 十二、自治模式

`/harness:auto {epic-id}` 启动全流程自治循环：

```
clarify → spec → plan → [议会] → work(task1) → work(task2) → ... → review → [议会] → done
```

- 低风险 feature 可全程自治（hooks + guard + receipts）
- 中风险 feature 在关键节点（PLAN→EXECUTE、VERIFY→DONE）暂停等人确认
- 高风险 feature 不启用自治
- guard hooks 注入 token 预算检查和安全防护
- 所有运行记录保存在 `.harness/features/{epic-id}/runs/`

---

## 十三、经验沉淀与复制

三层沉淀模型：

| 层 | 存储 | 内容 | 生命周期 |
|----|------|------|---------|
| 项目级 | `.harness/memory/` | 当前项目的 pitfalls / conventions | 项目结束时归档 |
| 团队级 | CLAUDE.md / rules | 团队通用的工程约定 | 长期维护，定期清理 |
| 个人级 | 本地配置 | 个人偏好 | 个人维护 |

晋升路径：项目经验 → DONE 阶段 learning-candidates.md → 人工审核 → 团队规则

清理策略：团队规则不超过 30 条，每季度 review。

---

## 十四、失败路径设计

| 场景 | 处理 |
|------|------|
| 需求不可行 | CLARIFY 输出 `not-feasible` + 原因，终止 |
| 技术方案不成立 | 计划议会 BLOCK，回流 SPEC 或终止 |
| 外部依赖不可用 | task 标记 `blocked`，等待解除 |
| Epic 被取消 | 标记关闭，保留产物 |
| Token 预算耗尽 | 暂停，保存进度，等恢复 |
| 自治循环异常 | guard hooks 暂停，输出错误报告 |

---

## 十五、MVP 路线

### MVP-1：最小闭环（一个插件跑通全流程）

**目标**：安装 stage-harness 一个插件，用 `/harness:start` 从模糊需求跑通到代码交付。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 1.1 | 创建 stage-harness 插件骨架 | 插件可被 Claude Code 识别加载 |
| 1.2 | 内化 flowctl CLI（fork 或复用 Flow-Next） | epic/task CRUD + 依赖管理 + 状态管理可用 |
| 1.3 | 实现 `/harness:clarify`（内化 brainstorming + interview） | 模糊需求可产出 clarification-notes + decision-bundle |
| 1.4 | 实现决策分类（must_confirm / assumable / deferrable） | AI 能区分哪些问题值得问人 |
| 1.5 | 实现 `/harness:spec`（epic 创建 + 规格写入 + interview 精炼） | epic spec 可生成 |
| 1.6 | 实现 `/harness:plan`（scouts 并行调研 + task 图谱生成） | task 图谱可生成，含依赖排序 |
| 1.7 | 实现 `/harness:work`（worker subagent + re-anchor + 原子提交） | 代码 + 测试 + evidence 可产出 |
| 1.8 | 实现轻议会（SPEC 出口，3~5 reviewer） | reviewer subagent 并行审查，输出 verdict |
| 1.9 | 实现计划议会（PLAN 出口，5~7 reviewer） | 多角色审查 task 图谱 |
| 1.10 | 实现验收议会（VERIFY 出口，5~7 reviewer） | 多角色审查实现结果 |
| 1.11 | 实现议会裁决汇总 | 多数决 + 安全一票否决 |
| 1.12 | 实现阶段门禁 + 自动放行 | must_confirm 阻断 + 议会 PASS 自动放行 |
| 1.13 | 实现 FIX 轮次控制 | 最多 3 轮后升级 |
| 1.14 | 实现 `/harness:start`（全流程串联） | 一条命令跑通全流程 |

### MVP-2：发布 + 自治 + 安全

**目标**：完成 DONE 阶段 + 自治模式 + 安全审查。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 2.1 | 实现发布议会 | 交付完整性审查 |
| 2.2 | 实现 `/harness:done`（交付包生成） | release-notes + delivery-summary |
| 2.3 | 实现 `/harness:auto`（自治循环） | 低风险 feature 可自治运行 |
| 2.4 | 实现安全 reviewer（参考 ECC） | 安全报告可产出 |
| 2.5 | 实现动态强度控制 | 按风险等级调整议会规模 |
| 2.6 | 实现跨模型技术 review（RepoPrompt/Codex/Export） | Claude 实现 → GPT 审查 |

### MVP-3：学习 + 度量 + 增强

**目标**：经验沉淀 + 量化度量 + 高级增强。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 3.1 | 实现 memory（pitfalls/conventions/decisions） | 经验可沉淀和检索 |
| 3.2 | 实现学习治理流程 | 项目经验 → 人工审核 → 团队规则 |
| 3.3 | 实现 Eval 数据面 | token / latency / outcome 指标 |
| 3.4 | 实现 adversarial-spec 增强（可选） | 多模型对抗式规格补盲 |

---

## 十六、关键风险与缓解

| 风险 | 缓解 |
|------|------|
| **内化 Flow-Next 工作量大** | fork flowctl.py + 复用 skill/agent markdown，不从零开始 |
| **议会 token 成本高** | 动态强度控制（低风险 3 reviewer，高风险 7 reviewer） |
| **自治模式安全风险** | guard hooks + token 预算 + 关键节点人工检查点 |
| **单插件体量过大** | 按 skill 模块化，按需加载；命令可独立使用 |
| **与 Flow-Next 上游更新同步** | 记录 fork 基线版本，定期合并上游改进 |
| **memory 过早引入** | MVP-3 再加，MVP-1/2 用纯文件 |

---

## 十七、超短摘要

- **一个插件**：stage-harness，安装即用
- **内化能力**：Flow-Next（执行引擎）+ Superpowers（澄清方法）+ ECC（安全审查）
- **核心机制**：PLAN 控制中心 + Decision Bundle + 分层议会 + 阶段门禁
- **决策分类**：must_confirm / assumable / deferrable，最小化人工打断
- **自动放行**：议会 PASS + assumable 自动推进
- **自治模式**：低风险 feature 可全程自治
- **经验沉淀**：项目级 → 团队级三层模型

---

## 十八、结论

V4 最终形态是**一个自包含的 Claude Code 插件**——用户安装 stage-harness 后，丢进一段模糊需求，插件自动完成从需求澄清到代码交付的全流程。

它内化了 Flow-Next 的执行引擎、Superpowers 的澄清方法、ECC 的安全审查，但用户不需要知道也不需要安装这些外部组件。

全流程中只有 `must_confirm` 的 Decision Bundle 会暂停等人拍板。其他所有环节——包括议会审查——只要 verdict 为通过就自动推进。

这直接回应了原始诉求：

> **面对模糊需求，AI 自主完成从需求澄清到交付的端到端推进；只有真正必须由人拍板的极少数决策点才会打断流程；其余全部自动推进并最终输出可用成果。**
