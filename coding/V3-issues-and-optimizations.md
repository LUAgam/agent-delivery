# V3 现存问题与优化建议（修订版）

> 基于 `Claude-Code-end.md`、V3 高星稳定优先版、全部前序文档、以及 **`gmickel-claude-marketplace` 仓库中 Flow-Next 插件的完整源码分析** 重新评估 V3 方案。

---

## 一、关键修正：Flow-Next 远比文档描述的更成熟

### 上一版分析的核误判

上一版分析将"Flow-Next 集成方案空白"列为 P0 阻塞性问题。这个判断是基于仅阅读 V3 方案文档而没有审阅仓库中 `gmickel-claude-marketplace` 实际代码得出的。

**经过对仓库的深入分析，这个判断需要大幅修正。**

Flow-Next（v0.26.1）在仓库中是一个高度成熟的 Claude Code 插件，具备：

| 能力维度 | 实际状态 |
|---------|---------|
| **命令接口** | 11 个 slash 命令：`plan`、`work`、`interview`、`plan-review`、`impl-review`、`epic-review`、`prime`、`sync`、`ralph-init`、`setup`、`uninstall` |
| **CLI 工具** | 完整的 `flowctl` CLI（Python），支持 40+ 子命令：epic/task CRUD、依赖图、状态管理、review 集成、memory、checkpoint 等 |
| **Artifact 体系** | 结构化的 `.flow/` 目录：`epics/*.json`、`specs/*.md`、`tasks/*.json + *.md`、`config.json`、`meta.json` |
| **Agent 体系** | 20 个专用 agent：9 个调研 scout、worker、plan-sync、quality-auditor、8 个 prime scout |
| **Skill 体系** | 16 个 skill，覆盖 plan、work、interview、review、prime、sync、worktree、browser 等 |
| **Review 能力** | 3 种 review 后端：RepoPrompt（跨模型）、Codex CLI、Export；plan-review + impl-review + epic-review 三层 |
| **自治能力** | Ralph 自治循环：hooks、receipts、guard 脚本、runs 日志、可暂停/恢复 |
| **Memory** | 可选的 pitfalls / conventions / decisions 跨会话记忆系统 |
| **Re-anchor** | 每个 task 执行前自动重新锚定 spec + 状态，防止上下文漂移 |
| **依赖管理** | task 间依赖图 + epic 间依赖，`flowctl ready` / `flowctl next` 自动排序 |

**结论**：Flow-Next 不是一个"空白"需要从头设计集成方案的组件——它是一个比 V2 中的 deep-plan + deep-implement 更完整的交付系统。V3 选择它作为后半程主干，是基于对其实际能力的正确判断。

---

## 二、总体重新评估

基于对 Flow-Next 实际代码的审阅，V3 的问题清单需要重新排序：

| 原优先级 | 问题 | 修订后优先级 | 修订原因 |
|---------|------|-----------|---------|
| P0 | Flow-Next 集成方案空白 | **P2（降级）** | Flow-Next 自身已高度成熟，真正的问题是 V3 文档没有描述它的具体能力 |
| P0 | SPEC 阶段能力真空 | **P1（微调）** | Flow-Next 的 `epic create + set-plan + interview` 可以部分承载 SPEC，问题缩小为"如何映射" |
| P1 | 文档体系断裂 | **P0（升级）** | 这现在成了最大的问题——下游实施文档和 V3 的差距更大了 |
| P1 | harness.md 补强未吸收 | **P1（不变）** | Flow-Next 的 Ralph + re-anchor 已部分覆盖，但仍有 gap |
| P2 | 状态机异常路径 | **P2（不变）** | |
| P2 | 成本模型过时 | **P2（不变）** | |
| P3 | 可验证性不足 | **P3（不变）** | |
| — | **新增：Flow-Next 与 stage-harness 的职责重叠** | **P0（新增）** | Flow-Next 本身就是一个编排系统，与 stage-harness 存在显著功能重叠 |

---

## 三、P0 — 新发现的核心问题：Flow-Next 与 stage-harness 的职责重叠

### 问题描述

这是审阅 Flow-Next 源码后发现的**最关键的架构问题**。

V3 的设计思路是：

> stage-harness 做编排外壳 → Flow-Next 做后半程交付主干

但实际审阅代码后发现，**Flow-Next 自身就是一个完整的编排系统**，它包含：

| 能力 | stage-harness 设计 | Flow-Next 已有 | 重叠程度 |
|------|-------------------|---------------|---------|
| **Plan 生成** | 调用 Flow-Next 的 plan 能力 | `/flow-next:plan` — 并行 scout 调研 + epic + tasks | ✅ 完全覆盖 |
| **Plan 审查** | 计划议会（agent teams） | `/flow-next:plan-review` — Carmack-level review | ⚠️ 高度重叠 |
| **任务执行** | 调用 Flow-Next 的 work 能力 | `/flow-next:work` — worker subagent + re-anchor | ✅ 完全覆盖 |
| **实现审查** | 验收议会（agent teams + ECC） | `/flow-next:impl-review` — 跨模型 review | ⚠️ 高度重叠 |
| **完成验证** | VERIFY 阶段 | `/flow-next:epic-review` — spec compliance review | ⚠️ 部分重叠 |
| **任务追踪** | `state.json` + 阶段历史 | `flowctl` 的 task 状态机（todo→in_progress→done） | ⚠️ 高度重叠 |
| **依赖管理** | 编排层控制 | `flowctl dep` + `flowctl ready` + `flowctl next` | ⚠️ 高度重叠 |
| **re-anchor** | EXECUTE 回流 PLAN | 每个 task 前自动 re-anchor spec + status | ✅ 完全覆盖 |
| **自治运行** | 未明确设计 | Ralph 自治循环 + hooks + receipts | Flow-Next 更强 |
| **Memory** | memsearch（增强候选） | `flowctl memory` — pitfalls / conventions / decisions | ⚠️ 部分重叠 |
| **Spec 澄清** | Superpowers brainstorming | `/flow-next:interview` — 深度 Q&A | ⚠️ 部分重叠 |

### 核心矛盾

V3 设计 stage-harness 是为了做"编排外壳"，但 Flow-Next **自身就是一个编排系统**——它有自己的 plan → work → review 流水线，自己的 task 状态机，自己的 re-anchor 机制，自己的自治循环（Ralph）。

如果 stage-harness 还要在 Flow-Next 上面再包一层编排，就会出现**双重编排**的问题：

1. stage-harness 有状态机（CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE）
2. Flow-Next 有自己的流程（plan → work → review → epic-review）
3. stage-harness 的 state.json 跟踪阶段
4. flowctl 的 task 状态也跟踪执行进度

这两套系统如何协调？谁是 source of truth？

### 三种可能的解决方向

**方向 A：stage-harness 作为"轻量 policy 层"，Flow-Next 作为"执行引擎"**

- stage-harness 只负责：Decision Bundle、阶段门禁、议会调度、学习治理
- Flow-Next 负责：全部 plan → work → review 执行
- stage-harness 通过 hooks 在关键节点注入门禁，但不重复 Flow-Next 已有的编排
- **状态来源**：以 flowctl 为 source of truth，stage-harness 读取 flowctl 状态做门禁判断

**方向 B：把 Flow-Next 降级为"task 引擎"，stage-harness 控制全流程**

- Flow-Next 只提供 flowctl 的 task CRUD 和 worker 执行能力
- 不使用 `/flow-next:plan`（改为 stage-harness 自己的 plan 流程）
- 不使用 `/flow-next:plan-review` 和 `/flow-next:impl-review`（改为议会）
- **问题**：浪费了 Flow-Next 最有价值的能力（parallel scouts、Carmack-level review、Ralph）

**方向 C：重新定义 stage-harness，使之成为 Flow-Next 的"治理增强层"**

- 接受 Flow-Next 已经是一个完整的 plan-first 编排系统
- stage-harness 不再重复 Flow-Next 的能力，而是在其上增加 V3 独有的治理机制：
  - Decision Bundle（Flow-Next 没有的：关键决策强制人工拍板）
  - 阶段门禁（SPEC → PLAN 的放行，Flow-Next 没有硬门禁）
  - 分层议会（比 Flow-Next 的 single-reviewer 更强的多角色审查）
  - ECC 治理（安全扫描、学习治理）
  - Superpowers 方法学（CLARIFY 阶段）

**建议采用方向 C**——它既保留了 V3 的核心机制价值，又不浪费 Flow-Next 的成熟能力。

---

## 四、P0 — 文档体系断裂（升级为最高优先级）

### 问题描述

基于对 Flow-Next 的深入分析，文档体系断裂的问题比之前评估的**更加严重**：

1. **DEVELOPMENT-PLAN.md** 仍然基于 V2 组件选型（ShipSpec + deep-plan + deep-implement + Ring），需要全面重写
2. **ITERATION-PLAN.md** 的 8 个迭代都基于 V2 组件，Iter-0 的 3 个 PoC 中有 2 个已失去意义
3. V3 文档中对 Flow-Next 的描述停留在"Flow 风格统一交付主干"的抽象层面，**完全没有反映 Flow-Next 的实际能力规模**（11 命令、20 agent、16 skill、flowctl CLI）
4. **最关键的缺失**：V3 没有讨论 Flow-Next 与 stage-harness 之间的职责边界问题

### 优化建议

**必须做**：

1. 在 V3 文档中增加 **Flow-Next 能力全景图**，明确列出其 11 个命令、20 个 agent 的具体作用
2. 明确 **Flow-Next 与 stage-harness 的职责分割**（参考上文方向 C）
3. 基于 V3 + Flow-Next 实际能力重写 **DEVELOPMENT-PLAN.md**

---

## 五、P1 — SPEC 阶段的重新审视

### 上一版判断的修正

上一版认为 SPEC 阶段存在"能力真空"——降级 ShipSpec 后没有替代方案。

审阅 Flow-Next 后发现：**Flow-Next 的 epic 模型可以部分承载 SPEC 功能**。

Flow-Next 的 epic spec 模板就是一个规格文档：

```
# Title
## Goal & Context
## Architecture & Data Models
## API Contracts
## Edge Cases & Constraints
## Acceptance Criteria
## Boundaries
## Decision Context
```

通过 `flowctl epic create` + `flowctl epic set-plan` 可以创建规格，通过 `/flow-next:interview` 可以做深度 Q&A 精炼。

### 剩余问题

Flow-Next 的 epic spec 格式与 V3 定义的权威产物（`PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md`）不同：

| V3 权威产物 | Flow-Next 对应物 | 覆盖度 |
|------------|-----------------|-------|
| `PRD.md` | Epic spec（Goal & Context + Acceptance Criteria） | ⚠️ 部分——缺少完整的产品需求文档结构 |
| `SDD.md` | Epic spec（Architecture & Data Models + API Contracts） | ⚠️ 部分——缺少详细的系统设计文档结构 |
| `TASKS.json` | `.flow/tasks/*.json` | ✅ 完全覆盖且更强（依赖图、状态、evidence） |
| `TASKS.md` | `.flow/tasks/*.md`（每个 task 的 Description + Acceptance） | ✅ 完全覆盖 |

### 优化建议

**两种策略选择**：

**策略 A：适配 V3 产物格式到 Flow-Next**
- 编写桥接层：从 `PRD.md` + `SDD.md` 生成 Flow-Next epic spec
- 或者反向：让 Flow-Next 的 epic spec 格式扩展为 V3 要求的 PRD + SDD

**策略 B：用 Flow-Next 的格式替代 V3 的 4 文件格式**
- 接受 Flow-Next 的 epic spec + task spec 作为规格权威
- 不再强制要求独立的 PRD.md / SDD.md
- SPEC 阶段的产物改为：epic spec（`.flow/specs/fn-N.md`）+ task 图谱（`.flow/tasks/*.json + *.md`）

**建议采用策略 B**——因为：
1. Flow-Next 的格式已经过实战验证
2. 避免桥接层增加复杂度
3. 与后半程的 plan → work → review 流程天然衔接
4. task 依赖图比 `TASKS.json` 更强（有 `depends_on` + `flowctl ready` 自动排序）

如果需要保留 PRD/SDD 格式的部分价值，可以在 epic spec 模板中增加对应 section。

---

## 六、P1 — harness.md 补强与 Flow-Next 能力的交叉分析

### 重新评估

`harness.md` 提出的 7 项补强中，**Flow-Next 已经覆盖了 4 项**：

| harness.md 补强项 | Flow-Next 覆盖情况 | 仍需补充？ |
|------------------|-------------------|----------|
| **Session Handoff** | Ralph 每次迭代 fresh context + re-anchor | ⚠️ 部分——Ralph 的接力机制不等于显式 handoff 文档 |
| **运行时 Evaluator** | `/flow-next:impl-review`（Carmack-level 跨模型 review） | ✅ 已覆盖——且比"轻量 evaluator"更强 |
| **持续验证前移** | 每个 task 前 re-anchor + 每个 work 后 review | ✅ 已覆盖 |
| **Eval Harness 数据面** | Ralph 的 runs 日志 + receipts + evidence JSON | ⚠️ 部分——有 evidence 但缺少 token/latency/outcome 指标 |
| **动态启用重型组件** | 未覆盖 | ❌ 需要 stage-harness 补充 |
| **并行 agent 扩展位** | worker subagent + 20 个专用 agent | ✅ 已有丰富的角色分工 |
| **Planner + Generator + Evaluator 三角色** | plan skill + worker agent + quality-auditor / impl-review | ✅ 已实现 |

### 仍需 stage-harness 补充的

1. **Decision Bundle**：Flow-Next 没有"关键决策强制人工拍板"的机制
2. **动态强度控制**：Flow-Next 没有按风险等级调整 review 深度的能力
3. **token / latency 量化指标**：Flow-Next 的 evidence 是定性的，缺少定量的 eval 数据面
4. **ECC 治理层**：安全扫描、学习候选治理不在 Flow-Next 范围内
5. **发布议会**：Flow-Next 的 epic-review 只检查 spec compliance，不做发布准备度审查

---

## 七、P2 — Flow-Next 与 V3 状态机的映射

### 映射分析

V3 状态机与 Flow-Next 流程的对应关系：

```
V3 状态机:     IDEA → CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE
                  │       │        │      │       │         │       │      │
Flow-Next 对应:   │  interview  epic    plan    work   impl-review  │  epic-review
                  │       │    create     │       │         │       │      │
stage-harness:  Superpowers  Decision   议会    门禁     ECC    FIX轮次  发布议会
  独有价值:     brainstorm   Bundle   (轻议会) (计划议会)  治理    控制    + 学习
```

### 关键发现

1. **CLARIFY**：Superpowers 的 brainstorming 与 Flow-Next 的 interview 是互补的（brainstorming 偏发散，interview 偏收敛），可以串联使用
2. **SPEC**：Flow-Next 的 `epic create` + `set-plan` + `interview` 可以承载主体，stage-harness 补 Decision Bundle
3. **PLAN**：Flow-Next 的 `/flow-next:plan`（并行 scouts + task 生成）完全覆盖，stage-harness 补 计划议会 + 门禁
4. **EXECUTE**：Flow-Next 的 `/flow-next:work`（worker + re-anchor + review）完全覆盖
5. **VERIFY**：Flow-Next 的 `/flow-next:impl-review` 覆盖代码审查，但 stage-harness 可补 ECC 安全扫描 + 多角色验收议会
6. **FIX**：Flow-Next 的 review → fix 循环已内置，stage-harness 补轮次限制和升级策略
7. **DONE**：stage-harness 独有价值最大——发布议会、交付包、学习治理

### 优化建议

重新定义 stage-harness 的角色为 **Flow-Next 的治理增强层**：

```
┌───────────────────────────────────────────────────────────┐
│  stage-harness（治理增强层）                                │
│  Decision Bundle · 分层议会 · 阶段门禁 · 动态强度 · 学习治理  │
├───────────────────────────────────────────────────────────┤
│  Superpowers（前半程方法学）                                │
│  CLARIFY 阶段的 brainstorming + 方法纪律                    │
├───────────────────────────────────────────────────────────┤
│  Flow-Next（全流程执行引擎）                                │
│  epic/task 模型 · plan · work · review · Ralph · flowctl   │
├───────────────────────────────────────────────────────────┤
│  ECC 精选子集（安全与质量门禁）                              │
│  security-reviewer · audit · safety gate                  │
├───────────────────────────────────────────────────────────┤
│  Claude Code 原生能力（运行时底座）                          │
│  hooks · subagents · agent teams · rules / skills / MCP    │
└───────────────────────────────────────────────────────────┘
```

---

## 八、其他仍需关注的问题

### 8.1 Flow-Next 的 Ralph 与 stage-harness 的关系

Flow-Next 的 Ralph 是一个**完整的自治运行循环**（hooks + guard + receipts + runs 日志）。V3 文档完全没有讨论：

- stage-harness 是否使用 Ralph？
- 如果使用，stage-harness 的门禁如何与 Ralph 的 guard hooks 协调？
- 如果不使用，是否浪费了 Flow-Next 最强的自治能力？

**建议**：明确 Ralph 在 V3 体系中的位置——最可能的方案是让 Ralph 作为 EXECUTE 阶段的执行引擎，stage-harness 在 Ralph 的 hooks 中注入阶段门禁。

### 8.2 Review 体系的统一

V3 设计了**分层议会**（轻议会、计划议会、验收议会、发布议会），Flow-Next 设计了 **Carmack-level review**（plan-review、impl-review、epic-review）。

两者不是替代关系而是互补关系：

- Flow-Next 的 review 是**跨模型的技术 review**（Claude 实现 → GPT 审查）
- V3 的议会是**多角色的治理 review**（多个 reviewer agent 从不同视角审查）

**建议**：
- SPEC 阶段：轻议会（stage-harness）
- PLAN 阶段：`/flow-next:plan-review`（Flow-Next） + 计划议会（stage-harness）
- EXECUTE/VERIFY 阶段：`/flow-next:impl-review`（Flow-Next） + 验收议会（stage-harness 的 ECC 增强）
- DONE 阶段：发布议会（stage-harness 独有）

### 8.3 产物体系的简化机会

既然 Flow-Next 已经有了结构化的 `.flow/` 产物体系，V3 的部分产物可以简化：

| V3 原定产物 | 可否由 Flow-Next 替代 |
|------------|---------------------|
| `bridge-spec.md` | ✅ 不再需要——Flow-Next 直接消费 epic spec |
| `execution-plan.md` | ✅ 由 `.flow/` 的 epic + tasks 替代 |
| `test-strategy.md` | ⚠️ 可嵌入 epic spec 的 section |
| `risk-register.md` | ⚠️ 可用 Flow-Next memory 的 pitfalls 替代 |

### 8.4 成本模型需要基于 Flow-Next 重建

Flow-Next 的成本特征与 V2 完全不同：

- **Plan 阶段**：并行 scouts（多个 subagent）+ task 生成，成本取决于 scout 数量和调研深度
- **Work 阶段**：worker subagent per task + re-anchor，每个 task 独立计费
- **Review 阶段**：跨模型 review（RepoPrompt/Codex）+ 可能的 fix 循环

**建议**：在 MVP 中用实际运行数据建立成本基线。

---

## 九、修订后的优先级排序

| 优先级 | 问题 | 行动项 |
|-------|------|-------|
| **P0** | Flow-Next 与 stage-harness 的职责重叠 | 明确 stage-harness 为"治理增强层"（方向 C），不重复 Flow-Next 的编排能力 |
| **P0** | 文档体系断裂 | 基于 Flow-Next 实际能力重写 DEVELOPMENT-PLAN.md 和 ITERATION-PLAN.md |
| **P1** | SPEC 阶段产物格式映射 | 决定是适配 V3 的 PRD/SDD 到 Flow-Next，还是直接用 Flow-Next 的 epic spec 格式 |
| **P1** | Ralph 在 V3 体系中的定位 | 明确 Ralph 是否作为 EXECUTE 的自治引擎 |
| **P1** | Review 体系统一 | 明确 Flow-Next review 与 stage-harness 议会的分工 |
| **P2** | harness.md 补强与 Flow-Next 的 gap 分析 | 明确 stage-harness 需要补充的 3 项能力（Decision Bundle、动态强度、eval 数据面） |
| **P2** | 状态机异常路径 | 在 flowctl 状态基础上扩展 |
| **P3** | 成本模型 | 基于 Flow-Next 实际运行数据重建 |
| **P3** | 可验证性标准 | 定义量化边界 |

---

## 十、总结

### 核心判断修正

V3 选择 Flow-Next 作为后半程主干，这个决策现在看来是**非常正确的**。Flow-Next 在仓库中是一个高度成熟的系统（v0.26.1，11 命令、20 agent、16 skill、完整的 flowctl CLI），其能力远超 V3 文档中"`.flow/*` + `flowctl` 的 plan-first 交付子集能力"的描述。

但正因为 Flow-Next 如此成熟，**V3 需要解决的核心问题从"Flow-Next 如何集成"变成了"stage-harness 还需要做什么"**。

### stage-harness 的真正独有价值

在 Flow-Next 已经覆盖大部分执行能力的前提下，stage-harness 的不可替代价值收束为：

1. **Decision Bundle** — Flow-Next 没有"关键决策强制人工拍板"的机制
2. **分层议会** — Flow-Next 有 review 但不是多角色多视角的议会模式
3. **动态强度控制** — 按风险等级调整流程重量
4. **CLARIFY 阶段** — Superpowers brainstorming（Flow-Next 的 interview 更偏收敛）
5. **ECC 治理** — 安全扫描、学习治理
6. **发布议会 + DONE 阶段** — 交付包、release notes、learning candidates

### 建议的下一步

1. **立即**：重新定义 stage-harness 的角色为"Flow-Next 的治理增强层"，而非"在 Flow-Next 上包一层编排"
2. **立即**：在 V3 文档中增加 Flow-Next 的完整能力描述和与 stage-harness 的职责分割
3. **尽快**：决定 SPEC 阶段的产物格式策略（V3 的 PRD/SDD vs Flow-Next 的 epic spec）
4. **尽快**：明确 Ralph 在 V3 体系中的位置
5. **后续**：基于实际运行数据建立成本模型
