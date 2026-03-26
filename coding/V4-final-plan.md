# Claude Code 阶段化 AI Harness V4 — 最终方案

> 基于 V3 方案 + Flow-Next 源码深度审阅 + 全部前序文档交叉分析的最终收敛版。本文档取代 V3 的 `Claude-Code-end.md`，作为后续实施的唯一权威基线。

---

## 一、文档定位

本文档是对 V3 方案的**关键修订与最终收敛**。

V3（`Claude-Code-end.md`）做出了正确的**机制设计**和**选型方向**，但在两个关键问题上存在重大缺陷：

1. **对 Flow-Next 的理解严重不足**——V3 将其描述为"`.flow/*` + `flowctl` 的 plan-first 交付子集能力"，但实际上 Flow-Next（v0.26.1）是一个拥有 11 命令、20 agent、16 skill、完整 CLI 的成熟编排系统
2. **stage-harness 的定位需要根本性调整**——由于 Flow-Next 自身就是完整的编排系统，stage-harness 不能再定位为"编排外壳"，否则会形成双重编排

本文档保留 V3 的全部机制设计（PLAN 控制中心、Decision Bundle、分层议会、阶段门禁），但对**架构分层**和**组件职责边界**做出关键修订。

---

## 二、最终主张

> 以 **Flow-Next** 为全流程执行引擎（plan → work → review → Ralph），以 **stage-harness** 为治理增强层（Decision Bundle + 分层议会 + 阶段门禁 + 动态强度控制），以 **Superpowers** 负责前半程方法学，以 **ECC 精选子集** 承担安全与学习治理，以 **Claude Code 原生能力** 为运行时底座。

与 V3 的关键差异：

| 维度 | V3 | V4（本文档） |
|------|-----|------------|
| stage-harness 定位 | 编排外壳（总控层） | **治理增强层**（不重复 Flow-Next 的编排能力） |
| Flow-Next 定位 | 后半程交付子集能力 | **全流程执行引擎**（plan + work + review + Ralph） |
| SPEC 产物格式 | PRD.md + SDD.md + TASKS.json + TASKS.md | **Flow-Next epic spec + task 图谱**（简化桥接） |
| 状态 source of truth | stage-harness 的 state.json | **flowctl**（stage-harness 读取 flowctl 状态做门禁） |
| 自治运行 | 未设计 | **Ralph**（Flow-Next 内置自治循环） |

---

## 三、不可替换的机制层（从 V2/V3 完整继承）

以下机制**不随承载组件变化**，是整个体系的骨架：

### 3.1 PLAN 是后半程控制中心

PLAN 不是中间文档，而是后半程的控制中心。它控制覆盖、切分、依赖、验证、风险。

后半程主链：`PLAN → EXECUTE → VERIFY → FIX → DONE`

硬规则：
- EXECUTE 发现切分失效 → 必须回流 PLAN
- EXECUTE 发现依赖不成立 → 必须回流 PLAN
- 不允许"计划之外的临场扩写"静默混入

### 3.2 Decision Bundle

在关键阶段出口，收束必须由人拍板的问题，防止 AI 替人拍板。

触发点：
- `CLARIFY → SPEC`
- `SPEC → PLAN`
- `PLAN → EXECUTE`
- `VERIFY → DONE`

### 3.3 分层议会

四类议会，不同阶段使用不同强度：

| 议会类型 | 阶段 | 规模 | 关注重点 |
|---------|------|------|---------|
| 轻议会 | SPEC | 3~5 | 漏项、冲突、隐含假设 |
| 计划议会 | PLAN | 5~7 | 覆盖、切分、依赖、风险 |
| 验收议会 | VERIFY | 5~7 | 代码质量、安全、测试 |
| 发布议会 | DONE | 3~4 | 交付完整性、安全签署 |

### 3.4 阶段门禁

每个阶段出口必须可审查、可阻断、可回退。

### 3.5 可审查 / 可阻断 / 可回退

整个流程的每一步都有据可查、不合格可阻断、出问题可回退。

---

## 四、最终架构 — 五层模型

```
┌─────────────────────────────────────────────────────────────────┐
│  L1. 治理增强层 Governance Enhancement                           │
│      stage-harness                                               │
│      Decision Bundle · 分层议会 · 阶段门禁 · 动态强度控制 · 学习治理 │
├─────────────────────────────────────────────────────────────────┤
│  L2. 方法层 Methodology                                          │
│      Superpowers                                                  │
│      CLARIFY 阶段 brainstorming + TDD/review 方法纪律              │
├─────────────────────────────────────────────────────────────────┤
│  L3. 执行引擎层 Execution Engine                                  │
│      Flow-Next                                                    │
│      epic/task 模型 · plan(scouts) · work(worker) · review        │
│      · interview · Ralph(自治) · flowctl CLI · memory             │
├─────────────────────────────────────────────────────────────────┤
│  L4. 安全与质量层 Safety & Quality                                │
│      ECC 精选子集                                                 │
│      security-reviewer · audit · safety gate · learning governance│
├─────────────────────────────────────────────────────────────────┤
│  L5. 运行时底座 Runtime Foundation                                │
│      Claude Code 原生能力                                         │
│      hooks · subagents · agent teams · rules / skills / MCP       │
└─────────────────────────────────────────────────────────────────┘
```

### 与 V3 四层模型的差异

V3 把 stage-harness 定位为 L1"编排层"，把 Flow-Next 定位为 L3"交付主干层"。这在逻辑上意味着 stage-harness 编排 Flow-Next。

但 Flow-Next 自身已经是一个完整的编排系统（plan → work → review → Ralph），在它上面再加一层编排会导致**双重编排**——两套状态机、两套任务追踪、两套 review 体系并存。

V4 的关键修订：

- **L1 从"编排层"改为"治理增强层"**：stage-harness 不做编排，只做 Flow-Next 没有的治理能力
- **L3 从"交付主干层"升级为"执行引擎层"**：Flow-Next 承担全流程执行
- **状态 source of truth 统一到 flowctl**：stage-harness 通过读取 flowctl 状态做门禁判断，不维护独立状态机

---

## 五、Flow-Next 能力全景（基于源码审阅）

Flow-Next（v0.26.1）在仓库中的实际能力：

### 5.1 命令体系（11 个 slash 命令）

| 命令 | 功能 | 对应 V3 阶段 |
|------|------|------------|
| `/flow-next:plan` | 并行 scouts 调研 + epic + task 生成 | PLAN |
| `/flow-next:work` | worker subagent 执行 + re-anchor + 原子提交 | EXECUTE |
| `/flow-next:interview` | 深度 Q&A 精炼 spec | SPEC / CLARIFY |
| `/flow-next:plan-review` | Carmack-level 计划审查 | PLAN 出口 |
| `/flow-next:impl-review` | Carmack-level 实现审查（跨模型） | VERIFY |
| `/flow-next:epic-review` | 完成度 / spec compliance 审查 | VERIFY / DONE |
| `/flow-next:prime` | 8 大支柱 / 48 标准就绪评估 | 任何阶段前 |
| `/flow-next:sync` | 手动 plan-sync（漂移后同步） | EXECUTE |
| `/flow-next:ralph-init` | 初始化 Ralph 自治循环 | EXECUTE |
| `/flow-next:setup` | 配置 review 后端 + 本地 flowctl | 初始化 |
| `/flow-next:uninstall` | 卸载引导 | — |

### 5.2 Agent 体系（20 个专用 agent）

**调研 scouts**（9 个）：repo-scout、github-scout、docs-scout、practice-scout、epic-scout、docs-gap-scout、memory-scout、context-scout、flow-gap-analyst

**执行**：worker（每个 task 一个隔离 subagent）、plan-sync（工作后下游同步）、quality-auditor

**Prime scouts**（8 个）：tooling-scout、build-scout、testing-scout、claude-md-scout、env-scout、observability-scout、security-scout、workflow-scout

### 5.3 Artifact 体系（`.flow/` 目录）

```
.flow/
├── config.json          # 配置（memory、planSync、review backend、scouts）
├── meta.json            # schema 版本、setup 版本
├── usage.md             # 使用说明
├── bin/flowctl           # 本地 CLI（可选）
├── epics/fn-N.json       # epic 元数据（状态、分支、依赖、review 状态）
├── specs/fn-N.md         # epic 规格（Goal、Architecture、API、Acceptance 等）
├── tasks/fn-N.M.json     # task 元数据（依赖、状态、evidence、assignee）
├── tasks/fn-N.M.md       # task 规格（Description、Acceptance、Done summary、Evidence）
└── memory/               # 可选：pitfalls / conventions / decisions
```

### 5.4 核心能力矩阵

| 能力 | 实现方式 | 对 V3 的意义 |
|------|---------|-------------|
| **Plan-first** | `/flow-next:plan` 并行 scouts 调研后生成 epic + tasks | 天然契合"PLAN 是控制中心" |
| **依赖管理** | `flowctl dep` + `flowctl ready` + `flowctl next` | 自动排序执行顺序 |
| **Re-anchor** | 每个 task 前重读 spec + 状态，防止漂移 | 覆盖 V3 的"EXECUTE 持续反向校验 PLAN" |
| **跨模型 Review** | RepoPrompt / Codex CLI / Export 三种后端 | Claude 实现 → GPT 审查，比单模型更可靠 |
| **Evidence** | `flowctl done` 时记录 commits / tests / PRs | 结构化验收证据 |
| **自治循环** | Ralph + hooks + guard + receipts | 支持 overnight 无人运行 |
| **Memory** | pitfalls / conventions / decisions | 跨会话经验沉淀 |
| **Worktree** | 隔离工作树支持多分支并行 | 多 task 并行执行 |

---

## 六、stage-harness 的重新定位 — 治理增强层

### 6.1 stage-harness 做什么（Flow-Next 没有的）

| 能力 | 说明 | 实现方式 |
|------|------|---------|
| **Decision Bundle** | 关键决策强制人工拍板，人未拍板则阻断 | hooks 注入 + 结构化 JSON |
| **分层议会** | 多角色多视角的治理审查（比 Flow-Next 的单 reviewer 更深） | Claude Code agent teams / subagents |
| **阶段门禁** | SPEC→PLAN、PLAN→EXECUTE、VERIFY→DONE 的硬放行检查 | hooks + flowctl 状态读取 |
| **动态强度控制** | 按风险等级调整议会规模、review 深度、是否启用 Ralph | 基于 riskLevel 的条件分支 |
| **CLARIFY 阶段** | Superpowers brainstorming（发散式澄清） | 串联 Flow-Next interview（收敛式精炼） |
| **ECC 治理** | 安全扫描、学习候选治理、audit | ECC 精选子集 selective install |
| **发布议会 + DONE** | 交付包、release notes、learning candidates | 发布议会 + 学习治理流程 |
| **Eval 数据面** | token / latency / outcome 量化指标 | 收集 Flow-Next evidence + 补充定量数据 |

### 6.2 stage-harness 不做什么（Flow-Next 已有的）

- ❌ 不做 plan 生成（Flow-Next 的 `/flow-next:plan` 更强）
- ❌ 不做 task 执行调度（Flow-Next 的 worker + re-anchor 更强）
- ❌ 不做代码 review（Flow-Next 的 impl-review 更强）
- ❌ 不做 task 状态追踪（flowctl 是 source of truth）
- ❌ 不做依赖管理（flowctl dep/ready/next 更成熟）
- ❌ 不做自治循环（Ralph 更成熟）
- ❌ 不维护独立状态机（读取 flowctl 状态）

### 6.3 状态管理策略

**Source of truth：flowctl**

stage-harness 不维护独立的 `state.json` 状态机，而是：

1. 通过 `flowctl` 读取当前 epic/task 状态
2. 在关键节点（SPEC→PLAN、PLAN→EXECUTE、VERIFY→DONE）注入门禁检查
3. 门禁元数据（Decision Bundle、议会 verdict、风险等级）存储在 `.harness/` 目录
4. 阶段流转由 Flow-Next 的 epic/task 状态自然驱动，stage-harness 只在需要阻断时介入

```
.harness/
├── config.json                    # 全局配置（风险等级、议会规模）
├── features/{epic-id}/
│   ├── decision-bundles/          # 各阶段 Decision Bundle
│   │   ├── clarify.json
│   │   ├── spec.json
│   │   └── verify.json
│   ├── councils/                  # 议会报告与裁决
│   │   ├── spec-council-verdict.json
│   │   ├── plan-council-verdict.json
│   │   └── release-council-verdict.json
│   ├── risk-assessment.json       # 风险评估结果
│   └── eval/                      # 量化指标（补充 Flow-Next evidence）
│       └── metrics.json
└── templates/
    ├── decision-bundle.json
    └── council-verdict.json
```

---

## 七、各阶段最终设计

### 7.1 CLARIFY — 需求澄清

| 项目 | 内容 |
|------|------|
| **主负责** | Superpowers brainstorming → Flow-Next interview |
| **工作流** | 1. Superpowers brainstorming 发散探索问题空间 → 2. `/flow-next:interview` 收敛精炼 → 3. Decision Bundle 收束待决策项 |
| **产物** | `clarification-notes.md`、`decision-bundle.json` |
| **出口** | Decision Bundle 中所有关键项已由人拍板 |

**Superpowers 与 Flow-Next interview 的分工**：brainstorming 偏发散（"这个问题空间有什么"），interview 偏收敛（"这个 spec 还缺什么"）。前者适合需求模糊时，后者适合 spec 已有初稿需要精炼时。

### 7.2 SPEC — 规格定义

| 项目 | 内容 |
|------|------|
| **主负责** | Flow-Next epic 模型 + stage-harness 门禁 |
| **工作流** | 1. `flowctl epic create` 创建 epic → 2. `flowctl epic set-plan` 写入规格 → 3. `/flow-next:interview` 精炼 → 4. 轻议会审查 → 5. Decision Bundle |
| **产物** | `.flow/specs/fn-N.md`（epic spec）、`decision-bundle.json` |
| **出口** | 轻议会 verdict = GO + Decision Bundle 已回复 |

**Epic spec 模板**（基于 Flow-Next 格式 + V3 需求扩展）：

```markdown
# {Epic Title}

## Goal & Context
为什么要做，解决什么问题。

## Architecture & Data Models
系统设计、数据流、关键组件。（对应原 SDD.md 的核心内容）

## API Contracts
接口、输入输出形态。

## Edge Cases & Constraints
失败模式、限制、性能要求。

## Acceptance Criteria
- [ ] 可测试的验收标准 1
- [ ] 可测试的验收标准 2

## Boundaries
显式的 out of scope。

## Decision Context
为什么选这个方案而不是其他。

## Test Strategy
测试策略与验证靶子。（V3 的 test-strategy.md 内化为 section）

## Risk Register
已识别风险与缓解措施。（V3 的 risk-register.md 内化为 section）
```

### 7.3 PLAN — 实施计划

| 项目 | 内容 |
|------|------|
| **主负责** | Flow-Next `/flow-next:plan` + stage-harness 计划议会 |
| **工作流** | 1. `/flow-next:plan {epic-id}` 并行 scouts 调研 + 生成 tasks → 2. `/flow-next:plan-review`（Carmack-level 技术审查） → 3. 计划议会（多角色治理审查） → 4. Decision Bundle |
| **产物** | `.flow/tasks/*.json + *.md`（task 图谱）、`plan-council-verdict.json` |
| **出口** | plan-review 通过 + 计划议会 verdict ≠ BLOCK + Decision Bundle 已回复 |

**双层 review 设计**：

- **Flow-Next plan-review**：Carmack-level 技术审查——计划是否技术可行、覆盖是否完整、风险是否识别
- **stage-harness 计划议会**：多角色治理审查——是否有未决策项被偷偷带入、是否符合团队标准、是否可交接

两者互补而不是替代。

### 7.4 EXECUTE — 开发执行

| 项目 | 内容 |
|------|------|
| **主负责** | Flow-Next `/flow-next:work` |
| **工作流** | 1. `flowctl ready` 获取可执行 task → 2. `/flow-next:work` 启动 worker subagent → 3. worker 在 re-anchor 后实现 task → 4. `flowctl done` 记录 evidence → 5. 循环直到所有 task 完成 |
| **产物** | 代码、测试、`.flow/tasks/*.json`（evidence）、git 原子提交 |
| **内循环** | worker re-anchor → 实现 → 测试 → review → done → 下一个 task |

**Ralph 自治模式**：对于高信心、中低风险的 epic，可启用 Ralph 自治循环：

```bash
/flow-next:ralph-init    # 初始化 Ralph
# Ralph 自动循环：pick task → work → review → done → next task
```

stage-harness 可通过 Ralph 的 guard hooks 注入额外检查（如 token 预算限制、关键 task 前强制人工确认）。

### 7.5 VERIFY — 验证与审查

| 项目 | 内容 |
|------|------|
| **主负责** | Flow-Next review + stage-harness 验收议会 + ECC |
| **工作流** | 1. `/flow-next:impl-review`（跨模型代码审查） → 2. `/flow-next:epic-review`（spec compliance 审查） → 3. ECC security-reviewer（安全扫描） → 4. 验收议会（多角色治理审查） |
| **产物** | review 结果、`verification.json`、安全报告 |
| **出口** | impl-review SHIP + epic-review SHIP + 安全扫描通过 + 验收议会 PASS |

**三层 review 体系**：

| 层 | 负责 | 关注 | 性质 |
|----|------|------|------|
| 技术 review | Flow-Next impl-review | 代码质量、逻辑正确性 | 跨模型自动 |
| Spec compliance | Flow-Next epic-review | 实现与规格的一致性 | 自动 |
| 治理 review | stage-harness 验收议会 + ECC | 安全、团队标准、ripple effect | 多角色 + 可人工 |

### 7.6 FIX — 问题修复

| 项目 | 内容 |
|------|------|
| **主负责** | Flow-Next（review → fix 循环已内置） |
| **stage-harness 补充** | 轮次限制（最多 3 轮 FIX → VERIFY 循环，超出升级人工） |
| **产物** | 修复代码、更新后的 evidence |

### 7.7 DONE — 交付与沉淀

| 项目 | 内容 |
|------|------|
| **主负责** | stage-harness（发布议会）+ ECC（治理）+ Flow-Next memory（学习） |
| **工作流** | 1. 发布议会审查（交付完整性、安全签署、文档） → 2. 生成交付包 → 3. 经验候选提名（Flow-Next memory + ECC） → 4. 人工审核后晋升 |
| **产物** | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` |
| **出口** | 发布议会 verdict = RELEASE_READY |

---

## 八、Review 体系总览

| 阶段 | Flow-Next Review | stage-harness 议会 | 关系 |
|------|-----------------|-------------------|------|
| SPEC | — | 轻议会（3~5 reviewer） | 议会独占 |
| PLAN | `/flow-next:plan-review` | 计划议会（5~7 reviewer） | 互补：技术 + 治理 |
| EXECUTE | `/flow-next:impl-review`（每个 task 后） | — | Flow-Next 独占 |
| VERIFY | `/flow-next:epic-review` + ECC | 验收议会（5~7 reviewer） | 互补：compliance + 治理 |
| DONE | — | 发布议会（3~4 reviewer） | 议会独占 |

---

## 九、动态强度控制

不是每个 feature 都走最重路径。根据风险等级动态调整：

| 控制维度 | 低风险 | 中风险 | 高风险 |
|---------|-------|-------|-------|
| CLARIFY | 可跳过 brainstorming | brainstorming + interview | 完整 brainstorming + 深度 interview |
| 轻议会 | 可跳过 | 3 reviewer | 5 reviewer |
| Plan depth | short | standard | deep |
| Plan-review | 可跳过 | 标准 | 标准 + 议会 |
| 计划议会 | 可跳过 | 5 reviewer | 7 reviewer |
| EXECUTE 模式 | Ralph 自治 | worker + review | worker + review + 人工检查点 |
| Impl-review | 标准 | 标准 + Codex 跨模型 | 标准 + Codex + 议会 |
| 验收议会 | 3 reviewer | 5 reviewer | 7 reviewer |
| 发布议会 | 2 reviewer | 3 reviewer | 4 reviewer |
| Decision Bundle | 仅 PLAN→EXECUTE | 全部触发点 | 全部触发点 + 额外检查点 |

风险等级在 CLARIFY 阶段评估，依据：
- 是否涉及安全敏感模块
- 是否跨多个子系统
- 是否涉及数据迁移
- 是否有高不确定性

---

## 十、选型分层（V3 继承 + 修订）

### 10.1 确定性已选依赖

| 组件 | 定位 | 变化 |
|------|------|------|
| Claude Code 原生能力 | 运行时底座 | 不变 |
| Flow-Next | **全流程执行引擎** | 从 V3 的"目标态优先主干"升级为"确定性已选依赖" |
| Superpowers | 前半程方法学层 | 不变 |
| ECC 精选子集 | 安全与质量门禁层 | 不变 |

### 10.2 增强候选项

| 组件 | 定位 | 变化 |
|------|------|------|
| adversarial-spec | SPEC/PLAN 关口增强器 | 不变 |
| memsearch | 学习层增强记忆 | Flow-Next 自带 memory 后优先级降低 |

### 10.3 降级为参考

| 组件 | 变化 |
|------|------|
| ShipSpec | 不变——规格参考标杆 |
| deep-plan / deep-implement | 不变——artifact 设计参考 |
| Ring | 不变——reviewer 思想参考 |
| aio-reflect | 不变——学习提名参考 |

---

## 十一、产物体系简化

V3 每个 feature 预计产出 30+ 文件。V4 借助 Flow-Next 的结构化 `.flow/` 体系，大幅简化：

### 已被 Flow-Next 覆盖（不再需要 stage-harness 生成）

| V3 原定产物 | Flow-Next 替代 |
|------------|--------------|
| `bridge-spec.md` | 不再需要——Flow-Next 直接消费 epic spec |
| `execution-plan.md` | `.flow/` 的 epic + tasks |
| `TASKS.json` / `TASKS.md` | `.flow/tasks/*.json + *.md`（更强：含依赖图、状态、evidence） |
| `test-strategy.md` | epic spec 内的 Test Strategy section |
| `risk-register.md` | epic spec 内的 Risk Register section + Flow-Next memory pitfalls |

### stage-harness 独有产物

| 产物 | 阶段 | 用途 |
|------|------|------|
| `decision-bundle.json` | CLARIFY / SPEC / PLAN / VERIFY 出口 | 人工决策记录 |
| `*-council-verdict.json` | SPEC / PLAN / VERIFY / DONE | 议会裁决 |
| `risk-assessment.json` | CLARIFY | 风险等级评估 |
| `metrics.json` | DONE | 量化指标（token / latency / outcome） |
| `release-notes.md` | DONE | 发布说明 |
| `delivery-summary.md` | DONE | 交付总结 |
| `learning-candidates.md` | DONE | 学习候选 |

---

## 十二、Ralph 在体系中的定位

Flow-Next 的 Ralph 是一个完整的自治运行循环。在 V4 体系中：

**定位**：EXECUTE 阶段的**可选自治引擎**。

**使用场景**：
- 低风险 feature：全程 Ralph 自治（hooks + guard + receipts）
- 中风险 feature：Ralph 自治 + 关键 task 前人工检查点
- 高风险 feature：不使用 Ralph，逐 task 手动驱动

**stage-harness 的协调方式**：
- 通过 Ralph 的 guard hooks 注入 token 预算检查
- 通过 `FLOW_RALPH` 环境变量控制 Ralph 是否启用
- 通过 receipts 目录读取 Ralph 运行记录用于 eval 数据面

---

## 十三、MVP 路线

### MVP-1：最小闭环

**目标**：打通 CLARIFY → SPEC → PLAN → EXECUTE → VERIFY 最小链路。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 1.1 | 安装 Flow-Next + Superpowers | 两个插件可正常使用 |
| 1.2 | Superpowers brainstorming + Flow-Next interview 串联 | 能从模糊需求产出清晰 spec |
| 1.3 | `flowctl epic create` + `set-plan` | epic spec 可创建 |
| 1.4 | `/flow-next:plan` 生成 tasks | task 图谱可生成 |
| 1.5 | `/flow-next:work` 执行 tasks | 代码 + 测试 + evidence 可产出 |
| 1.6 | `/flow-next:impl-review` | 跨模型 review 可运行 |
| 1.7 | 实现 Decision Bundle（PLAN→EXECUTE） | 人工拍板后才能进入 EXECUTE |
| 1.8 | 实现基础门禁（hooks） | 产物不齐全时可阻断 |

### MVP-2：议会 + 治理

**目标**：加入分层议会和 ECC 治理。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 2.1 | 实现轻议会（SPEC） | 3~5 reviewer 审查 epic spec |
| 2.2 | 实现计划议会（PLAN） | 5~7 reviewer 审查 task 图谱 |
| 2.3 | 实现验收议会（VERIFY） | 多角色审查 + ECC 安全扫描 |
| 2.4 | Decision Bundle 全触发点 | 所有阶段出口可拍板 |
| 2.5 | FIX 轮次控制 | 最多 3 轮后升级 |

### MVP-3：自治 + 发布 + 学习

**目标**：启用 Ralph 自治 + 完成 DONE 阶段 + 持续学习。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 3.1 | Ralph 自治模式集成 | 低风险 feature 可 overnight 运行 |
| 3.2 | 动态强度控制 | 根据风险等级调整流程重量 |
| 3.3 | 发布议会 | 交付完整性审查 |
| 3.4 | 交付包自动生成 | release-notes + delivery-summary |
| 3.5 | 学习流程 | Flow-Next memory + 人工晋升 |
| 3.6 | Eval 数据面 | token / latency / outcome 指标 |

---

## 十四、关键风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| **Flow-Next 与 stage-harness hooks 冲突** | 门禁机制失效 | stage-harness hooks 通过 Ralph guard 注入，不在 Flow-Next hooks 层面冲突 |
| **议会 + Flow-Next review 双重成本** | token 消耗翻倍 | 动态强度控制：低风险跳过议会，只用 Flow-Next review |
| **flowctl 作为 source of truth 的局限** | 阶段门禁元数据无处存放 | `.harness/` 目录存放治理元数据，flowctl 只管执行状态 |
| **Ralph 自治时安全风险** | 无人值守时做出危险操作 | Ralph guard hooks + token 预算 + 关键 task 前人工检查点 |
| **ECC 过重** | 治理层吞掉主流程 | 只装 security-reviewer + audit 子集，ECC 不定义产物格式 |
| **memory 层过早引入** | 复杂度上升 | 先用 Flow-Next 内置 memory，需要语义检索时再接 memsearch |

---

## 十五、超短摘要

- **机制不变**：PLAN 控制中心、议会、Decision Bundle、阶段门禁
- **底座不变**：Claude Code 原生能力
- **执行引擎**：Flow-Next（全流程：plan → work → review → Ralph）
- **治理增强层**：stage-harness（Decision Bundle + 议会 + 门禁 + 动态强度）
- **方法层**：Superpowers（CLARIFY brainstorming + 方法纪律）
- **安全层**：ECC 精选子集
- **核心调整**：stage-harness 从"编排外壳"改为"治理增强层"，不重复 Flow-Next 的编排能力

---

## 十六、结论

V4 是对 V3 的关键修订而非否定。V3 的机制设计（PLAN 控制中心、议会、Decision Bundle、门禁）全部保留。唯一的根本性调整是：

> **承认 Flow-Next 已经是一个完整的编排系统，把 stage-harness 从"编排外壳"重新定位为"治理增强层"。**

这个调整带来三个直接收益：

1. **消除双重编排**——不再有两套状态机、两套任务追踪、两套 review 体系
2. **大幅降低 stage-harness 的开发量**——不需要实现 plan 生成、task 调度、review 引擎
3. **充分利用 Flow-Next 的成熟能力**——11 命令、20 agent、Ralph 自治、跨模型 review

stage-harness 的价值不在于"什么都做"，而在于做好 Flow-Next 不做的事——**Decision Bundle、分层议会、动态强度控制、ECC 治理、发布流程**。这些恰恰是把 AI 辅助开发从"能跑"提升到"可治理"的关键。
