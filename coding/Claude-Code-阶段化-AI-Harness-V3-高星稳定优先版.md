# Claude Code 阶段化 AI Harness — 最终推荐实施方案（V3，高 stars / 主流 / 稳定优先版）

## 一、文档定位

本文档基于你当前的 V2 主版本方案继续收敛，但把选型优先级从“功能覆盖尽量全”进一步调整为：

1. **优先选择高 stars、主流、持续更新、安装链路成熟的组件；**
2. **优先使用 Claude Code 原生能力与官方支持形态；**
3. **小众、实验性或体量偏小的仓库，只参考思路，不作为主链硬依赖。**

因此，V3 不再追求“把每个阶段都绑定到一个社区插件”，而是追求：

> **用最少、最稳、最主流的组件，搭出一条可持续维护的阶段化 AI 工程流水线。**

---

## 二、V3 的最终判断

### 2.1 总体主张

继续保留自建 `stage-harness` 作为编排外壳，但核心依赖改为：

- 用 **Claude Code 原生能力** 做底座；
- 用 **Superpowers** 做需求澄清与工程方法学；
- 用 **Flow-Next** 做计划与执行主干；
- 用 **agent teams / subagents** 实现分层议会；
- 用 **ECC 子集** 做治理、质量门禁与学习治理；
- 用 **adversarial-spec / memsearch** 作为增强项；
- 把 **ShipSpec、deep-plan、deep-implement、Ring、aio-reflect** 降级为参考实现，不再作为后续整合的主依赖。

这里的 **Flow-Next** 不是指某个独立的新插件名，而是指 **`gmickel-claude-marketplace` 中与 `.flow/*`、`flowctl`、epic/spec/task artifact 对应的 plan-first 交付子集能力**。  
也就是说，V3 选择的是一类 **Flow 风格统一交付主干**，当前优先采用的具体承载，就是该仓库中这部分 `.flow/flowctl` 能力，而不是 `gmickel-claude-marketplace` 的全部功能。

### 2.2 这次调整后的核心理由

这次收敛不是否定 V2 的思想，而是把“正确思想”绑定到更稳的组件上：

- **V2 里最值得保留的是机制，不一定是具体插件。**
- **PLAN 作为控制中心**，这个判断继续保留。
- **四类分层议会**，这个判断继续保留。
- 但承载这些机制的组件，要尽量换成更成熟、更主流、更少踩坑的方案。

### 2.3 选择表达的分层约定

为了避免“机制已经确定”和“具体承载已经完全敲定”被混为一谈，V3 中的选择表述分为三层：

1. **确定性已选依赖**
   - Claude Code 原生能力
   - Superpowers
   - ECC 精选子集
2. **目标态优先主干**
   - Flow-Next（即 `gmickel-claude-marketplace` 中 `.flow/flowctl` 的 plan-first 交付子集能力）
3. **增强候选项**
   - adversarial-spec
   - memsearch

其中，真正**不可替换**的是机制层：

- `stage-harness` 编排外壳
- PLAN 控制中心
- 分层议会
- Decision Bundle
- 阶段门禁
- 可审查 / 可阻断 / 可回退

而 Superpowers、Flow-Next、ECC 子集、增强项，属于这些机制的**当前优先承载组件**，后续如果出现更稳、更契合的同类承载，机制本身不需要重写。

---

## 三、选型原则（V3 版）

### 原则 1：官方 / 原生能力优先

凡是 Claude Code 原生支持的能力，优先不自己发明替代层：

- hooks
- subagents
- agent teams
- plugin marketplaces
- rules / skills / MCP

### 原则 2：主链组件必须满足“四高一低”

主链硬依赖尽量满足：

- **高 stars**
- **高活跃**
- **高可见度**
- **高安装成熟度**
- **低整合脆弱性**

### 原则 3：一个阶段只保留一个主负责组件

V3 继续坚持：

- 每个阶段只有一个主负责组件；
- 每个阶段只有一个权威产物集合；
- 每个阶段出口只回答该阶段最该回答的问题。

### 原则 4：增强项可以存在，但不能反客为主

增强项可以解决盲区，但不能让主链依赖变成：

- 装很多插件才能跑；
- 换一个仓库作者节奏就失效；
- 某个小众插件停更就卡死主流程。

### 原则 5：机制契合度高于热度指标

`stars / 活跃度 / 可见度 / 安装成熟度` 是重要筛选器，但**不高于机制契合度本身**。

也就是说：

- 高 stars 不能替代阶段职责契合；
- 主流程度不能替代控制力；
- 热度用于缩小候选，不用于推翻已验证的机制设计。

---

## 四、最终主干架构（V3）

### 4.1 四层模型

```text
┌──────────────────────────────────────────────────────────────┐
│  1. 编排层 Orchestration                                     │
│     stage-harness                                             │
│     状态机 · 决策包 · 阶段门禁 · 议会调度                     │
│     底座：Claude Code hooks / subagents / agent teams         │
├──────────────────────────────────────────────────────────────┤
│  2. 方法层 Methodology                                        │
│     Superpowers                                                │
│     负责澄清、设计收敛、TDD 方法、review 方法、执行纪律        │
├──────────────────────────────────────────────────────────────┤
│  3. 交付主干层 Delivery Backbone                              │
│     Flow-Next（gmickel-claude-marketplace 的 .flow/flowctl 子集） │
│     spec/interview/plan/work/re-anchor/review/evidence        │
│     你的 PRD / SDD / TASKS 作为权威产物格式                    │
├──────────────────────────────────────────────────────────────┤
│  4. 治理与学习层 Govern & Learn                               │
│     ECC(selective install) + native memory + memsearch(opt)   │
│     verify · audit · safety gate · learning governance        │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 状态机

```text
IDEA -> CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
                                         ^        |
                                         └────────┘
```

可选前置：

```text
DISCOVER -> CLARIFY
```

适用场景：

- 目标太大
- 范围尚未稳定
- 需要先拆 feature / epic / spec

---

## 五、组件分级与最终取舍

### 5.1 A 类：主链硬依赖（其中 A1 / A2 / A4 为确定性已选依赖，A3 为目标态优先主干）

#### A1. Claude Code 原生能力

**定位：** 运行时底座。  
**使用范围：**

- hooks：硬门禁
- subagents：轻角色分工
- agent teams：关键出口议会（条件启用）
- marketplace：分发与版本管理
- rules / skills：知识与流程注入

**为什么必须作为底座：**

- 这是最稳的能力层；
- 不额外引入二次编排平台；
- 后续升级与团队推广成本最低。

#### A2. Superpowers

**定位：** 前半程方法学主力。  
**主负责阶段：**

- CLARIFY
- 部分 SPEC 前置澄清
- EXECUTE 过程中的 TDD / review 方法约束

**保留原因：**

- 对“先澄清、再规格、再计划、再执行”的开发方法支持成熟；
- 在需求模糊阶段明显强于纯执行插件；
- 更适合作为“工程工作方式”，而不是某个单点命令。

#### A3. Flow-Next

**定位：** PLAN / EXECUTE 主骨架。  
**主负责阶段：**

- SPEC 后承接
- PLAN
- EXECUTE
- VERIFY 前的 evidence / review / re-anchor

**在 V3 中的确切含义：**

- 这里的 **Flow-Next**，特指 `gmickel-claude-marketplace` 中与 `.flow/*` artifact、`flowctl`、epic/spec/task 图谱相关的 **plan-first 交付子集能力**；
- 不等于选择 `gmickel-claude-marketplace` 的全部功能；
- 本质上，它代表的是一种 **Flow 风格统一交付主干**，当前优先采用该仓库中的这部分承载。

**纳入主链的原因：**

- 它比 `deep-plan + deep-implement` 更适合做统一主干；
- 它天然强调 plan-first；
- 它带 task tracking、dependency graph、re-anchoring、cross-model review；
- 更接近“PLAN 是控制中心”的目标形态。

**选择地位：**

- 它是 V3 的**目标态优先主干**；
- 机制上，后半程统一主干已明确选择为 Flow 风格；
- 组件上，当前优先采用 `gmickel-claude-marketplace` 中的 `.flow/flowctl` 子集能力作为承载。

#### A4. ECC（只保留精选子集）

**定位：** 治理与质量门禁层。  
**主负责阶段：**

- VERIFY
- DONE
- 学习候选治理

**保留原因：**

- 体量大、生态成熟、治理能力强；
- 但必须 selective install，只保留治理、质量、安全、学习相关内容；
- 不让 ECC 反向吞掉主流程。

**精选子集边界：**

- **承担：** `audit / verify / safety gate / learning candidate governance / session & governance substrate`
- **不承担：** 主规划器、主执行器、主 reviewer workflow、核心 artifact 定义器

---

### 5.2 B 类：增强候选项（按需保留，不预设为当前主链组成）

#### B1. adversarial-spec

**定位：** SPEC / PLAN 关口增强器。  
**作用：**

- 做多模型对抗式规格审查；
- 在进入 PLAN 前，补强规格盲区暴露能力；
- 适合作为轻议会或计划议会的“外部挑战器”。

**建议：**

- 不替代主链；
- 作为 SPEC / PLAN 的增强审查步骤；
- 在高风险 feature、关键架构决策、复杂售前需求中启用。
- 选择地位上，把它视为**优先保留的增强候选项**，而不是默认启用的常驻主链组件。

#### B2. memsearch

**定位：** 学习层增强记忆。  
**作用：**

- 把会话、决策、经验沉淀为 markdown-first memory；
- 跨会话语义召回；
- 适合后续做“经验候选池”与“历史决策检索”。

**建议：**

- 先用 native memory；
- 真正需要跨会话语义检索时再接 memsearch；
- 不在 MVP-1 阶段强依赖。
- 选择地位上，把它视为**学习层增强位**，不是当前必须绑定的长期基础设施。

---

### 5.3 C 类：仅参考思路，不再作为主依赖

#### C1. ShipSpec

**处理结论：** 不再作为主链硬依赖。  
**原因：**

- 规格权威这件事，应该沉淀成你自己的 `PRD.md / SDD.md / TASKS.`* 标准格式；
- 不值得把 SPEC 阶段绑定到一个体量偏小的单仓库；
- 其价值更多在“规格组织方式”与提示词思路，而不是运行时依赖。
- 选择地位上，ShipSpec 保留为 **SPEC 阶段的重要参考标杆**，但不再视为长期默认规格引擎。

#### C2. deep-plan / deep-implement

**处理结论：** 不再作为主链硬依赖。  
**原因：**

- PLAN / EXECUTE 分开绑两个较小项目，后续维护和桥接成本高；
- Flow-Next 更适合作为统一交付主干；
- 它们更适合作为参考素材，吸收其 artifact 设计与流程思想。

#### C3. Ring

**处理结论：** 不再作为主运行时。  
**原因：**

- Ring 的 reviewer 分工思路很有价值；
- 但 V3 更建议把“分层议会”实现到 Claude Code agent teams / subagents 上；
- 也就是保留议会思想，不绑定 Ring 运行时。

#### C4. aio-reflect

**处理结论：** 不再作为主链依赖。  
**原因：**

- 学习层建议优先依赖原生 memory + markdown 产物；
- 需要语义检索时再引入 memsearch；
- 不再叠加更小众的学习插件。

---

## 六、职责与控制权矩阵（V3）


| 阶段      | 主负责组件                       | 权威产物                                                              | 重点控制对象              | 放行方式                   |
| ------- | --------------------------- | ----------------------------------------------------------------- | ------------------- | ---------------------- |
| CLARIFY | Superpowers                 | `clarification-notes.md`、`decision-bundle.json`                   | 边界、假设、未决项           | Decision Bundle + gate |
| SPEC    | stage-harness + 自定义 spec 模板 | `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md`                         | 规格完整性、一致性、可落地性      | 轻议会                    |
| PLAN    | Flow-Next + stage-harness   | `bridge-spec.md`、`.flow/`*、`execution-plan.md`、`test-strategy.md` | 覆盖、切分、依赖、验证、风险      | 计划议会                   |
| EXECUTE | Flow-Next                   | 代码、测试、evidence、task/section 记录                                    | section 边界、TDD、漂移控制 | section 内循环            |
| VERIFY  | agent teams + ECC 子集        | `review-report.md`、`test-report.md`、`verification.json`           | 正式工程验收、质量门禁         | 验收议会                   |
| FIX     | Flow-Next + VERIFY 重跑       | `fix-log.md`、更新后的 `verification.json`                             | 问题闭环、复验             | FIX -> VERIFY          |
| DONE    | 发布议会 + ECC + 学习层            | `release-notes.md`、`delivery-summary.md`、`learning-candidates.md` | 发布准备度、交付包、安全、学习治理   | 发布议会                   |


---

## 七、四类议会模板（V3 保留，但实现方式升级）

V2 的分层议会思想继续保留，但实现方式改为：

- **议会调度者：** `stage-harness`
- **议会执行底座：** Claude Code `agent teams` / `subagents`
- **议会模板：** 你自己的输入、输出、裁决语义
- **外部挑战器：** `adversarial-spec`（按需）

也就是说：

> **V3 保留议会机制，但不再把议会绑定到某个单独社区插件。**

### 7.1 A 类：轻议会（SPEC）

**目标：** 判断规格是否足够稳定，可进入 PLAN。  
**推荐人数：** 3~5  
**关注重点：**

- 漏项
- 冲突
- 隐含假设
- 规格与任务的一致性
- 是否足够承接为计划

**输出：**

- `spec-council-report.md`
- `spec-council-verdict.json`

### 7.2 B 类：计划议会（PLAN）

**目标：** 判断计划是否具备执行控制力。  
**推荐人数：** 5~7  
**关注重点：**

- 需求覆盖
- section / task 切分
- 依赖顺序
- 测试前移
- 风险与回滚安排
- 冷启动执行条件

**输出：**

- `plan-council-report.md`
- `plan-council-verdict.json`

### 7.3 C 类：验收议会（VERIFY）

**目标：** 判断实现结果是否正式过关。  
**推荐人数：** 标准 5~7，必要时扩到 7  
**关注重点：**

- 代码质量
- 业务逻辑正确性
- 测试质量
- 安全
- nil/null safety
- ripple effect
- dead code / reachability

**输出：**

- `review-report.md`
- `test-report.md`
- `verification.json`

### 7.4 D 类：发布议会（DONE）

**目标：** 判断是否具备发布、交付与治理条件。  
**推荐人数：** 3~4  
**关注重点：**

- 交付包完整性
- 最终安全签署
- 文档与 release notes
- 学习候选是否妥善提名而非直接晋升

**输出：**

- `release-council-report.md`
- `release-council-verdict.json`

---

## 八、PLAN 作为控制中心（V3 保留并强化）

### 8.1 核心结论不变

V3 继续明确：

> **PLAN 不是普通中间文档，而是后半程的控制中心。**

后半程仍然是：

```text
PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
```

### 8.2 与 V2 的差异

V2 的 PLAN 控制中心，主要绑定在：

- `bridge-spec.md`
- `deep-plan`
- `sections/*`

V3 仍然保留这个思想，但把底层承载调整为：

- `bridge-spec.md`
- 你自己的 `execution-plan.md`
- 你自己的 `test-strategy.md`
- Flow-Next 的 task graph / evidence / re-anchor / review artifacts

也就是说：

- **PLAN 的控制力保留**
- **artifact 的具体格式允许适当换皮**
- **控制目标不变：覆盖、切分、依赖、验证、风险**

### 8.3 PLAN 的放行条件（V3）

进入 EXECUTE 前至少要满足：

- `PRD.md / SDD.md / TASKS.`* 已冻结到当前版本；
- `bridge-spec.md` 已形成；
- execution plan 已形成；
- test strategy 已形成；
- Flow-Next 中的 epic / task / blocker 已可运行；
- 计划议会 verdict 不是阻断；
- 条件项已显式写入状态文件；
- 关键未决项未被偷偷带入执行阶段。

### 8.4 EXECUTE 必须持续反向校验 PLAN

V3 延续 V2 的硬规则：

- 发现 section 切分失效，必须回流 PLAN；
- 发现依赖不成立，必须回流 PLAN；
- 发现测试靶子不足，必须补计划而不是临场补脑；
- 不允许“计划之外的临场扩写”静默混入。

---

## 九、Decision Bundle 与阶段门禁（V3）

### 9.1 Decision Bundle 的职责

Decision Bundle 继续保留，并强化为：

- 收束必须由人拍板的问题；
- 让阶段门禁具备阻断能力；
- 避免 AI 在关键分歧点上自行替人拍板。

### 9.2 推荐触发点

- `CLARIFY -> SPEC`
- `SPEC -> PLAN`
- `PLAN -> EXECUTE`（V3 比 V2 更强调）
- `VERIFY -> DONE`

### 9.3 推荐结构

```json
{
  "stage": "PLAN",
  "decisionBundle": [
    {
      "id": "D-PLAN-01",
      "question": "当前 feature 是否允许先做单租户闭环，再在第二阶段补多租户？",
      "options": ["允许", "不允许"],
      "default": "允许",
      "impact": "影响 section 切分、测试范围、发布条件",
      "evidence": "plan-council-report.md 第 2 节"
    }
  ]
}
```

---

## 十、Hooks、Subagents、Agent Teams 的使用边界（V3）

### 10.1 hooks：只做硬规则

hooks 只做必须“零例外”的事情：

- 阶段门禁
- 阻断危险写操作
- 执行出口校验
- 状态注入
- 自动记录关键状态

### 10.2 subagents：默认角色分工

subagents 负责：

- 规格补漏
- task 切分检查
- 单文件 / 单模块 review
- 测试策略补充
- 风险点挖掘

原则：

- 默认先用 subagent
- 因为更轻、更省 token、更容易收束

### 10.3 agent teams：只在关键出口开

agent teams 用在：

- 轻议会
- 计划议会
- 验收议会
- 发布议会

**定位补充：**

- agent teams 属于**条件启用的高级协作能力**；
- 它不是日常默认底座，而是关键关口的议会执行方式；
- 如果任务规模小、争议少、共享任务列表需求弱，应优先退回 subagents。

原则：

- 平时不用它替代普通工作流
- 只在“需要讨论、互相挑战、共享任务列表”的节点使用

---

## 十一、权威产物格式（V3 建议）

### 11.1 SPEC 阶段

保留你自己的权威格式：

- `PRD.md`
- `SDD.md`
- `TASKS.json`
- `TASKS.md`

这四份文件，不再依赖 ShipSpec 的存在与否。
ShipSpec 可以继续作为规格组织方式和提示词设计的**参考标杆**，但不再构成长期规格权威本身。

### 11.2 PLAN 阶段

建议固定为：

- `bridge-spec.md`
- `execution-plan.md`
- `test-strategy.md`
- `risk-register.md`
- `rollback-notes.md`
- Flow-Next `.flow/*`（即 `gmickel-claude-marketplace` 中 `.flow/flowctl` 对应的交付 artifact 子集）
- `plan-council-report.md`
- `plan-council-verdict.json`

### 11.3 VERIFY / DONE 阶段

建议固定为：

- `review-report.md`
- `test-report.md`
- `verification.json`
- `release-notes.md`
- `delivery-summary.md`
- `learning-candidates.md`

---

## 十二、MVP 路线（V3 重排）

### MVP-1：稳底座 + 前半链打通

**目标：** 打通 `CLARIFY -> SPEC -> PLAN`，并建立最稳的控制骨架。

关键任务：

1. 创建 `stage-harness/` 脚手架；
2. 接入 Claude Code 原生 hooks / subagents；
3. 建立状态文件与阶段门禁；
4. 接入 Superpowers 的 brainstorming / plan discipline；
5. 固化 `PRD / SDD / TASKS` 模板；
6. 生成 `bridge-spec.md`；
7. 接入 Flow-Next；
8. 实现轻议会与计划议会；
9. 让 `PLAN -> EXECUTE` 真正具备强门禁。

### MVP-2：执行与验收闭环

**目标：** 打通 `EXECUTE -> VERIFY -> FIX`。

关键任务：

1. 用 Flow-Next 驱动 task / section 执行；
2. 建立漂移回流规则；
3. 用 subagents 做实现级 review；
4. 用 agent teams 实现验收议会；
5. 形成 FIX -> VERIFY 循环与轮次限制。

### MVP-3：治理、发布、学习增强

**目标：** 打通 `DONE` 与持续学习。

关键任务：

1. 接入 ECC 精选子集；
2. 实现发布议会；
3. 形成 `release / delivery / learning` 三类 artifacts；
4. 引入 native memory；
5. 按需接入 memsearch；
6. 对高风险规格接入 adversarial-spec。

### MVP-4：团队化分发

**目标：** 形成团队可复用能力包。

关键任务：

1. 把 `stage-harness` 做成可安装插件或仓库模板；
2. 把你的 spec / plan / gate / council 模板沉淀为团队标准；
3. 用 marketplace 做内部版本发布；
4. 建立升级与回滚策略。

---

## 十三、对原 V2 各组件的最终处置清单


| 组件               | V2 角色         | V3 处理结论 | 原因                             |
| ---------------- | ------------- | ------- | ------------------------------ |
| stage-harness    | 编排外壳          | 保留并加强   | 这是你的真正差异化能力                    |
| Superpowers      | 澄清与方法层        | 保留      | 主流、成熟、方法学价值高                   |
| ShipSpec         | 规格权威          | 降级为参考   | 规格应沉淀为你自己的权威模板                 |
| deep-plan        | 计划主干          | 降级为参考   | Flow-Next 更适合作为统一计划骨架          |
| deep-implement   | 执行主干          | 降级为参考   | 与 deep-plan 双依赖桥接成本高           |
| Ring             | 验收 / reviewer | 降级为参考   | 保留 reviewer 思想，不绑运行时           |
| ECC              | 治理与学习         | 保留精选子集  | 体量大、能力强，但不能全装                  |
| aio-reflect      | 学习提名          | 移除主依赖   | 由 native memory + memsearch 替代 |
| adversarial-spec | 原未明确主链        | 新增增强项   | 适合规格关口补盲                       |
| memsearch        | 原未明确主链        | 新增增强项   | 适合跨会话学习检索                      |


---

## 十四、关键风险与缓解（V3）

### 14.1 Flow-Next 替换双组件后，artifact 语义发生变化

**风险：** 你原先围绕 `deep-plan / deep-implement` 设计的部分桥接逻辑需要重写。  
**缓解：**

- 保留你自己的权威产物格式；
- 不绑定 Flow-Next 内部命名；
- 只把它当计划 / 执行 / evidence 引擎。

### 14.2 agent teams 用太多，成本过高

**风险：** token 成本和调度成本失控。  
**缓解：**

- 默认 subagents
- 只在 4 个关键出口开议会
- 小 feature 可降级为 subagent review

### 14.3 ECC 装得太多，主链被反向绑架

**风险：** 流程变重、难维护、难解释。  
**缓解：**

- 只装治理 / 安全 / verify / learn 子集
- 不把 ECC 当流程主干
- 不让 ECC 决定核心产物格式

### 14.4 memory 层过早引入，导致复杂度上升

**风险：** MVP 初期就引入 embedding / 检索 / watcher，调试成本高。  
**缓解：**

- 先 markdown + native memory
- 后续需要跨会话语义召回时再接 memsearch

---

## 十五、最终版一句话总结

V3 的最终形态不是“把更多插件串起来”，而是：

> **用 Claude Code 原生能力做底座，用 Superpowers 管前半程的方法学，用 Flow-Next 管后半程的 plan-first 交付主干，用 ECC 做治理门禁，再用 adversarial-spec / memsearch 做按需增强。**

---

## 十六、最终推荐实施基线

如果后续只保留一份主版本方案文档，建议以 V3 为统一实施基线：

- 机制上，保留 V2 的：
  - PLAN 控制中心
  - 四类分层议会
  - Decision Bundle
  - 阶段门禁
  - 可审查 / 可阻断 / 可回退
- 选型上，改为 V3 的：
  - **Claude Code 原生能力**
  - **Superpowers**
  - **Flow-Next（`gmickel-claude-marketplace` 的 `.flow/flowctl` 子集能力）**
  - **ECC 精选子集**
  - **adversarial-spec / memsearch（按需）**

---

## 十七、调研依据摘要（用于本次 V3 收敛）

本次 V3 收敛，主要依据如下：

- Claude Code 官方文档明确支持并区分 `hooks`、`subagents`、`agent teams`、`plugin marketplaces`，适合作为 V3 的原生底座；其中 hooks 适合做确定性硬门禁，subagents 更轻，agent teams 适合需要协作和互相挑战的复杂工作。 citeturn577507view0turn577507view1turn577507view2turn577507view3
- Superpowers 当前为高星、活跃项目，并已进入 Claude Code 官方 marketplace；其 README 直接强调从澄清、设计、计划到 subagent-driven development 的完整工程方法链。 citeturn398182search1turn271410view0
- ECC 当前仍是高星高活跃项目，且最近版本明确支持 selective install，因此更适合作为“治理层精选子集”，而不是整仓全装。 citeturn386119search1turn624831search2turn624831search6
- Flow-Next 当前约 552 stars，定位非常清晰：plan-first orchestration、dependency graph、re-anchoring、cross-model reviews，更适合承接你对 PLAN 控制中心的要求。 citeturn823845search0turn512768search6turn271410view1
- adversarial-spec 和 memsearch 都更适合作为增强项而非主链：前者偏规格关口补盲，后者偏跨会话记忆与检索。 citeturn611861search0turn611861search4turn512768search15

