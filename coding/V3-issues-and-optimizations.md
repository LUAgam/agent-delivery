# V3 现存问题与优化建议

> 基于 `Claude-Code-end.md`、`Claude-Code-阶段化-AI-Harness-V3-高星稳定优先版.md`、`DEVELOPMENT-PLAN.md`、`ITERATION-PLAN.md`、`harness.md`、`STAGE-HARNESS-REUSE-ASSESSMENT.md` 等全部前序文档的交叉审读，对 V3 方案做一次系统性的问题识别与优化建议。

---

## 一、总体判断

V3 在**机制设计层**上非常成熟：机制与承载分离、四级选型分层、PLAN 控制中心、Decision Bundle、分层议会——这些核心设计经得起推敲。

但从"方案文档"到"可落地实施"之间，仍然存在**七类问题**：

1. 文档体系内部的断裂与对齐缺失
2. Flow-Next 作为后半程主干的落地空白
3. SPEC 阶段"自定义模板"的能力真空
4. harness.md 的关键补强未被 V3 正式吸收
5. 状态机缺少异常路径与并行设计
6. 成本模型未随 V3 选型更新
7. 方案的"可验证性"不足

---

## 二、问题 1：文档体系内部断裂 — V3 收敛了选型，但下游文档仍在用 V2

### 问题描述

V3（`Claude-Code-end.md` + `高星稳定优先版.md`）已经明确：

- ShipSpec **降级为参考**
- deep-plan / deep-implement **降级为参考**
- Ring **降级为参考**
- aio-reflect **移除主依赖**
- Flow-Next 成为**后半程统一交付主干**

但 `DEVELOPMENT-PLAN.md` 和 `ITERATION-PLAN.md` 这两份**实施级文档**仍然以 V2 的组件选型为基础：

| 实施文档中的假设 | V3 的实际决策 | 冲突程度 |
|----------------|-------------|---------|
| SPEC 由 ShipSpec `/feature-planning` 承担 | SPEC 改为 stage-harness + 自定义模板 | **高** |
| PLAN 由 bridge + deep-plan 承担 | PLAN 改为 Flow-Next + stage-harness | **高** |
| EXECUTE 由 deep-implement 承担 | EXECUTE 改为 Flow-Next | **高** |
| VERIFY 由 Ring 7 路 reviewer 承担 | VERIFY 改为 agent teams + ECC 子集 | **高** |
| DONE 由 ECC + aio-reflect 承担 | aio-reflect 移除，学习层改为 native memory + memsearch | **中** |
| 桥接脚本 `bridge-shipspec-to-deepplan.sh` | ShipSpec 和 deep-plan 都不再是主链 | **高 — 该脚本不再需要** |
| Iter-0 的三个 PoC（Hook、Superpowers 截获、ShipSpec 无 Ralph Loop） | 只有 Superpowers 截获 PoC 仍然有意义 | **中** |

### 影响

如果按 V3 选型去做实际开发，但参考的是 V2 时代的 `DEVELOPMENT-PLAN.md` 和 `ITERATION-PLAN.md`，会导致：

- 开发团队不知道该信哪个
- 实现出来的东西和方案对不上
- 桥接脚本、Hook 配置、组件裁剪清单全部需要重写

### 优化建议

**必须做**：基于 V3 选型重写 `DEVELOPMENT-PLAN.md` 和 `ITERATION-PLAN.md`，或明确标注"这两份文档基于 V2 选型，V3 下需做 X、Y、Z 调整"。

**建议做**：在 V3 主文档中增加一节"与前序实施文档的差异清单"，让读者一眼看到哪些前序结论已失效。

---

## 三、问题 2：Flow-Next 落地空白 — V3 最关键的承载选型没有任何集成方案

### 问题描述

Flow-Next 在 V3 中被定位为**后半程统一交付主干**，承担 PLAN、EXECUTE、VERIFY 前支撑三个最重要的阶段。但在整个文档体系中：

1. **没有 Flow-Next 的具体集成方案**：没有说明 `.flow/*` 的 artifact 格式是什么、`flowctl` 的命令接口是什么、如何与 stage-harness 的状态机对接
2. **没有 Flow-Next 的能力裁剪清单**：V2 时代对 ShipSpec、deep-plan、Ring 都有详细的"保留什么、禁用什么"清单，但 V3 对 Flow-Next 没有同等精度的裁剪
3. **没有 Flow-Next 的 PoC 验证项**：V2 的 ITERATION-PLAN 对 ShipSpec 有 PoC（无 Ralph Loop 运行），对 Superpowers 有 PoC（截获），但 V3 没有给 Flow-Next 设计任何 PoC
4. **没有 Flow-Next 的桥接规格**：V3 的 SPEC 阶段产出 `PRD.md / SDD.md / TASKS.json / TASKS.md`，但这些产物如何输入到 Flow-Next 的 `.flow/*` 系统中，没有说明
5. **没有 Flow-Next 的降级路径**：V2 对每个组件都设计了"如果集成失败用内联 prompt 替代"的降级策略，但 V3 没有给 Flow-Next 设计降级路径

### 为什么这是最严重的问题

Flow-Next 不是可选增强项——它是**后半程主干**。如果它的集成方案不清楚，那 V3 的 PLAN → EXECUTE → VERIFY 整条链路实际上是空的。

而且 V3 文档中自己也提到 Flow-Next 只有约 552 stars，是所有确定性/目标态组件中成熟度最低的。把最关键的位置交给成熟度最低的组件，同时又没有详细的集成方案和降级路径，这是一个显著的风险敞口。

### 优化建议

**必须做**：

1. 为 Flow-Next 编写一份与 V2 对 ShipSpec / deep-plan 同等精度的**能力裁剪清单**（保留什么、不用什么）
2. 为 Flow-Next 设计至少 2 个 **PoC 验证项**：
   - PoC-A：`.flow/*` artifact 格式是否能承载 V3 定义的权威产物（`execution-plan.md`、`test-strategy.md` 等）
   - PoC-B：`flowctl` 的 task tracking / dependency graph 是否能与 stage-harness 的 `state.json` 协同工作
3. 为 Flow-Next 设计**降级路径**：如果 Flow-Next 集成失败，用什么替代——是退回到 deep-plan + deep-implement？还是用内联 prompt + 自定义 artifact 模板？

**建议做**：

4. 在 V3 主文档的 PLAN 阶段部分，补充 Flow-Next 的 artifact 与 V3 权威产物之间的**映射关系**
5. 评估 Flow-Next 的 `.flow/*` 产物格式是否需要做桥接（类似 V2 的 `bridge-shipspec-to-deepplan.sh`），如果需要则明确桥接方案

---

## 四、问题 3：SPEC 阶段"自定义模板"的能力真空

### 问题描述

V3 把 SPEC 阶段的主负责从 ShipSpec 改为 `stage-harness + 自定义 spec 模板`。这意味着：

- ShipSpec 的 `prd-gatherer → design-architect → task-planner` 这条自动化生产链不再是默认
- 权威产物仍然是 `PRD.md / SDD.md / TASKS.json / TASKS.md`
- 但**谁来生成这些产物**变得模糊了

V3 只说"ShipSpec 可以继续作为参考标杆"，但没有回答：

1. 自定义 spec 模板的**具体内容**是什么？（模板结构、必填字段、质量标准）
2. 在没有 ShipSpec 的情况下，靠什么能力来**自动生成**这四份产物？是纯 prompt？还是专用 agent？还是人工编写？
3. 从"参考 ShipSpec 的思路"到"拥有自己的成熟规格引擎"，中间的**过渡期怎么走**？

### 影响

如果不解决这个问题，V3 的 SPEC 阶段就会退化为"人工写 PRD + 人工写 SDD + 人工维护 TASKS"，而这恰恰是 stage-harness 想要通过 AI 自动化消除的痛点。

### 优化建议

**必须做**：

1. 明确 SPEC 阶段的**生成策略**：是用 stage-harness 内置的 `spec-generator` agent？是复用 ShipSpec 的 agents 但嵌入到 stage-harness 中？还是纯 prompt-driven？
2. 编写 `PRD.md / SDD.md / TASKS.json / TASKS.md` 的**模板规范**（必填字段、格式约定、质量 checklist）

**建议做**：

3. 在 MVP-1 中采用"**先用 ShipSpec 过渡，后续逐步内化**"的策略：
   - MVP-1：仍然使用 ShipSpec 的核心 agents 生成产物，但由 stage-harness 管控流程
   - MVP-2+：逐步把 ShipSpec 的 prompt 和 agent 设计内化到 stage-harness 的自有模板中
4. 这种策略可以避免"一步到位但什么都没有"的真空期

---

## 五、问题 4：harness.md 的关键补强未被 V3 正式吸收

### 问题描述

`harness.md` 基于 Anthropic 的最新 harness engineering 实践，提出了 7 项关键补强：

| 补强项 | 解决什么问题 | V3 中是否吸收 |
|-------|------------|-------------|
| Session Handoff | 跨会话接力 | V3 主文档**未提及** |
| 运行时 Evaluator | 执行过程中的外部挑刺 | V3 主文档**未提及** |
| 持续验证前移（session 级 smoke test） | 避免"总验收才暴雷" | V3 主文档**未提及** |
| Eval Harness 数据面（trace / metrics / grader） | 量化质量和学习基础 | V3 主文档**未提及** |
| 动态启用重型组件 | 避免"固定仪式流" | V3 **部分提及**（agent teams 条件启用） |
| 并行 agent / 专业 agent 扩展位 | 执行期角色协作 | V3 **未提及** |
| Planner + Generator + Evaluator 三角色结构 | 执行器自审不可靠 | V3 **未提及** |

这些补强在 `DEVELOPMENT-PLAN.md` 中已经被纳入了阶段详细设计（Session Loop、持续验证、Eval Harness 数据面等），但 V3 的两份主文档（`Claude-Code-end.md` 和 `高星稳定优先版.md`）都**没有正式把它们纳入架构描述**。

### 影响

1. V3 主文档对外传递的是"**静态阶段编排**"的形象，缺少"**动态运行时 harness**"的维度
2. `harness.md` 的补强如果不被 V3 正式吸收，就会停留在"补充建议"的地位，后续实施中容易被忽略
3. Session Handoff 和 Eval Harness 数据面对于长时执行的稳定性至关重要，缺少它们会导致系统在复杂 feature 上"越跑越偏"

### 优化建议

**建议做**：在 V3 的四层架构中，**正式新增"运行时 harness 层"**或将其纳入编排层的子层：

```
原四层：编排层 → 方法层 → 交付主干层 → 治理与学习层

建议五层：
  编排层（状态机 + 门禁 + 议会 + Decision Bundle）
  运行时 harness 层（Session Handoff + 持续验证 + Evaluator + Trace）  ← 新增
  方法层（Superpowers）
  交付主干层（Flow-Next）
  治理与学习层（ECC + memory）
```

或者至少在 V3 主文档中明确声明：

> harness.md 中的 Session Handoff、运行时 Evaluator、持续验证前移、Eval Harness 数据面属于 V3 架构的正式组成部分，分别在 PLAN 和 EXECUTE 阶段生效。

---

## 六、问题 5：状态机缺少异常路径与并行设计

### 问题描述

V3 的状态机是：

```
IDEA → CLARIFY → SPEC → PLAN → EXECUTE → VERIFY → FIX → DONE
                                       ↑        │
                                       └────────┘
```

这是一条**纯线性状态机**加一个 FIX 循环。但实际工程中存在多种异常路径，V3 没有明确设计：

#### 5.1 回流路径不完整

V3 说"EXECUTE 发现偏离必须回流 PLAN"，但没有明确：

- VERIFY 发现的是**架构层面问题**，需要回流到 SPEC 还是 PLAN？
- PLAN 阶段发现 SPEC 有漏洞，能否直接回流到 SPEC？
- 回流后，被跳过的中间阶段（如 SPEC → PLAN 之间的轻议会）是否需要重新运行？

目前的状态机只支持：
- `EXECUTE ↔ VERIFY/FIX` 循环
- `EXECUTE → PLAN` 回流（文字描述，非状态机定义）

缺少：
- `VERIFY → SPEC`（发现规格层问题）
- `PLAN → SPEC`（发现规格遗漏）
- `VERIFY → PLAN`（发现计划层问题而非代码层问题）

#### 5.2 并行执行未设计

当一个 feature 被拆分为多个 section 时：

- section 之间如果没有依赖，能否**并行执行**？
- 如果并行执行，VERIFY 是等所有 section 完成后统一验收，还是 section 级增量验收？
- 并行执行时，状态机的 `currentStage` 怎么表达"EXECUTE 中的第 3/5 个 section 完成"？

#### 5.3 外部中断与恢复未形式化

- token 耗尽
- 网络中断
- 人工主动暂停
- 外部依赖不可用

这些情况下，状态机应该进入什么状态？`DEVELOPMENT-PLAN.md` 提到了 `WAITING_HUMAN`，但 V3 主文档的状态机定义中没有这个状态。

### 优化建议

**建议做**：

1. 在状态机中**显式增加回流箭头**：

```
IDEA → CLARIFY → SPEC ⇄ PLAN → EXECUTE ⇄ VERIFY → FIX → DONE
                  ↑                        │
                  └────────────────────────┘  (架构层问题回流)
```

2. 定义 `PAUSED` / `WAITING_HUMAN` / `ERROR` 三种**异常状态**
3. 在 `state.json` 中增加 `sectionProgress` 字段，支持 section 级进度追踪
4. 明确回流后的"重新验证范围"规则（是从回流点开始重新运行所有后续阶段，还是只重新运行受影响的阶段）

---

## 七、问题 6：成本模型未随 V3 选型更新

### 问题描述

`ITERATION-PLAN.md` 提供了详细的 token 成本预估：

| 环节 | Token 预估 |
|------|-----------|
| SPEC（ShipSpec） | ~30K |
| SPEC 轻议会 | ~50K |
| PLAN（bridge + deep-plan） | ~80K |
| PLAN 计划议会 | ~150K |
| EXECUTE（deep-implement） | ~50K/section |
| VERIFY 验收议会（Ring 7 路） | ~200K |
| DONE（ECC + aio-reflect） | ~30K |
| **单 feature 合计** | **~600K~1M+** |

但 V3 更换了几乎所有承载组件，这个成本模型**完全失效**：

- SPEC 不再用 ShipSpec，用自定义模板 — 成本未知
- PLAN 不再用 deep-plan，用 Flow-Next — 成本未知
- EXECUTE 不再用 deep-implement，用 Flow-Next — 成本未知
- VERIFY 不再用 Ring 7 路，用 agent teams + ECC 子集 — 成本未知
- 议会不再由 Ring 执行，改由 Claude Code agent teams 执行 — 成本模型不同

### 影响

没有准确的成本模型，就无法做：
- token 预算规划
- 动态强度控制的阈值设定
- 议会规模的成本权衡
- "低风险走轻路径"的成本收益判断

### 优化建议

**建议做**：

1. 基于 Flow-Next 和 agent teams 的实际运行数据，**重建成本模型**
2. 如果没有实际数据，至少做一次**对比估算**：agent teams 的议会 vs Ring 的 7 路 reviewer，token 消耗差异预计在什么量级
3. 在 V3 主文档中标注"V2 的成本模型不再适用"

---

## 八、问题 7：方案的"可验证性"不足

### 问题描述

V3 做了很多判断，但部分关键判断**缺乏可验证的标准**：

| V3 的判断 | 验证标准是否清晰 |
|----------|---------------|
| "Flow-Next 比 deep-plan + deep-implement 更适合做统一主干" | ❌ 没有给出比较维度和评判标准 |
| "ECC 精选子集不能反向吞掉主流程" | ❌ 没有定义"吞掉"的量化边界 |
| "agent teams 条件启用，小任务优先退回 subagents" | ⚠️ 有方向但没有给出"小任务"的判定标准 |
| "治理层不能反向吞掉主流程" | ❌ 什么算"治理层吞掉主流程"？ |
| "增强项可以存在，但不能反客为主" | ❌ 什么算"反客为主"？ |

### 影响

这些判断如果不可验证，后续实施中就容易出现：
- 团队对"什么时候该用 agent teams"各有理解
- ECC 逐步扩大范围但没人能判断是否"过界"
- Flow-Next 和 stage-harness 之间的职责边界模糊

### 优化建议

**建议做**：为每个关键判断定义**可验证的边界条件**：

1. **agent teams vs subagents 的启用标准**：
   - section 数 > 5 或 riskLevel = high → agent teams
   - section 数 ≤ 5 且 riskLevel ≤ medium → subagents
   
2. **ECC 的"不越界"标准**：
   - ECC 组件参与的阶段不超过 VERIFY + DONE
   - ECC 不定义任何主链 artifact 的格式
   - ECC 的 token 消耗占单 feature 总消耗的比例不超过 15%

3. **增强项"不反客为主"的标准**：
   - 增强项不出现在主状态机的任何阶段的"主负责"列
   - 增强项的缺失不阻断主链运行
   - 增强项的 token 消耗不超过对应阶段总消耗的 20%

---

## 九、其他值得优化的点

### 9.1 产物体系过重

V3 各阶段的权威产物加起来至少有 20+ 个文件：

```
CLARIFY: clarification-notes.md, decision-bundle.json
SPEC: PRD.md, SDD.md, TASKS.json, TASKS.md
PLAN: bridge-spec.md, .flow/*, execution-plan.md, test-strategy.md,
      risk-register.md, rollback-notes.md, plan-council-report.md, plan-council-verdict.json
EXECUTE: 代码, 测试, evidence, task/section 记录
VERIFY: review-report.md, test-report.md, verification.json
FIX: fix-log.md, verification.json
DONE: release-notes.md, delivery-summary.md, learning-candidates.md
```

再加上议会报告（spec-council-report.md, plan-council-report.md, release-council-report.md 等）和运行时产物（session handoff, trace, metrics），每个 feature 将产出 **30+ 个文件**。

**建议优化**：

1. 区分"**必须产出**"和"**按需产出**"的产物
2. 低风险 feature 可以合并某些产物（比如 `risk-register.md` 和 `rollback-notes.md` 合并为 `plan-notes.md`）
3. 给出一个**最小产物集**：对于简单 feature，只需要产出哪些？

### 9.2 Superpowers 的实际集成路径不清晰

V3 说 Superpowers 负责 CLARIFY 阶段和 EXECUTE 过程中的 TDD/review 方法纪律。但：

- Superpowers 在 EXECUTE 过程中**如何介入** Flow-Next 的执行流？
- Superpowers 的 brainstorming 完成后，stage-harness **如何截获控制权**？
- V2 的 `ITERATION-PLAN.md` Iter-0.2 专门为此设计了 PoC，但 V3 没有延续这个 PoC

**建议**：延续 V2 的 Superpowers 截获 PoC，因为这个问题不因 V3 选型变化而消失。

### 9.3 缺少"退出条件"和"成功标准"

V3 定义了方案是什么，但没有定义：

- 什么条件下可以判定 V3 方案**已经成功落地**？
- 什么条件下应该**放弃 V3 回到 V2** 或探索 V4？
- 什么数据可以证明 V3 比 V2 更好？

**建议**：定义 3~5 个可量化的成功标准，例如：
- 单 feature 全流程跑通时间 < X
- VERIFY 首次通过率 > Y%
- FIX 循环平均轮次 < Z
- 单 feature token 消耗在可控范围内

### 9.4 多 feature 并行管理未设计

V3 的状态机和产物体系都是**单 feature 视角**。但实际工程中经常需要：

- 同时推进多个 feature
- feature 之间有依赖
- 不同 feature 处于不同阶段

`DEVELOPMENT-PLAN.md` 的 `state.json` 设计了 `features/{feature-name}/` 的目录隔离，但 V3 主文档没有讨论：

- 多 feature 的调度策略
- feature 间依赖如何表达和管控
- feature 优先级如何影响资源分配

**建议**：在状态机上层增加一个**feature 调度层**的设计，或者明确声明"V3 当前只处理单 feature 场景，多 feature 调度作为后续扩展"。

### 9.5 人机交互模型过于模糊

V3 的 Decision Bundle 要求人工拍板，但没有明确：

- 人工拍板的**响应时间预期**（异步？同步？超时策略？）
- 人工拍板的**界面形态**（CLI？Web UI？IDE 内嵌？Slack 通知？）
- 人工**不回复**时的处理策略（V2 的 `DEVELOPMENT-PLAN.md` 提到了 `WAITING_HUMAN` 状态和超时策略，但 V3 没有）

**建议**：至少明确 Decision Bundle 的**最小交互协议**：
- 输出格式（JSON / Markdown）
- 输入格式（用户如何回复）
- 超时策略（等多久、超时后做什么）

---

## 十、优先级排序

按**对方案可落地性的影响**排序：

| 优先级 | 问题 | 原因 |
|-------|------|------|
| **P0 — 阻塞性** | Flow-Next 集成方案空白 | 后半程主干没有落地路径，方案无法实施 |
| **P0 — 阻塞性** | SPEC 阶段能力真空 | 降级 ShipSpec 后没有替代，SPEC 无法运行 |
| **P1 — 高优先** | 文档体系断裂 | 实施团队无法对齐，容易做出与 V3 矛盾的实现 |
| **P1 — 高优先** | harness.md 补强未吸收 | 长时执行稳定性无保障 |
| **P2 — 中优先** | 状态机异常路径 | 影响复杂场景下的健壮性 |
| **P2 — 中优先** | 成本模型过时 | 影响资源规划和动态控制 |
| **P3 — 低优先** | 可验证性不足 | 影响长期治理但不阻塞短期实施 |
| **P3 — 低优先** | 产物体系过重 | 可通过动态强度控制缓解 |

---

## 十一、总结

V3 方案的**机制设计**是成熟的、经得起推敲的。它真正做到了"机制与承载分离"，这让整个方案获得了很高的抗变化能力。

但 V3 目前处于一个微妙的位置：**它成功地完成了"方案收敛"，但还没有完成"实施对齐"。**

最关键的两个 gap：

1. **Flow-Next 作为后半程主干，但完全没有集成方案** — 这是整个体系的承重墙，不能是空的
2. **SPEC 阶段降级了 ShipSpec 但没有替代方案** — 这是链条的前端，断了后面都无法启动

建议的下一步动作：

1. **立即**：为 Flow-Next 编写集成方案（artifact 映射、命令接口、降级路径）
2. **立即**：明确 SPEC 阶段的过渡策略（先用 ShipSpec 过渡还是直接自建）
3. **尽快**：基于 V3 选型重写或标注 DEVELOPMENT-PLAN.md 和 ITERATION-PLAN.md
4. **尽快**：正式把 harness.md 的补强纳入 V3 架构描述
5. **后续**：补充成本模型、异常状态机、可验证标准
