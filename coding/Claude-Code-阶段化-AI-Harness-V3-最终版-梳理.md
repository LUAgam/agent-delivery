# Claude Code 阶段化 AI Harness V3 — 最终版梳理

## 一、文档定位

本文档是对 `Claude-Code-阶段化-AI-Harness-V3-高星稳定优先版.md` 的结构化梳理版本。

它的目的不是替代主版本方案文档，也不是补充实施细节，而是把最终版 V3 的核心判断、选型分层、组件职责和机制边界整理成一份更便于评审、引用和对齐口径的说明文档。

因此，这份文档回答的是：

1. V3 最终版到底在主张什么；
2. 哪些是不可替换的机制；
3. 哪些是当前优先采用的承载组件；
4. 各组件的最终职责边界是什么；
5. 这份文档适合被如何使用。

---

## 二、最终版一句话主张

V3 的最终主张可以概括为：

> 保留 `stage-harness` 作为阶段化编排外壳，以 Claude Code 原生能力为底座，以 Superpowers 负责前半程方法学，以 Flow-Next（即 `gmickel-claude-marketplace` 中 `.flow/*`、`flowctl`、epic/spec/task artifact 对应的 plan-first 交付子集能力）作为后半程统一交付主干，以 ECC 精选子集承担治理层，并按需保留 adversarial-spec / memsearch 作为增强位。

---

## 三、最终版的三个核心判断

### 3.1 真正不可替换的是机制层，不是具体插件

最终版 V3 已经明确区分了两层：

#### 不可替换的机制层

- `stage-harness` 编排外壳
- 阶段化状态机
- PLAN 控制中心
- 分层议会
- Decision Bundle
- 阶段门禁
- 可审查 / 可阻断 / 可回退

#### 当前优先承载组件

- Claude Code 原生能力
- Superpowers
- Flow-Next
- ECC 精选子集
- adversarial-spec / memsearch

这意味着：

- 未来如果某个具体承载组件替换；
- 机制层本身不需要重写；
- V3 的稳定性来自机制层，而不是来自某个单独仓库。

### 3.2 V3 不是否定 V2，而是把 V2 的正确机制绑定到更稳的承载上

V2 最有价值的遗产包括：

- PLAN 是控制中心
- 分层议会
- Decision Bundle
- 阶段门禁
- 强权威产物
- 可回流、可阻断

V3 保留这些机制，但不再强绑定原来的插件组合，而是收敛到更原生、更主流、更低整合脆弱性的承载上。

### 3.3 V3 不是“多插件拼装”，而是“统一主链 + 清晰裁边”

V3 的思路不是把所有高星项目都装进来，而是：

- 底座尽量原生；
- 主链尽量统一；
- 治理层尽量裁边；
- 增强项尽量候选化；
- 参考项不再构成长期强依赖。

---

## 四、最终版的选型分层

为了避免“机制已定”和“组件承载已完全固定”被混淆，V3 采用了明确的选型分层。

### 4.1 确定性已选依赖

这些是最终版中已经明确选择、稳定性最高的部分。

#### A. Claude Code 原生能力

承担：

- hooks
- subagents
- rules / skills / MCP
- marketplace
- agent teams（条件启用）

定位：

> 运行时底座

#### B. Superpowers

承担：

- CLARIFY
- 部分 SPEC 前置澄清
- EXECUTE 过程中的 TDD / review 方法纪律

定位：

> 前半程方法学层

#### C. ECC 精选子集

承担：

- audit
- verify
- safety gate
- learning candidate governance
- session / governance substrate

不承担：

- 主规划器
- 主执行器
- 主 reviewer workflow
- 核心 artifact 定义器

定位：

> 治理与质量门禁层

### 4.2 目标态优先主干

#### Flow-Next

这里的 **Flow-Next** 不是一个独立的新插件名，而是：

> `gmickel-claude-marketplace` 中 `.flow/*`、`flowctl`、epic/spec/task artifact 对应的 plan-first 交付子集能力。

也就是说：

- 选的不是整个 `gmickel-claude-marketplace`；
- 选的是其中的 **Flow 风格交付主干能力**；
- 它承担的是后半程统一交付主干，而不是整个生态的全部功能。

承担：

- PLAN
- EXECUTE
- VERIFY 前的 evidence / review / re-anchor 支撑

定位：

> 后半程统一交付主干

### 4.3 增强候选项

#### A. adversarial-spec

定位：

> SPEC / PLAN 关口增强器

作用：

- 多模型对抗式规格补盲
- 轻议会 / 计划议会的外部挑战器

地位：

> 增强候选项，而非默认主链组件

#### B. memsearch

定位：

> 学习层增强记忆

作用：

- 跨会话语义检索
- 历史决策 / 经验候选召回

地位：

> 学习层增强位，而非当前必须绑定的长期基础设施

### 4.4 降级为参考

这些组件保留参考价值，但不再作为长期主链强依赖。

#### A. ShipSpec

保留价值：

- 规格组织方式
- 提示词思路
- SPEC 阶段参考标杆

不再承担：

- 长期默认规格引擎

#### B. deep-plan / deep-implement

保留价值：

- artifact 设计
- plan-first 思维
- section/TDD/执行方式参考

不再承担：

- 长期主链 PLAN / EXECUTE 骨架

#### C. Ring

保留价值：

- reviewer 分工思想
- 并行审查理念

不再承担：

- 长期主运行时

#### D. aio-reflect

保留价值：

- 学习提名思路

不再承担：

- 主链依赖

---

## 五、最终版四层架构

### 5.1 编排层

#### `stage-harness`

负责：

- 状态机
- Decision Bundle
- 阶段门禁
- 议会调度

底座：

- Claude Code hooks / subagents / agent teams

说明：

> 这是整个体系的总控层，也是最终版真正保留并加强的差异化能力。

### 5.2 方法层

#### Superpowers

负责：

- 澄清
- 设计收敛
- TDD 方法
- review 方法
- 执行纪律

说明：

> 它是方法层，不是总执行器。

### 5.3 交付主干层

#### Flow-Next

负责：

- spec/interview/plan/work/re-anchor/review/evidence
- `.flow/*` artifact 主干
- PLAN / EXECUTE 主线承载

说明：

> 它是统一后半程主干，而不是整个生态的全部功能集合。

### 5.4 治理与学习层

#### ECC(selective) + native memory + memsearch(opt)

负责：

- verify
- audit
- safety gate
- learning governance

说明：

> 治理层不能反向吞掉主流程。

---

## 六、最终版状态机

### 6.1 主状态机

```text
IDEA -> CLARIFY -> SPEC -> PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
                                         ^        |
                                         └────────┘
```

### 6.2 可选前置

```text
DISCOVER -> CLARIFY
```

### 6.3 各阶段含义

- **DISCOVER**：目标过大、范围未稳时先拆
- **CLARIFY**：澄清问题空间
- **SPEC**：形成规格权威
- **PLAN**：形成执行控制包
- **EXECUTE**：按计划推进实现
- **VERIFY**：正式验收
- **FIX**：问题闭环
- **DONE**：发布与治理完成

---

## 七、各阶段最终归属

### 7.1 CLARIFY

主负责：

- Superpowers

权威产物：

- `clarification-notes.md`
- `decision-bundle.json`

出口：

- Decision Bundle + gate

### 7.2 SPEC

主负责：

- `stage-harness + 自定义 spec 模板`

权威产物：

- `PRD.md`
- `SDD.md`
- `TASKS.json`
- `TASKS.md`

说明：

- ShipSpec 可以继续作为参考标杆；
- 但规格权威不再绑定 ShipSpec 本身。

### 7.3 PLAN

主负责：

- Flow-Next + `stage-harness`

权威产物：

- `bridge-spec.md`
- `.flow/*`
- `execution-plan.md`
- `test-strategy.md`

核心：

> PLAN 是后半程控制中心。

### 7.4 EXECUTE

主负责：

- Flow-Next

权威产物：

- 代码
- 测试
- evidence
- task / section 记录

### 7.5 VERIFY

主负责：

- agent teams + ECC 子集

权威产物：

- `review-report.md`
- `test-report.md`
- `verification.json`

### 7.6 FIX

主负责：

- Flow-Next + VERIFY 重跑

权威产物：

- `fix-log.md`
- 更新后的 `verification.json`

### 7.7 DONE

主负责：

- 发布议会 + ECC + 学习层

权威产物：

- `release-notes.md`
- `delivery-summary.md`
- `learning-candidates.md`

---

## 八、最终版保留的关键机制

### 8.1 PLAN 是控制中心

最终版明确保留：

> PLAN 不是中间文档，而是后半程控制中心。

它控制：

- 覆盖
- 切分
- 依赖
- 验证
- 风险

后半程主链：

```text
PLAN -> EXECUTE -> VERIFY -> FIX -> DONE
```

### 8.2 Decision Bundle 保留

作用：

- 收束必须由人拍板的问题
- 防止 AI 在关键分歧点替人拍板
- 为 gate 提供阻断依据

推荐触发点：

- `CLARIFY -> SPEC`
- `SPEC -> PLAN`
- `PLAN -> EXECUTE`
- `VERIFY -> DONE`

### 8.3 分层议会保留

四类议会仍然存在：

- 轻议会（SPEC）
- 计划议会（PLAN）
- 验收议会（VERIFY）
- 发布议会（DONE）

实现升级为：

- 调度者：`stage-harness`
- 执行底座：Claude Code `agent teams / subagents`
- 外部挑战器：`adversarial-spec`（按需）

### 8.4 hooks / subagents / agent teams 边界最终明确

#### hooks

只做硬规则：

- 门禁
- 阻断危险写操作
- 出口校验
- 状态注入
- 自动记录关键状态

#### subagents

默认角色分工：

- 规格补漏
- task 切分检查
- 单模块 review
- 风险挖掘
- 测试策略补充

#### agent teams

不是默认底座，而是：

- 条件启用的高级协作能力
- 只在关键出口开议会
- 小任务优先退回 subagents

---

## 九、最终版文档的阅读主线

如果要用最清晰的方式理解 V3，建议按下面顺序阅读：

1. 先看文档定位  
   - 它是主版本选择方案文档
2. 再看总主张  
   - 保留机制，收敛承载，原生优先，稳定优先
3. 再看选型分层  
   - 确定性已选、目标态优先主干、增强候选、降级为参考
4. 再看四层架构  
   - 编排层、方法层、交付主干层、治理层
5. 再看状态机与阶段职责  
   - 谁负责每一阶段，产物是什么，gate 是什么
6. 最后看风险  
   - Flow artifact 语义变化、agent teams 成本、ECC 过重、memory 过早引入

---

## 十、最终版文档最适合的用途

这份最终版文档最适合用来做：

1. 方案评审
2. 团队对齐口径
3. 后续实现裁边依据
4. 判断哪些组件属于主链、哪些只是参考
5. 避免实现阶段回到“全都装上”的思路

它不适合直接承担：

- 详细开发方案
- 任务拆解清单
- MVP 操作说明
- 目录结构与脚手架规范

---

## 十一、超短摘要

### 最终版超短摘要

- **机制不变**：阶段机、PLAN 控制中心、议会、Decision Bundle、gate
- **底座已定**：Claude Code 原生能力
- **方法层已定**：Superpowers
- **交付主干已定方向**：Flow 风格统一主干，当前承载为 `gmickel-claude-marketplace` 的 `.flow/flowctl` 子集能力
- **治理层已定**：ECC 精选子集
- **增强项保留**：adversarial-spec / memsearch
- **降级为参考**：ShipSpec / deep-plan / deep-implement / Ring / aio-reflect

---

## 十二、结论

这份最终版 V3 文档现在已经形成一个清晰的主版本选择方案：

- 机制层稳定；
- 选型层有分层；
- 组件边界更明确；
- 主链与增强位已经被清楚区分；
- 可以作为后续所有实现、评审与裁边的统一基线。

如果后续还需要更短的版本，建议在本文件基础上再压缩出一份：

> `V3-执行摘要版`

用于放在文档最前面，供快速阅读。
