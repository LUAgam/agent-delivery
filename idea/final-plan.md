# Claude Code 阶段化 AI Harness — 最终选择方案与实施路线

## 一、文档定位

本文档基于 `idea/end-revised.md` 的修订方案，结合对仓库中所有相关组件源码的逐一核验，输出一份**经过代码验证的最终选择方案**，并给出可落地的实施路线。

与修订版的关系：

- 保留修订版中经代码验证正确的选型方向；
- 修正修订版中遗漏的能力交叉与格式断层问题；
- 补充从代码中发现的、修订版未覆盖的关键约束；
- 给出从 MVP-1 到 MVP-3 的可执行任务清单。

---

## 二、最终选型结论

### 核心分工

```
CLARIFY   → Superpowers（仅 brainstorming 技能）
SPEC      → ShipSpec（PRD / SDD / TASKS 产物）
PLAN      → deep-plan（section 级计划与 TDD 桩）
EXECUTE   → deep-implement（TDD 实现 + 内置审查）
VERIFY    → Ring（7 路并行审查门禁）
GOVERN    → ECC 子集 + aio-reflect（治理审计 + 经验提炼）
```

### 与修订版的差异

| 维度 | 修订版表述 | 最终方案调整 | 原因 |
|------|-----------|-------------|------|
| Superpowers 范围 | "使用其 brainstorming 一类能力" | **仅启用 brainstorming 技能，显式阻止后续自动触发** | Superpowers 自带完整链路（writing-plans → subagent-driven-development → requesting-code-review），不阻止会与 deep-plan/deep-implement 冲突 |
| Ring 范围 | "用于并行 code review" | **仅启用 default 插件的 review 能力，显式禁用 pm-team 和 dev-cycle** | Ring 的 pm-team 有 15 个规划技能与 ShipSpec 重叠；dev-cycle 有 10 门控开发流与 deep-implement 重叠 |
| ECC 范围 | "做质量门控与治理审计" | **仅启用治理相关子集（security-reviewer、harness-optimizer、质量门控命令），不启用 planner/architect/tdd-guide 等** | ECC 有 28 个代理覆盖全链路，不收敛会与上游组件职责混淆 |
| ShipSpec → deep-plan | 未提及格式衔接 | **增加格式桥接方案** | ShipSpec 输出 TASKS.json/TASKS.md，deep-plan 输入为 spec.md，格式不兼容 |
| deep-implement 审查 | 未区分两层审查 | **明确内置审查为"实现级"，Ring 审查为"验证级"** | deep-implement 自带 code-reviewer 子代理，不区分会导致重复审查 |
| TaskCompleted 钩子 | 作为推荐配置写入 | **标记为需 PoC 验证** | 仓库中无任何插件实际使用此事件 |

---

## 三、架构四层模型

```
┌──────────────────────────────────────────────────────────┐
│  1. 编排层 Orchestration                                  │
│     stage-harness 插件                                    │
│     状态机 · Decision Bundle · 阶段出口门禁               │
├──────────────────────────────────────────────────────────┤
│  2. 产物生成层 Spec & Plan                                │
│     Superpowers(brainstorming) → ShipSpec(PRD/SDD/TASKS) │
│     → 桥接脚本 → deep-plan(sections)                      │
├──────────────────────────────────────────────────────────┤
│  3. 执行与验证层 Execute & Verify                         │
│     deep-implement(TDD + 内置审查)                        │
│     → Ring(7路并行审查门禁)                                │
├──────────────────────────────────────────────────────────┤
│  4. 治理与学习层 Govern & Learn                           │
│     ECC子集(安全/质量门控) + aio-reflect(经验提炼)        │
└──────────────────────────────────────────────────────────┘
```

---

## 四、阶段状态机

```
IDEA → CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE
                                           ↑        │
                                           └────────┘
```

可选前置：`DISCOVER → CLARIFY`（由 deep-project 处理大目标拆解）

每个阶段出口都有：
- **状态文件**：记录当前阶段、必备产物、验证状态
- **Decision Bundle**：汇总需人工拍板的问题
- **门禁脚本**：检查产物完整性，阻断不合格流转

---

## 五、各阶段详细设计

### 5.1 CLARIFY — 需求澄清

| 项目 | 内容 |
|------|------|
| 组件 | Superpowers — **仅 brainstorming 技能** |
| 目标 | 把模糊需求变成可确认的问题空间 |
| 输出 | `clarification-notes.md`、`decision-bundle.json`、初始 feature 描述 |
| 关键约束 | 必须阻止 Superpowers 自动进入 `writing-plans` 和 `subagent-driven-development`。实现方式：在 stage-harness 的编排逻辑中，CLARIFY 完成后由编排器接管控制权，不将后续提示交还 Superpowers |

**为什么不用 Ring 的 brainstorming？**
Superpowers 和 Ring 都有 `brainstorming` 技能。选择 Superpowers 的原因是：它的 brainstorming 专注于交互式设计探索和分段确认，更适合早期模糊需求；Ring 的 brainstorming 偏向已有方案的结构化精炼。两者不应同时启用。

### 5.2 SPEC — 规格定义

| 项目 | 内容 |
|------|------|
| 组件 | ShipSpec — `/feature-planning` 命令 |
| 目标 | 产出结构化、可审查的规格文档 |
| 输出 | `.shipspec/planning/{feature}/PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md` |
| 关键约束 | **不启用 ShipSpec 的 Ralph Loop 执行闭环**（`/implement-task`、`/implement-feature`、Stop 钩子）。仅使用其规划侧：`/feature-planning` → prd-gatherer → design-architect → task-planner |

**ShipSpec 钩子处理：** ShipSpec 的 `hooks/hooks.json` 注册了 `Stop` 事件的三个钩子（task-loop-hook、feature-retry-hook、planning-refine-hook），这些是 Ralph Loop 的核心。在 stage-harness 中应**不安装或显式禁用这些钩子**，仅保留 ShipSpec 的 commands/agents/skills。

### 5.3 PLAN — 实施计划

| 项目 | 内容 |
|------|------|
| 组件 | deep-plan — `/deep-plan` 命令 |
| 目标 | 把规格转为 section 级实施计划 |
| 输出 | `planning/` 目录下的 `claude-plan.md`、`claude-plan-tdd.md`、`sections/*.md` |
| 关键约束 | deep-plan 期望输入为单个 spec markdown 文件，不能直接消费 ShipSpec 的 TASKS.json |

**格式桥接方案（关键新增）：**

ShipSpec 输出 → deep-plan 输入之间需要一个桥接步骤。推荐方案：

```
ShipSpec 输出              桥接                    deep-plan 输入
─────────────          ──────────              ──────────────
PRD.md          ──┐
SDD.md          ──┼──→ bridge-spec.md ──→ /deep-plan @bridge-spec.md
TASKS.json      ──┘
```

桥接脚本的职责：
1. 从 PRD.md 提取需求摘要
2. 从 SDD.md 提取架构决策和关键设计
3. 从 TASKS.json 提取任务清单和依赖关系
4. 合并为一份 deep-plan 可消费的 spec 文件

备选方案：直接将 ShipSpec 的 `SDD.md` 作为 deep-plan 的输入（SDD 已包含架构决策、API 规格、数据模型等），然后让 deep-plan 的 Interview 阶段补充缺失信息。此方案更简单但信息损失更大。

### 5.4 EXECUTE — 开发执行

| 项目 | 内容 |
|------|------|
| 组件 | deep-implement — `/deep-implement` 命令 |
| 目标 | 按 section 推进 TDD 实现 |
| 输出 | 代码变更、测试文件、section 实现记录、分段提交 |
| 关键约束 | 一次只有 deep-implement 推进代码；其内置的 code-reviewer 子代理负责**实现级审查**（针对当前 section 的 staged diff） |

**两层审查模型：**

| 层次 | 负责组件 | 审查范围 | 触发时机 |
|------|---------|---------|---------|
| 实现级 | deep-implement 内置 code-reviewer | 当前 section 的 staged diff | 每个 section 实现后自动触发 |
| 验证级 | Ring 并行 reviewer | 全量变更 + 跨 section 影响 | 所有 section 完成后，进入 VERIFY 阶段 |

### 5.5 VERIFY — 验证与审查

| 项目 | 内容 |
|------|------|
| 组件 | Ring — **仅 default 插件的审查能力** |
| 目标 | 对完整实现做多维度并行审查 |
| 输出 | `review-report.md`、`test-report.md`、`verification.json` |
| 使用的 Ring 能力 | `/ring:codereview`（调度 7 路并行 reviewer）、`ring:verification-before-completion` |

**Ring 能力裁剪清单：**

| Ring 插件 | 是否启用 | 原因 |
|-----------|---------|------|
| ring-default（22 skills, 10 agents） | **部分启用**：仅 review 相关 skills/agents/commands | 核心审查能力在此 |
| ring-dev-team（29 skills, 12 agents） | **不启用** | dev-cycle 与 deep-implement 冲突 |
| ring-pm-team（15 skills, 4 agents） | **不启用** | pre-dev 工作流与 ShipSpec 冲突 |
| ring-pmo-team（9 skills, 6 agents） | **不启用** | PMO 能力超出当前范围 |
| ring-finops-team（7 skills, 3 agents） | **不启用** | 非核心需求 |
| ring-tw-team（7 skills, 3 agents） | **按需启用** | 文档审查可在 DONE 阶段使用 |

**审查通过条件：**
- 所有 7 个 reviewer 通过（PASS）
- CRITICAL 级别问题数 = 0
- 测试全部通过
- 不满足 → 回退到 FIX 阶段

### 5.6 FIX — 问题修复

| 项目 | 内容 |
|------|------|
| 组件 | deep-implement 继续执行修复 + Ring 重跑审查 |
| 输出 | `fix-log.md`、更新后的 `verification.json` |
| 循环限制 | 最多 3 轮 FIX → VERIFY 循环，超出则升级为人工干预 |

### 5.7 DONE — 交付与沉淀

| 项目 | 内容 |
|------|------|
| 组件 | ECC 子集 + aio-reflect |
| 目标 | 输出交付包 + 提炼可复用经验 |
| 输出 | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` |

**ECC 能力裁剪清单：**

| ECC 组件 | 是否启用 | 用途 |
|----------|---------|------|
| security-reviewer 代理 | **启用** | 最终安全扫描 |
| harness-optimizer 代理 | **启用** | 流程优化建议 |
| `/code-review` 命令 | **不启用** | 已有 Ring 审查 |
| planner / architect / tdd-guide | **不启用** | 已有上游组件 |
| loop-operator | **按需启用** | 监控自主循环 |
| 其余 20+ 代理 | **不启用** | 与上游组件职责重叠 |

**aio-reflect 工作流：**
1. 提取会话记录 → `bun run extract-session.ts`
2. AI 分析识别经验候选
3. 输出 CLAUDE.md 更新建议 + 技能候选
4. **人工审核后才晋升**为规则或技能（双轨制）

---

## 六、职责边界总表（最终版）

| 组件 | 保留职责 | 显式禁用 |
|------|---------|---------|
| Superpowers | brainstorming 技能 | writing-plans、executing-plans、subagent-driven-development、requesting-code-review 的自动触发 |
| ShipSpec | `/feature-planning` → PRD/SDD/TASKS | `/implement-task`、`/implement-feature`、Stop 钩子（Ralph Loop） |
| deep-plan | `/deep-plan` → research/interview/review/TDD/sections | — |
| deep-implement | `/deep-implement` → TDD 实现 + 内置审查 + 原子提交 | — |
| Ring | `/ring:codereview` 7 路并行审查 | pm-team、dev-team（dev-cycle）、pmo-team、finops-team |
| ECC | security-reviewer、harness-optimizer、质量门控 | planner、architect、tdd-guide、code-reviewer 等全链路代理 |
| aio-reflect | 会话分析 → 经验提名 → 人工晋升 | 自动写入 rules（必须经人工确认） |

---

## 七、Hooks 设计

### 7.1 事件选用

| 事件 | 用途 | 验证状态 |
|------|------|---------|
| `SessionStart` | 加载 stage-harness 状态、注入阶段上下文 | ✅ 已验证（Ring、deep-implement 都在用） |
| `Stop` | 阶段内循环控制（如 FIX 循环） | ✅ 已验证（ShipSpec Ralph Loop 在用） |
| `UserPromptSubmit` | 阶段感知提醒 | ✅ 已验证（Ring claude-md-reminder 在用） |
| `TaskCompleted` | 阶段出口硬门禁 | ⚠️ **需 PoC 验证**（schema 支持但无现有实现） |
| `TeammateIdle` | 空闲检测 + 补动作提醒 | ⚠️ **需 PoC 验证** |

### 7.2 推荐配置

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
    ]
  }
}
```

### 7.3 状态文件格式

```json
{
  "currentStage": "EXECUTE",
  "feature": "user-auth",
  "stageHistory": [
    { "stage": "CLARIFY", "completedAt": "...", "artifacts": ["clarification-notes.md"] },
    { "stage": "SPEC", "completedAt": "...", "artifacts": ["PRD.md", "SDD.md", "TASKS.json"] },
    { "stage": "PLAN", "completedAt": "...", "artifacts": ["claude-plan.md", "sections/"] }
  ],
  "pendingDecisions": [],
  "verifyAttempts": 0
}
```

---

## 八、Decision Bundle 机制

在以下阶段出口触发：

| 触发点 | 典型决策项 |
|--------|-----------|
| CLARIFY → SPEC | 需求优先级、范围确认、技术约束 |
| SPEC → PLAN | 架构选型、数据库选择、部署方式 |
| VERIFY → DONE | 是否接受当前质量、遗留问题处理方式 |

格式：

```json
{
  "stage": "SPEC",
  "decisionBundle": [
    {
      "id": "D1",
      "question": "数据库选型",
      "options": ["PostgreSQL", "MongoDB"],
      "default": "PostgreSQL",
      "impact": "影响数据模型与部署方式",
      "evidence": "SDD Section 5.1 分析结论"
    }
  ]
}
```

---

## 九、stage-harness 插件结构

```
stage-harness/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── harness-start.md          # 启动 stage-harness 工作流
│   ├── harness-status.md         # 查看当前阶段状态
│   └── harness-advance.md        # 手动推进阶段（需满足门禁）
├── agents/
│   └── stage-orchestrator.md     # 编排代理：决定调用哪个组件
├── skills/
│   ├── stage-flow/
│   │   └── SKILL.md              # 阶段流转规则
│   └── bridge-spec/
│       └── SKILL.md              # ShipSpec → deep-plan 格式桥接
├── hooks/
│   ├── hooks.json
│   ├── stage-init.sh             # SessionStart：加载状态
│   └── stage-gate-check.sh       # Stop：检查阶段产物完整性
├── scripts/
│   ├── bridge-shipspec-to-deepplan.sh  # 格式桥接脚本
│   ├── verify-artifacts.sh             # 产物完整性检查
│   └── decision-bundle.sh             # Decision Bundle 生成
├── templates/
│   ├── state.json                # 状态文件模板
│   └── decision-bundle.json      # Decision Bundle 模板
└── README.md
```

---

## 十、MCP 配置策略

| 优先级 | 配置位置 | 用途 |
|--------|---------|------|
| 1（最高） | stage-harness 插件的 `.mcp.json` 或 manifest `mcpServers` | harness 专属 MCP 工具 |
| 2 | 用户级 `~/.claude.json` | 全局凭据与通用工具 |
| 3 | 项目级配置 | 项目特定的 MCP 集成 |

推荐用途：
- PLAN 阶段：通过 MCP 拉取外部文档、技术调研
- DONE 阶段：通过 MCP 创建 PR、收集交付信息

---

## 十一、MVP 实施路线

### MVP-1：规格与计划打通

**目标**：验证 CLARIFY → SPEC → PLAN 链路可走通

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 1.1 | 创建 `stage-harness/` 插件脚手架 | plugin.json 合法，可被 Claude Code 识别 |
| 1.2 | 实现 `stage-init.sh`：在 SessionStart 时加载/创建状态文件 | 状态文件可读写 |
| 1.3 | 集成 Superpowers brainstorming → 输出 clarification-notes.md | 能完成一次需求澄清对话 |
| 1.4 | 集成 ShipSpec `/feature-planning` → 输出 PRD/SDD/TASKS | 产物齐全且格式合规 |
| 1.5 | **实现桥接脚本** `bridge-shipspec-to-deepplan.sh` | 能将 ShipSpec 产物转为 deep-plan 可消费的 spec 文件 |
| 1.6 | 集成 deep-plan → 输出 sections/*.md | sections 可被 deep-implement 消费 |
| 1.7 | 实现简单状态流转（文件驱动，不上复杂钩子） | 状态文件正确记录阶段历史 |
| 1.8 | **PoC：验证 `TaskCompleted` 和 `TeammateIdle` 钩子的 stdin/stdout 契约** | 文档化 JSON 输入输出格式 |

### MVP-2：执行与验证闭环

**目标**：验证 EXECUTE → VERIFY → FIX 循环

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 2.1 | 集成 deep-implement → 按 section 执行 TDD | 每个 section 产出代码 + 测试 + 原子提交 |
| 2.2 | 集成 Ring `/ring:codereview` 7 路并行审查 | 所有 reviewer 产出结果，汇总为 verification.json |
| 2.3 | 实现 `stage-gate-check.sh`：Stop 钩子检查阶段完整性 | 产物不齐全时阻断流转 |
| 2.4 | 实现 FIX → VERIFY 循环（最多 3 轮） | 循环正确终止或升级 |
| 2.5 | 实现 Decision Bundle 在 VERIFY → DONE 出口的触发 | 人工确认后才能进入 DONE |

### MVP-3：治理与学习

**目标**：闭合治理与持续学习循环

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 3.1 | 集成 ECC security-reviewer 做最终安全扫描 | 安全报告产出 |
| 3.2 | 集成 aio-reflect 做会话复盘 | 经验候选列表产出 |
| 3.3 | 实现"候选经验 → 人工审核 → 晋升为规则/技能"流程 | 双轨制可运行 |
| 3.4 | 实现 release-notes.md 和 delivery-summary.md 自动生成 | 交付包齐全 |
| 3.5 | 按需启用 Ring tw-team 做文档审查 | 文档质量审查通过 |

---

## 十二、关键风险与缓解

### 12.1 组件自动触发导致职责越界

**风险**：Superpowers、ShipSpec、Ring 都有自动触发机制，可能在非预期阶段激活。

**缓解**：
- Superpowers：编排器在 CLARIFY 结束后接管控制权
- ShipSpec：不安装其 Stop 钩子（hooks.json 中的 Ralph Loop 相关钩子）
- Ring：仅安装 default 插件，且只启用 review 相关能力

### 12.2 ShipSpec → deep-plan 格式断层

**风险**：两者产物格式不兼容，无法直接衔接。

**缓解**：
- 在 MVP-1 中实现桥接脚本（优先）
- 备选：直接用 SDD.md 作为 deep-plan 输入（信息损失可接受时）

### 12.3 Hooks 契约未验证

**风险**：`TaskCompleted`、`TeammateIdle` 的 stdin/stdout 格式仅见于 schema 定义，无实际使用先例。

**缓解**：
- MVP-1 中包含最小 PoC
- 先用已验证的 `Stop` 和 `SessionStart` 实现核心门禁
- `TaskCompleted` 作为增强项，PoC 通过后再迁移

### 12.4 两层审查的成本与延迟

**风险**：deep-implement 内置审查 + Ring 7 路审查，Token 消耗显著。

**缓解**：
- deep-implement 的审查保持不变（它是 section 级的快速审查）
- Ring 审查可配置为仅在全部 section 完成后运行一次
- 对低风险项目可跳过 Ring 审查（通过状态文件中的 `skipVerify` 标记）

### 12.5 规则与经验膨胀

**风险**：aio-reflect 持续产出经验候选，长期积累会互相冲突。

**缓解**：
- 严格的双轨制：机器只提名，人工审核后才晋升
- 定期清理：每季度审视已有规则，淘汰过时条目
- 数量限制：同一项目的活跃规则不超过 30 条

---

## 十三、附录：代码验证依据

以下仓库文件支撑了本文档的结论：

| 组件 | 关键文件 | 验证内容 |
|------|---------|---------|
| ShipSpec | `shipspec-claude-code-plugin/README.md`、`CLAUDE.md`、`hooks/hooks.json` | PRD/SDD/TASKS 产物、Ralph Loop 钩子使用 `Stop` 事件 |
| deep-plan | `deep-plan/README.md` | `Research → Interview → External Review → TDD → Sections` 流程 |
| deep-implement | `deep-implement/README.md` | 按 section 执行、自带 code-reviewer 子代理、原子提交 |
| Ring | `ring/README.md`、`ring/CLAUDE.md`、`ring/default/hooks/hooks.json` | 89 skills / 38 agents / 33 commands；pm-team 与 dev-cycle 的能力范围 |
| ECC | `everything-claude-code/docs/zh-CN/README.md`、`AGENTS.md` | 28 代理 / 125 技能的全能型定位 |
| aio-reflect | `claude-plugins/plugins/aio-reflect/skills/aio-reflect/SKILL.md` | 会话提取 → AI 分析 → 候选提名 → 人工晋升 |
| Superpowers | `superpowers/README.md` | brainstorming → writing-plans → subagent-driven-development 完整链路 |
| Hooks Schema | `everything-claude-code/schemas/hooks.schema.json` | 合法事件列表含 `TaskCompleted`、`TeammateIdle` |
| 插件规范 | `compound-engineering-plugin/docs/specs/claude-code.md` | `.claude-plugin/` 目录规范、钩子合并机制、MCP 配置方式 |

---

## 十四、下一步行动

1. **立即可做**：创建 `stage-harness/` 插件脚手架（MVP-1.1）
2. **优先验证**：实现桥接脚本 PoC + `TaskCompleted` 钩子 PoC（MVP-1.5 + 1.8）
3. **持续推进**：按 MVP-1 → MVP-2 → MVP-3 顺序逐步集成
