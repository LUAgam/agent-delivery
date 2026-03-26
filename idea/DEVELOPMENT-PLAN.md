# Stage-Harness 开发方案

> 基于 `final-plan-v2.md`、`harness.md`、`final-plan-v2-supplements.md` 及仓库内全部前序文档与组件源码，输出的**可落地开发方案**。

---

## 一、文档定位与前序关系

本文档是对前序所有设计文档的最终收敛，定位为**实施级开发方案**——不再讨论"要不要做"，而是回答"怎么做、用什么做、分几步做、产出什么"。

与前序文档的关系：

| 文档 | 定位 | 本文档继承内容 |
|------|------|---------------|
| `0.md` | 初始调研与候选方案评分 | 三层/四层架构思想、候选组件评分结论 |
| `1.md` | 平替与补充候选深度调研 | Deep Trilogy 替换/增强 PLAN→EXECUTE 的决策、aio-reflect 持续学习补强 |
| `2.md` | 综合分析与融合方案 | Decision Bundle 机制、质量门禁设计、钩子脚本模板 |
| `end.md` | 融合落地方案初版 | "少打断、硬门禁、Decision Bundle、阶段产物"核心精神 |
| `end-revised.md` | 修订版（贴近代码现实） | 四层架构、职责边界、组件裁剪清单、MVP 分步策略 |
| `final-plan.md` | 最终选择方案（含代码验证） | 桥接技术规格、两层审查模型、Hooks 验证状态、插件目录结构 |
| `final-plan-v2.md` | 最终修订版 V2（主版本） | PLAN 作为控制中心、四类分层议会模板、状态机定义、阶段门禁规则 |
| `final-plan-v2-supplements.md` | V2 补充建议 | 组件能力裁剪清单、桥接技术规格、两层审查模型、Hooks 验证表、插件结构 |
| `harness.md` | Harness Engineering 补强 | Session Handoff、运行时 Evaluator、持续验证前移、Eval Harness 数据面、动态强度控制 |

本文档将上述内容统一收敛为一份**可执行的开发方案**。

---

## 二、目标系统概述

### 2.1 一句话定义

构建一个名为 `stage-harness` 的 Claude Code 插件，作为编排外壳，将澄清、规格、计划、执行、验收、发布组织成一条**阶段化流水线**，通过状态文件、Decision Bundle、分层议会和阶段门禁确保每个环节可审查、可阻断、可回退、可交付。

### 2.2 核心组件分工

```
CLARIFY   → Superpowers（仅 brainstorming）
SPEC      → ShipSpec（PRD / SDD / TASKS）
PLAN      → bridge + deep-plan（bridge-spec → plan / tdd / sections）
EXECUTE   → deep-implement（section 级 TDD + 内置审查）
VERIFY    → Ring（7 路并行 reviewer 验收议会）
GOVERN    → ECC 子集 + aio-reflect（治理审计 + 经验提炼）
```

### 2.3 四层架构

```
┌──────────────────────────────────────────────────────────────────┐
│  L1. 编排层 Orchestration                                        │
│      stage-harness 插件                                          │
│      状态机 · Decision Bundle · 阶段门禁 · 议会调度              │
├──────────────────────────────────────────────────────────────────┤
│  L2. 产物生成层 Spec & Plan                                      │
│      Superpowers(brainstorming) → ShipSpec(PRD/SDD/TASKS)        │
│      → bridge-spec → deep-plan(plan/tdd/sections)                │
├──────────────────────────────────────────────────────────────────┤
│  L3. 执行与验证层 Execute & Verify                               │
│      EXECUTE: deep-implement(section 级 TDD + 实现级审查)         │
│      VERIFY:  Ring 7-reviewer 验收议会                            │
├──────────────────────────────────────────────────────────────────┤
│  L4. 治理与学习层 Govern & Learn                                  │
│      ECC 子集(安全/治理) + aio-reflect(经验提名)                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 状态机

```
IDEA → CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE
                                           ↑        │
                                           └────────┘

可选前置：DISCOVER → CLARIFY
```

---

## 三、组件能力裁剪清单

**核心原则**：每个组件只保留其"最强职责"，显式禁用与其他组件重叠的能力，防止自动触发导致职责越界。

| 组件 | 保留职责 | 显式禁用 | 禁用原因 |
|------|---------|---------|---------|
| **Superpowers** | `brainstorming` 技能 | `writing-plans`、`executing-plans`、`subagent-driven-development`、`requesting-code-review` 的自动触发 | 后续链路自动触发会与 deep-plan/deep-implement 冲突 |
| **ShipSpec** | `/feature-planning` → PRD/SDD/TASKS | `/implement-task`、`/implement-feature`、Stop 钩子（Ralph Loop 的 task-loop-hook、feature-retry-hook、planning-refine-hook） | 执行主循环由 deep-implement 承担 |
| **deep-plan** | `/deep-plan` → research / interview / review / TDD / sections | — | 全量保留 |
| **deep-implement** | `/deep-implement` → TDD 实现 + 内置 code-reviewer + 原子提交 | — | 全量保留 |
| **Ring** | `/ring:codereview` 7 路并行审查 | `pm-team`（15 规划技能与 ShipSpec 重叠）、`dev-team` 的 `dev-cycle`（10 门控开发流与 deep-implement 重叠）、`pmo-team`、`finops-team` | 仅保留 default 插件的 review 相关 skills/agents/commands |
| **ECC** | `security-reviewer` 代理、`harness-optimizer` 代理、质量门控命令 | `planner`、`architect`、`tdd-guide`、`code-reviewer` 等全链路代理（28 代理中仅启用 2~3 个） | 避免与上游组件职责混淆 |
| **aio-reflect** | 会话分析 → 经验提名 → 人工晋升 | 自动写入 rules（必须经人工确认） | 防止规则膨胀与冲突 |

---

## 四、阶段详细设计

### 4.1 CLARIFY — 需求澄清

| 项目 | 内容 |
|------|------|
| **目标** | 把模糊需求变成清晰问题空间 |
| **主负责组件** | Superpowers — 仅 `brainstorming` 技能 |
| **输入** | 用户的模糊需求描述 |
| **权威产物** | `clarification-notes.md`、`decision-bundle.json`、初始 feature 描述 |
| **出口机制** | Decision Bundle |
| **门禁条件** | Decision Bundle 中所有关键项已拍板 |
| **控制要点** | 必须阻止 Superpowers 自动进入 `writing-plans` 和 `subagent-driven-development`；CLARIFY 完成后由编排器接管控制权 |

#### 实现要点

1. 编排器在 CLARIFY 阶段向 LLM 注入 Superpowers 的 `brainstorming` 技能上下文
2. brainstorming 完成后，编排器截获控制权，不将后续提示交还 Superpowers
3. 收集所有需要人工拍板的问题，打包为 `decision-bundle.json`
4. 人工回复后更新状态文件，允许进入 SPEC

#### Decision Bundle 格式

```json
{
  "stage": "CLARIFY",
  "decisionBundle": [
    {
      "id": "D-CLARIFY-01",
      "question": "目标用户是内部团队还是外部客户？",
      "options": ["内部团队", "外部客户", "两者都有"],
      "default": null,
      "impact": "影响认证方案与 UI 设计方向",
      "evidence": "clarification-notes.md 第 2 节"
    }
  ]
}
```

---

### 4.2 SPEC — 规格定义

| 项目 | 内容 |
|------|------|
| **目标** | 形成规格权威 |
| **主负责组件** | ShipSpec — `/feature-planning` |
| **输入** | `clarification-notes.md`、`decision-bundle.json`（已回复） |
| **权威产物** | `.shipspec/planning/{feature}/PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md` |
| **出口治理** | **轻议会（A 类）** |
| **门禁条件** | 轻议会 verdict = `GO` |

#### ShipSpec 钩子处理

ShipSpec 的 `hooks/hooks.json` 注册了 `Stop` 事件的三个钩子（`task-loop-hook.sh`、`feature-retry-hook.sh`、`planning-refine-hook.sh`），这些是 Ralph Loop 的核心。stage-harness 中应**不安装或显式禁用这些钩子**，仅保留 ShipSpec 的 commands/agents/skills。

#### 轻议会（A 类）设计

- **规模**：3~5 个 reviewer
- **典型角色**：规格完整性、一致性、可落地性、可测试性（可选）、安全/数据约束（按需）
- **关注重点**：需求完整性、PRD/SDD/TASKS 一致性、隐含假设、是否可被 PLAN 承接
- **裁决语义**：`GO` / `REVISE` / `HOLD`
- **输出**：`spec-council-report.md`、`spec-council-verdict.json`
- **阻断规则**：`GO` 放行；`REVISE`/`HOLD` 阻断

#### 实现要点

1. 编排器调用 ShipSpec 的 `/feature-planning` 命令
2. ShipSpec 通过 `prd-gatherer` → `design-architect` → `task-planner` 链路产出 PRD/SDD/TASKS
3. 编排器启动轻议会：向 3~5 个 reviewer agent 并行发送产物进行评审
4. 汇总 reviewer 结果，生成 verdict
5. 根据 verdict 决定放行或回退

---

### 4.3 PLAN — 实施计划（控制中心）

| 项目 | 内容 |
|------|------|
| **目标** | 形成执行控制包 |
| **主负责组件** | bridge 脚本 + deep-plan |
| **输入** | PRD.md、SDD.md、TASKS.json |
| **权威产物** | `bridge-spec.md`、`claude-plan.md`、`claude-plan-tdd.md`、`sections/index.md`、`sections/section-*.md` |
| **出口治理** | **计划议会（B 类）** |
| **门禁条件** | 计划议会 verdict ≠ `BLOCK` |

> **PLAN 不是普通中间文档，而是后半程的控制中心。** 它决定开发按什么边界推进、测试按什么靶子设计、审查按什么基线核对。

#### 4.3.1 桥接设计

ShipSpec 输出 `TASKS.json`/`TASKS.md`（结构化 JSON + Markdown），deep-plan 期望输入为单个 spec markdown 文件。格式不兼容需要桥接：

```
ShipSpec 输出              桥接                     deep-plan 输入
─────────────          ──────────              ──────────────
PRD.md          ──┐
SDD.md          ──┼──→ bridge-spec.md ──→ /deep-plan @bridge-spec.md
TASKS.json      ──┘
```

**桥接脚本职责**（`scripts/bridge-shipspec-to-deepplan.sh`）：

1. 从 `PRD.md` 提取需求摘要与优先级
2. 从 `SDD.md` 提取架构决策、接口设计、数据模型
3. 从 `TASKS.json` 提取任务清单、依赖关系、验收标准
4. 合并为 deep-plan 可消费的 `bridge-spec.md`

**桥接不是摘要，而是把规格权威无损转成计划输入。** 禁止以下情况：
- 任务依赖丢失
- 关键验收标准丢失
- 架构决策只留在 SDD 未传递到 plan
- 规格未冻结但 bridge 默认替人拍板

**备选方案**：直接以 `SDD.md` 作为 deep-plan 输入（信息损失较大但更简单），由 deep-plan 的 Interview 阶段补充缺失信息。

#### 4.3.2 deep-plan 五步质量放大

deep-plan 的计划生成过程内置质量放大链：

| 步骤 | 控制目标 | 产出 |
|------|---------|------|
| Research | 防止 plan 脱离现有代码与外部现实 | `claude-research.md` |
| Interview | 暴露隐藏需求、边界、异常场景 | `claude-interview.md` |
| External Review | 给 plan 做外部挑战，减少盲区 | `reviews/*.md` |
| TDD Plan | 强制把验证策略前移 | `claude-plan-tdd.md` |
| Section Splitting | 把 plan 变成可执行、可恢复的最小单元 | `sections/index.md` + `section-*.md` |

#### 4.3.3 运行时 Harness 产物（harness.md 补强）

除了 deep-plan 原生产物，PLAN 阶段还应产出以下运行时 harness 产物，使 PLAN 不只是"执行控制包"，还成为"长时执行运行包"：

| 产物 | 用途 |
|------|------|
| `session-handoff.template.md` | Session 接力模板，让后续 session/agent 一进来就能开工 |
| `feature-list.json` | 当前 feature 的子任务列表与状态 |
| `smoke-check.sh` | Session 开始时的冒烟检查脚本 |
| `evaluator-rubric.md` | 运行时 evaluator 的评判标准 |

#### 4.3.4 计划议会（B 类）设计

- **规模**：5~7 个 reviewer
- **典型角色**：覆盖性、任务切分、依赖路径、测试策略、架构承接、安全风险、恢复/回滚（按需）
- **核心审查问题**：
  1. 所有关键需求是否都有落点？
  2. 所有关键架构决策是否被 plan 继承？
  3. 是否还有关键未决问题未显式暴露？
  4. 每个 section 是否边界清晰、done 条件清晰？
  5. 每个 section 是否已有 TDD 入口与验证靶子？
  6. section 之间依赖是否清晰、无明显循环？
  7. 高风险点是否有验证、缓解或回滚安排？
  8. 一个冷启动执行器能否只凭 artifacts 开工？
- **裁决语义**：`READY` / `READY_WITH_CONDITIONS` / `BLOCK`
- **输出**：`plan-council-report.md`、`plan-council-verdict.json`
- **阻断规则**：`READY` 不阻断；`READY_WITH_CONDITIONS` 通常不阻断但需记录跟踪；`BLOCK` 阻断

#### 4.3.5 PLAN → EXECUTE 强门禁

进入 EXECUTE 前必须同时满足：
- 计划议会 verdict ≠ `BLOCK`
- `claude-plan-tdd.md` 已形成且不是泛泛"记得写测试"
- 每个 section 有清晰范围、依赖、done 条件
- 关键未决问题已清空或显式升级到 Decision Bundle
- 状态文件记录本次 plan 放行结果与条件项

---

### 4.4 EXECUTE — 开发执行

| 项目 | 内容 |
|------|------|
| **目标** | 按 section 推进 TDD 实现 |
| **主负责组件** | deep-implement |
| **输入** | `sections/index.md` + `section-*.md` |
| **权威产物** | 代码、测试、section 实现记录、原子提交 |
| **内循环** | section 实现 → 实现级审查 → 提交 |
| **门禁** | section 内循环自控 |

#### 两层审查模型

| 层次 | 负责组件 | 审查范围 | 触发时机 | 成本特征 |
|------|---------|---------|---------|---------|
| **实现级** | deep-implement 内置 `code-reviewer` 子代理 | 当前 section 的 staged diff | 每个 section 实现后自动触发 | 轻量、高频 |
| **验证级** | Ring 7-reviewer 验收议会 | 全量变更 + 跨 section 影响 | 所有 section 完成后进入 VERIFY | 重量、低频 |

#### Session Loop（harness.md 补强）

每个 section 内，不是单纯做实现，而是固定循环：

1. 读取 session handoff / 恢复上下文
2. 跑 smoke / e2e sanity check（如有 `smoke-check.sh`）
3. 只选一个子目标推进
4. TDD 实现 + 本地验证
5. 实现级 code review（deep-implement 内置）
6. 更新 handoff / trace / next steps
7. 原子提交

#### 漂移回流规则

执行中发现以下情况不得继续靠临场判断推进：
- 依赖顺序不成立
- section 切分不合理
- 测试策略无法覆盖风险
- 关键约束未进入 plan

必须：回写 section 或 plan → 必要时回到 PLAN → 重新 gate → 再继续 EXECUTE。

---

### 4.5 VERIFY — 验证与审查

| 项目 | 内容 |
|------|------|
| **目标** | 做正式工程验收 |
| **主负责组件** | Ring（仅 default 插件的审查能力） |
| **输入** | 全量代码变更、plan 基线 |
| **权威产物** | `review-report.md`、`test-report.md`、`verification.json` |
| **出口治理** | **验收议会（C 类）** |

#### 验收议会（C 类）设计

- **规模**：标准 7 reviewer
- **底层实现**：复用 Ring 的 `/ring:codereview` 7 路并行 reviewer
  - `ring:code-reviewer`
  - `ring:business-logic-reviewer`
  - `ring:security-reviewer`
  - `ring:test-reviewer`
  - `ring:nil-safety-reviewer`
  - `ring:consequences-reviewer`
  - `ring:dead-code-reviewer`
- **关注重点**：代码质量、业务逻辑正确性、安全、测试质量、nil/null safety、ripple effect、dead code
- **裁决语义**：`PASS` / `FAIL`
- **输出**：`review-report.md`、`test-report.md`、`verification.json`
- **阻断规则**：`PASS` 允许进入 DONE；`FAIL` 必须回 FIX

#### 持续验证（harness.md 补强）

将 VERIFY 拆成两层：
- **运行时持续验证**：每个 session 开头先 smoke test / e2e sanity check
- **阶段正式验收**：验收议会

#### Ring 能力裁剪

| Ring 插件 | 是否启用 | 原因 |
|-----------|---------|------|
| ring-default（22 skills, 10 agents） | **部分启用**：仅 review 相关 | 核心审查能力 |
| ring-dev-team（29 skills, 12 agents） | **不启用** | dev-cycle 与 deep-implement 冲突 |
| ring-pm-team（15 skills, 4 agents） | **不启用** | 规划技能与 ShipSpec 冲突 |
| ring-pmo-team（9 skills, 6 agents） | **不启用** | 超出当前范围 |
| ring-finops-team（7 skills, 3 agents） | **不启用** | 非核心 |
| ring-tw-team（7 skills, 3 agents） | **按需启用** | DONE 阶段文档审查 |

---

### 4.6 FIX — 问题修复

| 项目 | 内容 |
|------|------|
| **目标** | 问题闭环 |
| **主负责组件** | deep-implement 继续修复 + Ring 重跑审查 |
| **权威产物** | `fix-log.md`、更新后的 `verification.json` |
| **循环限制** | 最多 3 轮 FIX → VERIFY 循环，超出升级人工干预 |

#### 实现要点

1. 验收议会的 `FAIL` 结果中需标注具体问题列表
2. deep-implement 针对问题列表逐项修复
3. 修复完成后重新触发验收议会
4. 状态文件记录 `verifyAttempts`，达到 3 次上限后强制升级

---

### 4.7 DONE — 交付与沉淀

| 项目 | 内容 |
|------|------|
| **目标** | 形成可交付、可沉淀的结果 |
| **主负责组件** | ECC 子集 + aio-reflect |
| **权威产物** | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` |
| **出口治理** | **发布议会（D 类）** |

#### 发布议会（D 类）设计

- **规模**：3~4 个 reviewer
- **典型角色**：Release readiness、Security signoff、Delivery/docs、Learning/governance
- **关注重点**：交付包完整性、最终安全扫描、文档与 release notes、经验提名治理
- **裁决语义**：`RELEASE_READY` / `RELEASE_WITH_CONDITIONS` / `NOT_READY`
- **输出**：`release-council-report.md`、`release-council-verdict.json`
- **阻断规则**：`RELEASE_READY` 不阻断；`RELEASE_WITH_CONDITIONS` 需条件项写入状态文件（安全风险等升级为阻断）；`NOT_READY` 阻断

#### 持续学习双轨制

1. **治理型学习（ECC 思路）**：
   - ECC `security-reviewer` 做最终安全扫描
   - ECC `harness-optimizer` 做流程优化建议
   
2. **复盘型学习（aio-reflect 思路）**：
   - aio-reflect 提取会话记录（`bun run extract-session.ts`）
   - AI 分析识别经验候选
   - 输出 CLAUDE.md 更新建议 + 技能候选
   - **人工审核后才晋升**为规则或技能

#### Eval Harness 数据面（harness.md 补强）

在 DONE 阶段收集以下数据供后续分析：

| 数据 | 用途 |
|------|------|
| `trace/*.jsonl` | 每轮 transcript / tool calls / session summary |
| `metrics.json` | tokens、latency、成功率、返工率 |
| `outcome-check.json` | 结果态校验 |
| `grader-results.json` | 代码 grader、规则 grader、LLM rubric grader |

---

## 五、Hooks 设计

### 5.1 事件选用与验证状态

| 事件 | 用途 | 验证状态 | 依据 |
|------|------|---------|------|
| `SessionStart` | 加载状态、恢复阶段上下文、注入 gate 信息 | ✅ 已验证 | Ring、deep-plan、deep-implement 都在使用 |
| `Stop` | 执行阶段出口门禁 | ✅ 已验证 | ShipSpec Ralph Loop 在用 |
| `UserPromptSubmit` | 阶段感知提醒与上下文警示 | ✅ 已验证 | Ring `claude-md-reminder` 在用 |
| `TaskCompleted` | 阶段出口硬门禁（增强项） | ⚠️ 需 PoC | schema 支持但仓库中无实际使用 |
| `TeammateIdle` | 空闲检测 + 补动作提醒（增强项） | ⚠️ 需 PoC | schema 支持但仓库中无实际使用 |

**核心门禁应先建立在已验证事件之上**。`TaskCompleted` / `TeammateIdle` 先做 PoC，验证通过后再迁移。

### 5.2 推荐 Hooks 配置

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stage-init.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stage-gate-check.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stage-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

### 5.3 各 Hook 职责

#### `stage-init.sh`（SessionStart）

1. 检查 `.harness/` 目录是否存在，不存在则创建
2. 读取 `state.json`，恢复当前阶段上下文
3. 向 LLM 注入当前阶段信息、待办事项、门禁要求
4. 如在 EXECUTE 阶段，执行 `smoke-check.sh`（如存在）

#### `stage-gate-check.sh`（Stop）

1. 读取当前阶段的状态
2. 检查当前阶段的必备产物是否齐全
3. 如产物不齐全或验证未通过，返回 `decision: "block"` + `systemMessage` 提示
4. 如通过，允许正常退出

#### `stage-reminder.sh`（UserPromptSubmit）

1. 读取当前阶段状态
2. 向用户提示输出中注入"当前阶段、已完成步骤、待完成步骤"的简要提醒
3. 如检测到用户输入可能触发跨阶段操作，发出警告

---

## 六、状态文件设计

### 6.1 目录结构

```
.harness/
├── global-config.json              # 全局配置
├── features/
│   ├── {feature-name}/
│   │   ├── state.json              # 阶段状态机状态
│   │   ├── decision-bundles/       # 各阶段的 Decision Bundle
│   │   │   ├── clarify.json
│   │   │   ├── spec.json
│   │   │   └── verify.json
│   │   ├── councils/               # 各议会报告与裁决
│   │   │   ├── spec-council-report.md
│   │   │   ├── spec-council-verdict.json
│   │   │   ├── plan-council-report.md
│   │   │   ├── plan-council-verdict.json
│   │   │   ├── review-report.md
│   │   │   ├── test-report.md
│   │   │   ├── verification.json
│   │   │   ├── release-council-report.md
│   │   │   └── release-council-verdict.json
│   │   ├── artifacts/              # 各阶段权威产物
│   │   │   ├── clarification-notes.md
│   │   │   ├── bridge-spec.md
│   │   │   ├── release-notes.md
│   │   │   ├── delivery-summary.md
│   │   │   └── learning-candidates.md
│   │   ├── sessions/               # Session handoff
│   │   │   └── session-{n}.md
│   │   └── trace/                  # Eval harness 数据面
│   │       ├── trace-{session}.jsonl
│   │       └── metrics.json
│   └── {another-feature}/
│       └── ...
└── templates/
    ├── state.json
    ├── decision-bundle.json
    └── session-handoff.md
```

### 6.2 state.json 格式

```json
{
  "currentStage": "PLAN",
  "feature": "user-auth",
  "riskLevel": "high",
  "stageHistory": [
    {
      "stage": "CLARIFY",
      "completedAt": "2026-03-26T10:00:00Z",
      "artifacts": ["clarification-notes.md", "decision-bundle.json"]
    },
    {
      "stage": "SPEC",
      "completedAt": "2026-03-26T12:00:00Z",
      "artifacts": ["PRD.md", "SDD.md", "TASKS.json", "TASKS.md"],
      "councilVerdict": "GO"
    }
  ],
  "pendingDecisions": [],
  "verifyAttempts": 0,
  "maxVerifyAttempts": 3,
  "councilResults": {
    "specCouncil": {
      "verdict": "GO",
      "timestamp": "2026-03-26T12:00:00Z"
    },
    "planCouncil": null,
    "acceptanceCouncil": null,
    "releaseCouncil": null
  },
  "rollbackHistory": [],
  "sessionCount": 0,
  "totalTokens": 0
}
```

### 6.3 回滚策略

| 项目 | 策略 |
|------|------|
| 上游 artifacts 保留/清除 | **保留**（便于对比与审计） |
| 回退目标 | 回到上一阶段入口重新执行 |
| git 策略 | 从最后一次成功提交新建 fix 分支 |
| 状态追踪 | `rollbackHistory` 记录每次回退事件 |
| 次数限制 | 单阶段最多 3 次回退，超出升级人工干预 |

---

## 七、上下文窗口管理策略

整个流水线产出大量文档，LLM 上下文窗口无法同时容纳。每个阶段只加载与当前阶段相关的 artifacts：

| 阶段 | 加载内容 | 不加载 |
|------|---------|--------|
| CLARIFY | 初始需求描述 | 无 |
| SPEC | `clarification-notes.md` + `decision-bundle.json` | 上游对话 |
| PLAN | `bridge-spec.md`（已压缩的 PRD/SDD/TASKS 精华） | 原始 PRD/SDD 全文 |
| EXECUTE | 当前 `section-*.md` + `claude-plan-tdd.md` 对应部分 | 历史 section、完整 plan |
| VERIFY | plan 基线 + 全量 diff | 历史对话、完整产物链 |
| DONE | `verification.json` + delivery-summary 模板 | 执行过程细节 |

**原则**：每个阶段的输入是上一阶段的 artifacts，而非上一阶段的完整对话上下文。

---

## 八、stage-harness 插件结构

```
stage-harness/
├── .claude-plugin/
│   └── plugin.json                     # 插件 manifest
├── commands/
│   ├── harness-start.md                # 启动 stage-harness 工作流
│   ├── harness-status.md               # 查看当前阶段状态
│   ├── harness-advance.md              # 手动推进阶段（需满足门禁）
│   └── harness-rollback.md             # 手动回退阶段
├── agents/
│   ├── stage-orchestrator.md           # 编排代理：决定调用哪个组件
│   ├── spec-reviewer.md                # 轻议会 reviewer
│   ├── plan-reviewer.md                # 计划议会 reviewer
│   └── release-reviewer.md             # 发布议会 reviewer
├── skills/
│   ├── stage-flow/
│   │   └── SKILL.md                    # 阶段流转规则与状态机
│   ├── bridge-spec/
│   │   └── SKILL.md                    # ShipSpec → deep-plan 桥接
│   ├── council-dispatch/
│   │   └── SKILL.md                    # 议会调度与裁决汇总
│   └── session-handoff/
│       └── SKILL.md                    # Session 接力管理
├── hooks/
│   ├── hooks.json                      # Hook 事件注册
│   ├── stage-init.sh                   # SessionStart：加载状态
│   ├── stage-gate-check.sh             # Stop：检查阶段产物完整性
│   └── stage-reminder.sh              # UserPromptSubmit：阶段感知提醒
├── scripts/
│   ├── bridge-shipspec-to-deepplan.sh  # 格式桥接
│   ├── verify-artifacts.sh             # 产物完整性检查
│   ├── decision-bundle.sh              # Decision Bundle 生成
│   ├── council-runner.sh               # 议会启动与结果汇总
│   └── smoke-check.sh                  # Session 开始冒烟检查
├── templates/
│   ├── state.json                      # 状态文件模板
│   ├── decision-bundle.json            # Decision Bundle 模板
│   ├── session-handoff.md              # Session Handoff 模板
│   ├── spec-council-verdict.json       # 轻议会裁决模板
│   ├── plan-council-verdict.json       # 计划议会裁决模板
│   └── release-council-verdict.json    # 发布议会裁决模板
└── README.md
```

---

## 九、MCP 配置策略

| 优先级 | 配置位置 | 用途 |
|--------|---------|------|
| 1（最高） | stage-harness 插件的 `.mcp.json` 或 manifest `mcpServers` | harness 专属 MCP 工具 |
| 2 | 用户级 `~/.claude.json` | 全局凭据与通用工具 |
| 3 | 项目级配置 | 项目特定的 MCP 集成 |

推荐用途：
- PLAN 阶段：通过 MCP 拉取外部文档、技术调研
- DONE 阶段：通过 MCP 创建 PR、收集交付信息

---

## 十、动态强度控制（harness.md 补强）

不是每个 feature 都需要完整跑最重路径。按风险等级动态决定控制强度：

| 控制维度 | 低风险（riskLevel=low） | 中风险（riskLevel=medium） | 高风险（riskLevel=high） |
|---------|----------------------|-------------------------|----------------------|
| 轻议会 | 可跳过 | 3 reviewer | 5 reviewer |
| 计划议会 | 3 reviewer | 5 reviewer | 7 reviewer |
| 运行时 evaluator | 不启用 | 按需启用 | 必须启用 |
| Session 级回归 | 不要求 | 建议 | 必须 |
| 验收议会 | 3 reviewer | 5 reviewer | 标准 7 reviewer |
| 发布议会 | 2 reviewer | 3 reviewer | 4 reviewer |
| Token 预算 | 宽松 | 标准 | 无上限但需监控 |

风险等级在 CLARIFY 阶段由编排器根据以下因素自动评估：
- 是否涉及安全敏感模块
- 是否跨多个子系统
- 是否涉及数据库迁移
- 是否有高不确定性

---

## 十一、人机交互协议

### 11.1 交互方式

| 场景 | 交互方式 |
|------|---------|
| Decision Bundle | CLI 对话窗口展示结构化 Bundle，用户以 JSON 或选择式回答 |
| 议会裁决 HOLD/BLOCK | 展示裁决报告，等待用户确认或提供补充信息 |
| FIX 轮次上限 | 展示问题汇总，升级为人工干预 |
| 回退确认 | 展示回退原因和影响范围，等待用户确认 |

### 11.2 异步模式

支持将 Decision Bundle 写入文件，人工修改后通过 `/harness-advance` 命令继续。

### 11.3 超时策略

设置最大等待时间，超时后将状态标记为 `WAITING_HUMAN`，不自动推进。

---

## 十二、成本监控

### 12.1 Token 预算

| 议会类型 | 建议预算上限 |
|---------|------------|
| 轻议会（SPEC） | ≤ 50K tokens |
| 计划议会（PLAN） | ≤ 150K tokens |
| 验收议会（VERIFY） | ≤ 200K tokens |
| 发布议会（DONE） | ≤ 50K tokens |

### 12.2 监控指标

在 `metrics.json` 中持续追踪：
- 每阶段 token 消耗
- 各议会首次通过率 vs 总通过率
- FIX 循环平均次数
- 每个 feature 的总 token 消耗
- Decision Bundle 的平均等待时间
- 每阶段平均耗时

---

## 十三、MVP 实施路线

### MVP-1：规格与计划主链打通

**目标**：打通 `CLARIFY → SPEC → PLAN`，建立 PLAN 的关键控制力。

| 序号 | 任务 | 主要内容 | 验收标准 |
|------|------|---------|---------|
| 1.1 | 创建 `stage-harness/` 插件脚手架 | 按第八节目录结构创建，编写 `plugin.json` | 插件可被 Claude Code 识别加载 |
| 1.2 | 实现状态文件与基础状态机 | 编写 `stage-flow/SKILL.md`、`state.json` 模板 | 状态文件可读写，阶段流转正确 |
| 1.3 | 实现 `stage-init.sh` | SessionStart 加载/创建状态文件 | 新 session 能恢复上下文 |
| 1.4 | 接入 Superpowers brainstorming | 在 CLARIFY 阶段调用 brainstorming 技能 | 能完成一次需求澄清对话，产出 `clarification-notes.md` |
| 1.5 | 实现 Decision Bundle | 编写 `decision-bundle.sh`、模板文件 | CLARIFY 出口能产出 Decision Bundle 供人工确认 |
| 1.6 | 接入 ShipSpec `/feature-planning` | 在 SPEC 阶段调用，**禁用 Ralph Loop 钩子** | 产出 PRD/SDD/TASKS 且格式合规 |
| 1.7 | 实现桥接脚本 | 编写 `bridge-shipspec-to-deepplan.sh` | ShipSpec 产物成功转为 deep-plan 可消费的 `bridge-spec.md` |
| 1.8 | 接入 deep-plan | 在 PLAN 阶段调用 `/deep-plan @bridge-spec.md` | 产出 plan/tdd/sections 全套产物 |
| 1.9 | 实现轻议会 | 编写 `spec-reviewer.md` agent、`council-dispatch` skill | 3~5 reviewer 能并行评审 SPEC 产物并输出 verdict |
| 1.10 | 实现计划议会 | 编写 `plan-reviewer.md` agent、复用 `council-dispatch` | 5~7 reviewer 能评审 PLAN 产物并输出 verdict |
| 1.11 | 实现 `stage-gate-check.sh` | Stop 钩子检查产物完整性 | 产物不齐全时阻断流转 |
| 1.12 | PoC：验证 `TaskCompleted`/`TeammateIdle` | 最小 PoC 验证 stdin/stdout JSON 契约 | 文档化实际 JSON 格式 |

### MVP-2：执行与验收闭环

**目标**：打通 `EXECUTE → VERIFY → FIX`。

| 序号 | 任务 | 主要内容 | 验收标准 |
|------|------|---------|---------|
| 2.1 | 接入 deep-implement | 在 EXECUTE 阶段调用 `/deep-implement` | 按 section 产出代码 + 测试 + 原子提交 |
| 2.2 | 实现 Session Handoff | 编写 `session-handoff` skill、模板 | 每个 session 能读取 handoff 恢复工作 |
| 2.3 | 实现 smoke-check | 编写 `smoke-check.sh` | Session 开始时能执行基础验证 |
| 2.4 | 实现漂移回流 | 在编排器中加入 plan 偏离检测逻辑 | 检测到偏离时自动触发回流 PLAN |
| 2.5 | 接入 Ring 验收议会 | 仅安装 ring-default，调用 `/ring:codereview` | 7 路 reviewer 并行审查并输出 `verification.json` |
| 2.6 | 实现验收议会裁决 | 汇总 Ring 审查结果为 PASS/FAIL | 裁决正确且状态文件更新 |
| 2.7 | 实现 FIX → VERIFY 循环 | 包含轮次上限与升级逻辑 | 循环正确终止或升级 |
| 2.8 | 实现 Decision Bundle（VERIFY→DONE） | 在 VERIFY 出口触发 | 人工确认后才能进入 DONE |

### MVP-3：发布、治理与学习

**目标**：打通 DONE 阶段与持续学习。

| 序号 | 任务 | 主要内容 | 验收标准 |
|------|------|---------|---------|
| 3.1 | 接入 ECC security-reviewer | 最终安全扫描 | 安全报告产出 |
| 3.2 | 接入 aio-reflect | 会话复盘 | 经验候选列表产出 |
| 3.3 | 实现发布议会 | 编写 `release-reviewer.md`、裁决汇总 | 3~4 reviewer 能评审交付并输出 verdict |
| 3.4 | 实现双轨学习流程 | "候选经验 → 人工审核 → 晋升"流程 | 双轨制可运行，自动写入被阻止 |
| 3.5 | 实现 release/delivery artifacts 自动生成 | `release-notes.md`、`delivery-summary.md` | 交付包齐全 |
| 3.6 | 实现 Eval Harness 数据面 | trace、metrics、outcome-check | 数据正确收集 |
| 3.7 | 实现动态强度控制 | 根据 riskLevel 调整议会规模 | 低风险项目自动简化流程 |
| 3.8 | 实现成本监控 | `harness-status` 展示累计消耗 | 数据准确可读 |

---

## 十四、关键风险与缓解

| 风险 | 描述 | 缓解措施 |
|------|------|---------|
| **组件自动触发导致职责越界** | Superpowers / ShipSpec / Ring 都有自动触发机制 | Superpowers：编排器在 CLARIFY 后接管；ShipSpec：不安装 Ralph Loop 钩子；Ring：仅安装 default 的 review 能力 |
| **ShipSpec → deep-plan 格式断层** | 两者产物格式不兼容 | MVP-1 中优先实现桥接脚本；备选直接用 SDD.md |
| **Hooks 契约不稳定** | `TaskCompleted`/`TeammateIdle` 无实际使用先例 | 先用已验证的 `SessionStart`/`Stop`/`UserPromptSubmit` 建核心门禁；增强事件先做 PoC |
| **PLAN 看完整但无法约束执行** | EXECUTE 阶段自由发挥 | PLAN 不是单文件而是控制包；section + TDD artifacts 作为执行入口；漂移回流硬规则 |
| **两层审查成本过高** | deep-implement 内置审查 + Ring 7 路审查 | 实现级审查保持不变（section 级快速审查）；Ring 审查仅在全部 section 完成后运行一次；低风险项目可跳过 |
| **未决问题隐式带入 PLAN** | plan 替业务/架构偷偷拍板 | 决策必须进 Decision Bundle；未拍板不得放行关键 gate |
| **执行中漏项临场补脑** | plan 快速失效 | 建立"发现漂移必须回流 PLAN"的硬规则 |
| **学习产物污染长期规则** | 规则膨胀、冲突、失控 | 严格双轨制：机器只提名，人工审核后晋升；定期清理；同项目活跃规则不超过 30 条 |
| **Token 与延迟失控** | 多阶段多 reviewer 成本高 | 四类议会按阶段控制强度；动态强度控制；Token 预算上限 |
| **上下文窗口溢出** | 产物过多 LLM 无法消费 | 分阶段加载策略；每阶段输入为上游 artifacts 而非完整对话 |
| **会话断裂恢复困难** | 网络中断、token 耗尽 | EXECUTE 以 section 为恢复单元；Session Handoff 模板；未完成 section 回滚 git |
| **MCP 凭据安全** | 第三方 server 风险 | 最小权限；显式密钥管理；MCP 优先级分层 |
| **Prompt Injection** | 工具输入输出注入 | MCP 输入输出注入扫描；hooks 脚本不执行未转义外部输入；ECC security-reviewer 最终扫描 |

---

## 十五、Harness 自身测试策略

stage-harness 作为编排层自身也需要测试：

| 测试类型 | 测试内容 | 方法 |
|---------|---------|------|
| **状态机单元测试** | 阶段流转、回退、循环终止 | 模拟各种状态转换场景 |
| **门禁脚本集成测试** | 产物齐全/缺失、审查通过/失败 | 准备各种通过/失败场景的 mock artifacts |
| **桥接脚本转换测试** | ShipSpec 产物到 bridge-spec.md 的完整性 | 对比转换前后的关键信息 |
| **Hook 契约测试** | stdin/stdout JSON 格式是否正确 | 最小 PoC + 自动化回归 |
| **端到端冒烟测试** | 用最小 feature 跑通全流程 | "Hello World" 级别 feature 全流程 |
| **成本测试** | 各阶段 token 消耗是否在预算内 | 记录并对比多次运行数据 |

---

## 十六、组件版本与依赖管理

| 组件 | 关键依赖 | 版本管理方式 |
|------|---------|-------------|
| deep-plan | Python 3.11+, uv | `pyproject.toml` 锁定 |
| deep-implement | Python 3.11+, uv | `pyproject.toml` 锁定 |
| deep-project | Python 3.11+, uv | `pyproject.toml` 锁定 |
| ShipSpec | jq (hooks) | 系统级依赖 |
| Superpowers | Node.js (hooks) | `package.json` |
| Ring | Go (Mithril, 可选) | `go.sum` |
| ECC | Node.js (hooks), Python (InsAIts, 可选) | `package.json` |
| aio-reflect | Bun | `bun.lockb` |

建议：
- 在 `global-config.json` 中记录依赖组件的版本或 commit hash
- 升级时做兼容性测试（特别是 hooks 契约和 artifact 格式变化）
- 在 `stage-init.sh` 中验证依赖组件是否存在且版本匹配

---

## 十七、Git 分支模型

| 维度 | 策略 |
|------|------|
| Feature 分支 | 每个 feature 一个分支（如 `feature/user-auth`） |
| Section 提交 | 每个 section 一个原子提交（由 deep-implement 控制） |
| VERIFY 合并 | VERIFY 通过后合并到主干 |
| FIX 分支 | 在同一 feature 分支上追加提交 |
| 回退策略 | 从最后一次成功提交创建新分支 |

---

## 十八、附录：仓库内支撑文件索引

以下仓库文件支撑了本文档的结论：

| 组件 | 关键文件 | 验证内容 |
|------|---------|---------|
| ShipSpec | `shipspec-claude-code-plugin/README.md`、`CLAUDE.md`、`hooks/hooks.json` | PRD/SDD/TASKS 产物格式；Ralph Loop 使用 `Stop` 事件；3 个 Stop 钩子 |
| deep-plan | `deep-plan/README.md`、`skills/deep-plan/SKILL.md`、`hooks/hooks.json` | Research→Interview→Review→TDD→Sections 流程；输入为单 `.md` 文件；使用 `SessionStart` 和 `SubagentStop` 事件 |
| deep-implement | `deep-implement/README.md`、`skills/deep-implement/SKILL.md`、`agents/code-reviewer.md` | 按 section 执行、自带 code-reviewer 子代理、原子提交；使用 `SessionStart` 事件 |
| deep-project | `deep-project/README.md`、`skills/deep-project/SKILL.md` | 大目标拆解为 feature/spec；使用 `SessionStart` 事件 |
| Ring | `ring/README.md`、`ring/CLAUDE.md`、`ring/default/hooks/hooks.json` | 7 路并行 reviewer；22 skills / 10 agents（default）；使用 `SessionStart` 和 `UserPromptSubmit` 事件 |
| ECC | `everything-claude-code/AGENTS.md`、`agents/security-reviewer.md`、`agents/harness-optimizer.md` | 28 代理 / 125 技能；security-reviewer OWASP 导向；harness-optimizer 改进 harness 配置 |
| aio-reflect | `claude-plugins/plugins/aio-reflect/skills/aio-reflect/SKILL.md` | 会话提取→AI 分析→候选提名→人工晋升；需要 Bun |
| Superpowers | `superpowers/README.md`、`skills/brainstorming/` | brainstorming→writing-plans→subagent-driven-development 完整链路；使用 `SessionStart` 事件 |
| Hooks Schema | `everything-claude-code/schemas/hooks.schema.json` | 合法事件列表含 `TaskCompleted`、`TeammateIdle` |
| 插件规范 | `compound-engineering-plugin/docs/specs/claude-code.md` | `.claude-plugin/` 目录规范、钩子合并机制、MCP 配置方式 |
