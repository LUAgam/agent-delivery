# Claude Code 阶段化 AI Harness — 最终修订版（V2）

## 一、文档定位

本文档是对 `idea/final-plan.md` 的最终修订版，总结并收敛前序文档中的稳定诉求，保留已有正确选型，并重点补强两件事：

1. **把 PLAN 明确提升为整个后半程的控制中心**；
2. **把阶段审查改造成分层议会模板，而不是所有阶段统一套用同一套 7 reviewer 模式**。

本文档的目标不是给出所有实现细节，而是输出一份可用于后续落地、评审与裁边的**主版本方案文档**。

与前序文档的关系：

- `idea/end.md`：保留其“少打断、硬门禁、Decision Bundle、阶段产物”的核心精神；
- `idea/end-revised.md`：保留其四层架构、职责边界与对插件现实的修正；
- `idea/final-plan.md`：保留其主干选型、桥接思路、MVP 路线；
- 本文档：进一步明确 **PLAN 作为关键门** 与 **四类议会模板**，作为后续实施的推荐主线。

---

## 二、最终判断与总原则

### 2.1 总体主张

构建一个自建 `stage-harness` 作为编排外壳：

- 用 **Superpowers** 做需求澄清；
- 用 **ShipSpec** 做规格权威；
- 用 **deep-plan / deep-implement** 做计划与执行主干；
- 用 **分层议会** 做重点节点把控；
- 用 **ECC 子集 + aio-reflect** 做治理、审计与学习。

### 2.2 三条核心原则

#### 原则 1：PLAN 是后半程的控制中心

PLAN 不是普通中间文档，而是：

- 规格到执行的转换层；
- 执行阶段的边界合同；
- 测试与验证的前置约束；
- 进入 EXECUTE 前的关键放行门。

如果 PLAN 不完整，后续开发和测试即使执行认真，也可能沿着错误方向高质量偏离。

这里的“后半程”特指：

```text
PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
```

#### 原则 2：不同阶段使用不同强度的议会

不是所有阶段都适合用同一套 7 reviewer。

更合理的方式是：

- SPEC 用轻议会；
- PLAN 用计划议会；
- VERIFY 用验收议会；
- DONE 用发布议会。

也就是说，**议会是阶段治理模板，不是固定人数的统一审查器**。

#### 原则 3：每个阶段出口都必须可审查、可阻断、可回退

每个阶段出口至少要有：

- 结构化产物；
- 状态记录；
- 阶段门禁；
- 必要时的 Decision Bundle；
- 不通过时的回退路径。

---

## 三、最终主干架构

### 3.1 四层模型

```text
┌──────────────────────────────────────────────────────────┐
│  1. 编排层 Orchestration                                  │
│     stage-harness                                          │
│     状态机 · 决策包 · 阶段门禁 · 议会调度                  │
├──────────────────────────────────────────────────────────┤
│  2. 产物生成层 Spec & Plan                                │
│     Superpowers(brainstorming) -> ShipSpec(PRD/SDD/TASKS) │
│     -> bridge -> deep-plan(plan/tdd/sections)             │
├──────────────────────────────────────────────────────────┤
│  3. 执行与验证层 Execute & Verify                         │
│     EXECUTE: deep-implement(section级 TDD 与实现级审查)    │
│     VERIFY: 验收议会(标准 7 reviewer)                      │
├──────────────────────────────────────────────────────────┤
│  4. 治理与学习层 Govern & Learn                           │
│     ECC 子集(安全/治理) + aio-reflect(经验提名)            │
└──────────────────────────────────────────────────────────┘
```

### 3.2 状态机

```text
IDEA -> CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
                                         ^        |
                                         └────────┘
```

可选前置：

```text
DISCOVER -> CLARIFY
```

适用场景：目标过大、范围模糊、需要先拆成多个 feature/spec。

---

## 四、职责与控制权矩阵

| 阶段 | 主负责组件 | 权威产物 | 重点控制对象 | 放行方式 |
|------|-----------|----------|--------------|----------|
| CLARIFY | Superpowers（仅 brainstorming） | `clarification-notes.md`、`decision-bundle.json` | 问题空间、边界、假设 | Decision Bundle + 阶段门禁 |
| SPEC | ShipSpec | `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md` | 规格完整性、一致性、可落地性 | **轻议会** |
| PLAN | bridge + deep-plan | `bridge-spec.md`、`claude-plan.md`、`claude-plan-tdd.md`、`sections/*` | 计划完整性、任务切分、依赖、测试、风险 | **计划议会** |
| EXECUTE | deep-implement | 代码、测试、section 记录、原子提交 | section 范围、TDD、实现级审查、漂移控制 | section 内循环 |
| VERIFY | 验收议会（标准 7 reviewer） | `review-report.md`、`test-report.md`、`verification.json` | 全量变更质量、跨 section 风险、测试证据 | **验收议会** |
| FIX | deep-implement + 验收议会重跑 | `fix-log.md`、更新后的 `verification.json` | 问题闭环、复验证据 | FIX -> VERIFY 循环 |
| DONE | 发布议会 + ECC + aio-reflect | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` | 交付完整性、安全、文档、学习治理 | **发布议会** |

关键原则：

- 每个阶段只有一个主负责组件；
- 每个阶段只有一个权威产物集合；
- 每个阶段出口只回答该阶段最该回答的问题。

---

## 五、四类议会模板（最终版）

议会不是某一个固定插件，而是 `stage-harness` 统一调度的**阶段治理模板**。  
底层可以复用现有 agent、reviewer 或自建角色，但其**输入、输出、裁决语义**应统一。

特别说明：

- 四类议会并不要求覆盖全部阶段；
- 它们只绑定四个关键出口：`SPEC`、`PLAN`、`VERIFY`、`DONE`；
- `CLARIFY` 主要依赖 Decision Bundle；
- `EXECUTE` 主要依赖 section 内循环与实现级审查；
- `FIX` 主要依赖 FIX -> VERIFY 的问题闭环。

### 5.1 A 类：轻议会（用于 SPEC）

#### 定位

规格评审会。  
目标是判断：**当前规格是否足够稳定，可以进入 PLAN。**

#### 推荐规模

- **3~5 个 reviewer**

#### 关注重点

- 需求是否完整；
- PRD / SDD / TASKS 是否一致；
- 是否有明显漏项、冲突、隐含假设；
- 当前规格能否被后续计划真正承接。

#### 典型 reviewer 角色

- 规格完整性 reviewer
- 一致性 reviewer
- 可落地性 reviewer
- 可测试性 reviewer（可选）
- 安全/数据约束 reviewer（按需）

#### 输出

- `spec-council-report.md`
- `spec-council-verdict.json`

#### 裁决语义

- `GO`：可进入 PLAN
- `REVISE`：需修订后复议
- `HOLD`：存在关键未决项，先回到 Decision Bundle

#### 是否阻断

- `GO`：放行，允许进入 PLAN
- `REVISE` / `HOLD`：阻断

---

### 5.2 B 类：计划议会（用于 PLAN）

#### 定位

进入 EXECUTE 前的关键门。  
目标是判断：**当前计划是否已经足够完整、清晰、可执行、可验证。**

#### 推荐规模

- **5~7 个 reviewer**

#### 关注重点

- 需求覆盖是否完整；
- 任务与 section 切分是否合理；
- 依赖顺序是否成立；
- 测试策略是否足够；
- 架构约束是否被承接；
- 安全与高风险点是否进入计划；
- 是否具备冷启动执行条件。

#### 典型 reviewer 角色

- 覆盖性 reviewer
- 任务切分 reviewer
- 依赖路径 reviewer
- 测试策略 reviewer
- 架构承接 reviewer
- 安全风险 reviewer
- 恢复/回滚 reviewer（按需）

#### 输出

- `plan-council-report.md`
- `plan-council-verdict.json`

#### 裁决语义

- `READY`：可进入 EXECUTE
- `READY_WITH_CONDITIONS`：存在非阻断条件，需显式记录
- `BLOCK`：不能进入 EXECUTE

#### 是否阻断

- `READY`：不阻断
- `READY_WITH_CONDITIONS`：通常不阻断，但需落状态文件并跟踪
- `BLOCK`：阻断

#### 特别说明

**计划议会是整个体系里最重要的前置治理关。**  
它的职责不是优化措辞，而是判断：

> “这个计划能否真正约束后续开发与测试，而不是让下游继续自由发挥。”

---

### 5.3 C 类：验收议会（用于 VERIFY）

#### 定位

标准验收门。  
目标是判断：**实现结果是否通过正式工程验收。**

#### 推荐规模

- **标准 7 reviewer**

#### 关注重点

- 代码质量
- 业务逻辑正确性
- 安全
- 测试质量
- nil/null safety
- ripple effect / consequences
- dead code / reachability

#### 推荐底层实现

优先复用 Ring 的标准 7 reviewer 调度能力。

#### 输出

- `review-report.md`
- `test-report.md`
- `verification.json`

#### 裁决语义

- `PASS`
- `FAIL`

#### 是否阻断

- `PASS`：允许进入 DONE
- `FAIL`：必须回 FIX

#### 特别说明

验收议会是**最硬的质量放行门**。  
它不讨论“方向是否合理”，只回答：

> “结果是否过关。”

---

### 5.4 D 类：发布议会（用于 DONE）

#### 定位

交付与治理检查会。  
目标是判断：**当前结果是否具备发布、交付、文档沉淀与经验治理条件。**

#### 推荐规模

- **3~4 个 reviewer**

#### 关注重点

- 交付包是否完整；
- 最终安全扫描是否通过；
- 文档与 release notes 是否足够；
- 本次经验是否被妥善提名且未越权进入长期规则。

#### 典型 reviewer 角色

- Release readiness reviewer
- Security signoff reviewer
- Delivery/docs reviewer
- Learning/governance reviewer

#### 输出

- `release-council-report.md`
- `release-council-verdict.json`

#### 裁决语义

- `RELEASE_READY`
- `RELEASE_WITH_CONDITIONS`
- `NOT_READY`

#### 是否阻断

- `RELEASE_READY`：不阻断
- `RELEASE_WITH_CONDITIONS`：默认不阻断，但必须把条件项写入状态文件、交付摘要与发布说明；若条件项涉及未接受的安全风险、缺失交付件或关键文档缺口，则升级为阻断
- `NOT_READY`：阻断

---

## 六、PLAN 作为控制中心：最终版详细设计

### 6.1 为什么 PLAN 是最关键环节

PLAN 决定了后续：

- 开发按什么边界推进；
- 测试按什么靶子设计；
- 审查按什么基线核对；
- 风险按什么路径暴露；
- 漏项发现后回流到哪里。

如果 PLAN 不完整，下游的开发和测试就会偏；  
如果 PLAN 只描述“做什么”而不描述“如何验证”，VERIFY 阶段就会失焦；  
如果 PLAN 没把架构与依赖变成 section 边界，EXECUTE 阶段就会自由发挥。

因此：

> PLAN 不是中间站，而是后半程的控制中心。

---

### 6.2 PLAN 的输入冻结条件

进入 PLAN 前，至少应满足：

- `clarification-notes.md` 已形成；
- `decision-bundle` 中影响实现路径的关键项已拍板；
- `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md` 已产出；
- 当前不存在会直接改变计划结构的重大未决问题。

如果以下问题仍未定：

- 数据库/存储形态；
- 同步/异步处理模式；
- 多租户/单租户；
- 核心接口契约；
- 回滚/迁移方式；

则不得直接放行 PLAN，必须回到 `SPEC -> PLAN` 的阶段出口拍板。

---

### 6.3 ShipSpec -> deep-plan 的桥接要求

PLAN 的第一道控制不是写计划，而是确保桥接不失真。

### 必须带入 bridge 的信息

- PRD 的需求摘要与优先级；
- SDD 的架构决策、接口设计、数据模型；
- TASKS.json 的任务关系、依赖、验收标准、测试要求；
- 已确认的范围边界与已知风险；
- 来自澄清阶段的关键假设与限制。

### bridge 的目标

生成 `bridge-spec.md`，使 deep-plan 能在不依赖聊天上下文的情况下继续工作。

### 禁止状态

不允许出现以下情况：

- 任务依赖丢失；
- 关键验收标准丢失；
- 架构决策只留在 SDD，未传递到 plan；
- 规格未冻结，但 bridge 默认替人拍板。

也就是说，桥接不是摘要，而是：

> **把规格权威无损转成计划输入。**

---

### 6.4 PLAN 生成过程的五步质量放大

deep-plan 的价值不只是写一份 plan，而是在计划生成过程中内置质量放大链：

1. **Research**  
   - 防止 plan 脱离现有代码与外部现实；
2. **Interview**  
   - 暴露隐藏需求、边界、异常场景；
3. **External Review**  
   - 给 plan 做外部挑战，减少盲区；
4. **TDD Plan**  
   - 强制把验证策略前移；
5. **Section Splitting**  
   - 把 plan 变成可执行、可恢复、可提交的最小单元。

这五步分别控制：

- 现实性
- 完整性
- 盲区
- 可验证性
- 可执行性

---

### 6.5 PLAN 的必备控制产物

PLAN 阶段至少需要以下产物：

- `bridge-spec.md`
- `claude-plan.md`
- `claude-plan-tdd.md`
- `sections/index.md`
- `sections/section-*.md`
- `plan-council-report.md`
- `plan-council-verdict.json`

如果没有形成这一整包控制产物，就不应进入 EXECUTE。

---

### 6.6 计划议会的核心审查问题

计划议会至少要回答以下问题：

1. 所有关键需求是否都有落点？
2. 所有关键架构决策是否被 plan 继承？
3. 是否还有关键未决问题未显式暴露？
4. 每个 section 是否边界清晰、done 条件清晰？
5. 每个 section 是否已有 TDD 入口与验证靶子？
6. section 之间依赖是否清晰、无明显循环？
7. 高风险点是否有验证、缓解或回滚安排？
8. 一个冷启动执行器能否只凭 artifacts 开工？

如果这些问题里有关键问题答不上来，则 verdict 应为 `BLOCK`。

---

### 6.7 PLAN -> EXECUTE 的强门禁

进入 EXECUTE 前，不应该只检查文件存在，而应同时满足：

- 计划议会 verdict 不是 `BLOCK`；
- `claude-plan-tdd.md` 已形成，且不是泛泛“记得写测试”；
- 每个 section 有清晰范围、依赖、done 条件；
- 关键未决问题已清空或显式升级到 Decision Bundle；
- 状态文件记录本次 plan 放行结果与条件项。

也就是说：

> EXECUTE 的前提不是“计划写好了”，而是“计划已具备执行控制力”。

---

### 6.8 执行中如何持续反向校验 PLAN

PLAN 的控制不能只发生在 PLAN 阶段本身，后续还要持续反向校验。

### EXECUTE 阶段

- deep-implement 必须消费 `sections/*.md`，而不是自由读取一堆上游文档；
- section 级实现与实现级审查要检查是否越界、漏项、违反 section 约束；
- 不允许“计划之外的临场扩写”直接混入当前 section。

### VERIFY 阶段

- 验收议会要把 plan 视为审查基线；
- 不只是问“代码好不好”，还要问“是否按计划完成、是否有计划承诺未兑现”。

### 漏项回流规则

一旦执行中发现：

- 依赖顺序不成立；
- section 切分不合理；
- 测试策略无法覆盖风险；
- 关键约束未进入 plan；

则不得继续靠临场判断推进，而应：

- 回写 section 或 plan；
- 必要时回到 PLAN；
- 重新 gate；
- 再继续 EXECUTE。

这条规则的目的，是防止：

> **PLAN 在执行期被悄悄架空。**

---

## 七、阶段化把控机制（按环节）

### 7.1 CLARIFY

**目标：** 把模糊需求变成清晰问题空间。  
**产物：** `clarification-notes.md`、`decision-bundle.json`。  
**重点控制：**

- 是否已显式记录边界、假设、约束；
- 是否把关键未决问题打包，而不是中途零散打断。

### 7.2 SPEC

**目标：** 形成规格权威。  
**产物：** `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md`。  
**重点控制：**

- 规格完整性；
- PRD / SDD / TASKS 一致性；
- 是否具备进入 PLAN 的条件。  

**出口治理：** 轻议会。

### 7.3 PLAN

**目标：** 形成执行控制包。  
**产物：** `bridge-spec.md`、`claude-plan.md`、`claude-plan-tdd.md`、`sections/*`。  
**重点控制：**

- bridge 保真；
- 需求覆盖；
- 架构承接；
- 任务切分；
- 测试前移；
- section 可执行。  

**出口治理：** 计划议会。

### 7.4 EXECUTE

**目标：** 按 section 推进 TDD 实现。  
**产物：** 代码、测试、section 记录、原子提交。  
**重点控制：**

- 一次只执行一个 section；
- 必须 TDD；
- 必须做实现级审查；
- 发现漂移必须回流 plan。

### 7.5 VERIFY

**目标：** 做正式工程验收。  
**产物：** `review-report.md`、`test-report.md`、`verification.json`。  
**重点控制：**

- 全量质量放行；
- 7 路并行 reviewer；
- 关键问题归零；
- 测试证据充分。  

**出口治理：** 验收议会。

### 7.6 FIX

**目标：** 问题闭环。  
**产物：** `fix-log.md`、更新后的 `verification.json`。  
**重点控制：**

- 问题来源可追溯；
- 修复后重新跑验收；
- 最多 3 轮循环，超出升级人工干预。

### 7.7 DONE

**目标：** 形成可交付、可沉淀的结果。  
**产物：** `release-notes.md`、`delivery-summary.md`、`learning-candidates.md`。  
**重点控制：**

- 发布准备度；
- 安全最终签署；
- 文档与交付说明；
- 学习提名与人工晋升。  

**出口治理：** 发布议会。

---

## 八、Decision Bundle 机制（保留并升级）

Decision Bundle 的作用不是让系统频繁打断人，而是：

- 把必须由人拍板的问题集中到阶段出口；
- 让阶段门禁具备“阻断但不混乱”的能力；
- 让状态机知道哪些问题已解决、哪些仍待决。

推荐触发点：

- `CLARIFY -> SPEC`
- `SPEC -> PLAN`
- `VERIFY -> DONE`

其中 `VERIFY -> DONE` 的典型分工是：

- **Decision Bundle**：收束“是否接受条件发布、如何记录遗留项、是否接受当前发布条件”等必须由人拍板的问题；
- **发布议会**：对交付完整性、安全、文档与学习治理做正式判断；
- 两者可以串联：先由发布议会形成条件项，再把必须由人决策的内容整理进 Decision Bundle。

推荐格式：

```json
{
  "stage": "PLAN",
  "decisionBundle": [
    {
      "id": "D-PLAN-01",
      "question": "当前高风险迁移是否允许分两次发布？",
      "options": ["允许", "不允许"],
      "default": "允许",
      "impact": "影响 section 切分、测试范围与回滚策略",
      "evidence": "plan-council-report.md 第 3 节"
    }
  ]
}
```

---

## 九、Hooks 与状态文件（修订版）

### 9.1 事件使用策略

优先使用已在仓库生态中有实践依据的事件：

- `SessionStart`
- `Stop`
- `UserPromptSubmit`

以下事件继续作为增强项，不作为初版正式依赖：

- `TaskCompleted`
- `TeammateIdle`

也就是说，PoC 可以做，但核心阶段门禁应先建立在已验证事件之上。

### 9.2 推荐 hooks 职责

- `SessionStart`：加载状态、恢复阶段上下文、注入当前 gate 信息；
- `Stop`：执行阶段出口门禁；
- `UserPromptSubmit`：做阶段感知提醒与上下文警示。

### 9.3 推荐状态文件字段

```json
{
  "currentStage": "PLAN",
  "feature": "user-auth",
  "stageHistory": [],
  "pendingDecisions": [],
  "verifyAttempts": 0,
  "councilResults": {
    "specCouncil": null,
    "planCouncil": {
      "verdict": "READY_WITH_CONDITIONS",
      "blockingIssues": [],
      "conditionalIssues": ["补充回滚说明"]
    },
    "acceptanceCouncil": null,
    "releaseCouncil": null
  }
}
```

---

## 十、MVP 路线（按最终修订版重排）

### MVP-1：规格与计划主链打通

**目标：** 打通 `CLARIFY -> SPEC -> PLAN`，并建立 PLAN 的关键控制力。

关键任务：

1. 创建 `stage-harness/` 插件脚手架；
2. 实现状态文件与基础门禁；
3. 接入 Superpowers brainstorming；
4. 接入 ShipSpec 产出规格；
5. 实现 `bridge-spec.md` 生成；
6. 接入 deep-plan 产出 plan / tdd / sections；
7. 实现 **轻议会**；
8. 实现 **计划议会**；
9. 让 `PLAN -> EXECUTE` 具备强门禁。

### MVP-2：执行与验收闭环

**目标：** 打通 `EXECUTE -> VERIFY -> FIX`。

关键任务：

1. 接入 deep-implement；
2. 建立 section 级漂移回流规则；
3. 接入 Ring 标准 7 reviewer；
4. 实现 **验收议会**；
5. 完成 FIX -> VERIFY 循环与轮次上限。

### MVP-3：发布、治理与学习

**目标：** 打通 `DONE` 阶段与持续学习。

关键任务：

1. 接入 ECC 子集做最终安全与治理扫描；
2. 接入 aio-reflect 做经验提名；
3. 实现 **发布议会**；
4. 建立“候选经验 -> 人工审核 -> 晋升”双轨流程；
5. 自动生成 release / delivery artifacts。

---

## 十一、关键风险与缓解

### 11.1 所有阶段都上重型议会，成本过高

**风险：** Token 与延迟失控，前期节奏过慢。  
**缓解：** 使用四类议会模板，按阶段控制强度。

### 11.2 PLAN 看起来完整，但无法真正约束执行

**风险：** EXECUTE 阶段继续自由发挥。  
**缓解：** 把 PLAN 视为控制包，而非单文件；以 section 与 TDD artifacts 作为执行入口。

### 11.3 未决问题隐式带入 PLAN

**风险：** plan 替业务或架构偷偷拍板。  
**缓解：** 决策必须进入 Decision Bundle；未拍板不得放行关键 gate。

### 11.4 执行中发现漏项，团队临场补脑

**风险：** plan 快速失效。  
**缓解：** 建立“发现漂移必须回流 PLAN”的硬规则。

### 11.5 hooks 契约不稳定

**风险：** 阻断逻辑失效或行为不一致。  
**缓解：** 先基于 `SessionStart` / `Stop` / `UserPromptSubmit` 建核心门禁；`TaskCompleted` / `TeammateIdle` 先做 PoC。

### 11.6 学习产物污染长期规则

**风险：** 规则膨胀、冲突和失控。  
**缓解：** 严格双轨制：机器只提名，人工审核后晋升。

---

## 十二、最终版一句话总结

这套方案的最终形态不是“多个插件串起来”，而是：

> 用 `stage-harness` 把澄清、规格、计划、执行、验收、发布组织成一条阶段化流水线；  
> 把 **PLAN** 定义为后半程的控制中心；  
> 把重点节点的审查改造为 **轻议会 / 计划议会 / 验收议会 / 发布议会** 四类分层治理模板；  
> 再通过状态文件、Decision Bundle 和阶段门禁确保每个环节的结果可审查、可阻断、可回退、可交付。

---

## 十三、建议作为后续实施基线的内容

后续若只保留一份主版本方案文档，建议以本文档为主，并将：

- `idea/end.md`
- `idea/end-revised.md`
- `idea/final-plan.md`

视为背景与演进记录。

本文档可作为后续：

- 方案评审；
- 实施拆解；
- gate 设计；
- 文档修订；
- 插件编排落地；

的统一基线。
