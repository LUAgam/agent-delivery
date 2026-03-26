# Stage-Harness 复用性与自研边界评估

> 基于 `coding/DEVELOPMENT-PLAN.md`、`coding/final-plan-v2.md`、`coding/final-plan-v2-supplements.md` 以及仓库内现有插件/代码实现，对 `stage-harness` 的后续落地做一次“复用 vs 自研”判断。

---

## 一、结论摘要

### 1.1 一句话判断

`stage-harness` **不是**“参考现有代码简单拼接后做少量二次开发”。

更准确的判断是：

> **底层阶段能力大部分可复用，但编排层、桥接层、门禁层和裁决层需要中等量以上的新开发。**

也可以换一种更工程化的表述：

- **纵向能力复用度：高**
- **横向编排自研量：中高**
- **整体形态：集成式开发，不是轻量拼装**

### 1.2 为什么会形成这个判断

仓库内已经存在多条成熟的“纵向能力链”：

- `deep-project`：大需求拆解
- `deep-plan`：单 spec -> research/interview/review/TDD/sections
- `deep-implement`：按 section 做 TDD、code review、原子提交
- `shipspec-claude-code-plugin`：生成 `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md`
- `ring`：提供 `/ring:codereview` 等并行审查能力

但文档中定义的 `stage-harness` 并不是上述任一组件的别名，而是一个新的**编排外壳**，负责：

- 阶段状态机
- 阶段门禁
- Decision Bundle
- 组件裁剪与控制权切换
- ShipSpec -> deep-plan 格式桥接
- 分层议会调度与 verdict 汇总
- VERIFY / FIX / DONE 的治理闭环

这些能力在仓库里**没有单独的现成实现可直接拿来用**。

但要注意，这个判断只适用于“**stage-aware 的统一编排器**”，**不等于所有底座都要从零开始**。仓库里仍然存在一些可复用的通用基础设施，尤其是 ECC 的：

- session/state 存储 schema
- session adapter contract
- state-store / recording shim 一类持久化与观测底座
- governance / audit 相关数据面

因此更准确的边界应该是：

> **没有现成的阶段编排器，但存在可以借用的 persistence / inspection substrate。**

---

## 二、核心判断：哪里可以直接复用，哪里不能

### 2.1 可以直接复用的，不是“整体 harness”，而是“阶段能力内核”

从当前仓库代码看，最成熟的是各阶段的专业插件，而不是一个总控插件。

例如：

- `deep-project` 已经完成从模糊需求到拆分 spec 的工作流
- `deep-plan` 已经完成从单个 spec 到 plan/tdd/sections 的工作流
- `deep-implement` 已经完成按 section 实施、审查、提交的工作流
- `ShipSpec` 已经完成规格权威生成
- `Ring` 已经完成并行 reviewer 调度

因此，后续实现 `stage-harness` 时，**不应重复建设这些纵向能力**，而应把它们当成“已存在的阶段执行器”。

### 2.2 不能直接复用的，恰恰是方案最关键的那层

`coding/DEVELOPMENT-PLAN.md` 把 `stage-harness` 定义为：

- 阶段化流水线的编排层
- 状态与恢复中心
- 阶段门禁执行者
- 审查与决策的统一分发器

仓库内目前没有 `stage-harness/` 实现目录，也没有发现任何现有插件已经把这些能力打包成可直接安装的整体方案。

所以不能把这项工作理解成：

> “把几个插件都装上，再写少量 glue code 就结束。”

更接近现实的理解是：

> “复用多个成熟子系统，但需要新建一个 orchestrator，把职责、输入输出、事件、状态、裁决语义统一起来。”

---

## 三、可直接复用清单

本节只回答一个问题：**哪些东西不应该重写，而应该直接接入或裁剪复用。**

### 3.1 `deep-project`

**现有能力**

- 大目标拆解为多个规划单元
- 访谈、切分、依赖分析、目录生成
- 适合作为 `DISCOVER` 或超大需求前置拆分层

**为什么可复用**

- README 已明确其定位是 Deep Trilogy 的第一步
- 与文档中的“可选前置 DISCOVER”高度契合

**建议复用方式**

- 作为可选前置，而不是强制主链
- 仅在需求规模过大或边界模糊时启用

### 3.2 `deep-plan`

**现有能力**

- 输入单个 spec markdown
- 输出 research/interview/review/TDD/sections
- 已有恢复能力与规划产物体系

**为什么可复用**

- 文档中 `PLAN` 阶段本来就明确指定 `bridge + deep-plan`
- 这部分不是候选方案，而是主方案的一部分

**建议复用方式**

- 直接作为 `PLAN` 阶段执行器
- harness 负责准备输入、控制出口和消费结果

### 3.3 `deep-implement`

**现有能力**

- 按 section 顺序实施
- TDD
- 内置 code review
- 原子提交
- 进度恢复

**为什么可复用**

- 文档中 `EXECUTE` 阶段已经明确指定 `deep-implement`
- 仓库代码和 README 都表明它已是成熟工作流，不需要重复造轮子

**建议复用方式**

- 直接作为 `EXECUTE` 执行器
- harness 只负责决定“何时进入执行、执行哪个 section 集合、执行后如何进入 VERIFY”

### 3.4 `ShipSpec`

**现有能力**

- `/feature-planning`
- 产出 `PRD.md`、`SDD.md`、`TASKS.json`、`TASKS.md`
- 已有 `prd-gatherer`、`design-architect`、`task-planner` 等 agents

**为什么可复用**

- `SPEC` 阶段生成规格权威的能力已经很完整
- 文档多处明确指定 `ShipSpec` 是规格主负责组件

**建议复用方式**

- 复用其规划链路与产物格式
- 禁用或隔离其 Ralph Loop 的 `Stop` 钩子
- 不复用其自动执行主循环

### 3.5 `Ring`

**现有能力**

- `/ring:codereview`
- 并行 reviewer 体系
- default 插件的 review 能力较完整

**为什么可复用**

- 文档中 `VERIFY` 阶段本来就指定 Ring 做验收议会底层能力
- 多 reviewer 审查体系已现成，不值得自造

**建议复用方式**

- 只启用 `default` 的 review 相关能力
- 不启用与 planning / dev-cycle 重叠的整套团队插件

### 3.6 `ECC` 的通用状态与观测底座

**现有能力**

- 通用 state-store schema
- session adapter contract
- session recording shim
- governance / decision / session 观测数据结构

**为什么可复用**

- 虽然它不是 `stage-harness` 的现成 orchestrator，但已经提供了较成熟的持久化和记录底座
- 对 `state.json`、session snapshot、governance events、decision records 这类对象建模有直接参考价值

**建议复用方式**

- 复用其 schema、持久化思路和 session 记录抽象
- 不直接照搬 ECC 的全量治理体系
- 将其作为 `stage-harness` 的底层 substrate，而不是顶层状态机替代品

---

## 四、必须新开发清单

本节是整个评估最关键的部分。真正的工程量主要在这里。

### 4.1 `stage-harness` 插件骨架本身

需要新建：

- `.claude-plugin/plugin.json`
- `commands/`
- `agents/`
- `skills/`
- `hooks/`
- `scripts/`
- `templates/`

原因：

- 仓库里目前没有现成 `stage-harness/`
- 这不是“修改已有插件”，而是新增一个总控插件

### 4.2 状态机与状态文件体系

需要新建：

- `state.json` 模板
- `global-config.json` 或等价配置
- 阶段历史记录
- rollback / retry / escalation 字段
- 多 feature 隔离结构

原因：

- 现有插件都维护自己的局部状态
- ECC 等仓库虽然有状态存储底座，但没有 `stage-harness` 所需的**阶段语义、阶段流转、阶段门禁**模型
- 文档要求的是**跨插件统一状态机**

更准确地说：

- **底座可复用**：schema、session snapshot、decision/governance 记录方式
- **阶段语义需自建**：`currentStage`、阶段历史、rollback 规则、feature 隔离、放行条件

### 4.3 桥接脚本：`ShipSpec -> deep-plan`

需要新建：

- `scripts/bridge-shipspec-to-deepplan.sh`
- 相关转换测试与完整性校验

原因：

- `ShipSpec` 的输出是 `PRD.md / SDD.md / TASKS.json`
- `deep-plan` 期待的是单个可消费 spec markdown
- 这之间存在明确格式断层

这块不是简单 markdown 拼接，而是必须保证：

- 需求摘要不丢
- 架构决策不丢
- 任务依赖不丢
- 验收标准不丢

### 4.4 决策包与阶段门禁

需要新建：

- `decision-bundle.sh`
- `decision-bundle.json` 模板
- `stage-gate-check.sh`
- `stage-reminder.sh`

原因：

- 文档中 Decision Bundle 是贯穿多个阶段出口的统一机制
- ECC 有 decision / governance 的通用记录模型可借鉴，但没有直接等价于 `stage-harness` 的阶段决策包抽象

更准确地说：

- **记录与审计底座可参考 ECC**
- **阶段决策包语义、阻断规则和用户交互协议仍需自建**

### 4.5 分层议会调度与 verdict 汇总

需要新建：

- `spec-reviewer.md`
- `plan-reviewer.md`
- `release-reviewer.md`
- `council-dispatch` 技能或脚本
- verdict 汇总逻辑

原因：

- `Ring` 只覆盖 VERIFY 最接近
- SPEC / PLAN / DONE 三种议会模板仍需 harness 自己定义
- 即使底层 reviewer 可复用，上层输入输出与裁决语义仍需自建

### 4.6 组件裁剪与 Hook 协调

需要新建或明确实现：

- ShipSpec 的禁用钩子安装策略
- Ring 的 default-only 安装策略
- Superpowers 的截获策略或替代策略
- 多插件 Hook 并存时的冲突规避方案

原因：

- 现有插件都是按自己的控制权模型设计的
- `stage-harness` 要做的是“收编并裁剪”，不是“原封不动叠加”

### 4.7 VERIFY / FIX / DONE 的编排闭环

需要新建：

- `verification.json` 统一语义
- FIX 轮次计数与升级逻辑
- PASS / FAIL 规则
- DONE 交付物生成与治理流程

原因：

- 现有插件负责各自局部流程
- ECC / Ring / deep-implement 分别覆盖局部治理、局部审查或局部执行，但没有哪个插件天然承担“全局质量门 + 修复回路 + 发布出口”的角色

更准确地说：

- **局部审查与治理能力可复用**
- **全局 PASS/FAIL 语义、FIX 升级规则、DONE 出口契约需自建**

---

## 五、基线与裁边建议

这一节不再简单区分“可延后”，而是区分：

- **当前基线**：主方案里已吸收、应进入正式范围
- **可在 MVP-1 裁掉**：不是第一阶段 blocker
- **后续增强**：适合基础链路稳定后再接入

特别说明：

- **“属于当前基线”** 不等于 **“必须在 MVP-1 交付”**
- 当前基线回答的是“总方案是否应包含它”
- MVP 回答的是“应该在哪一阶段落地它”

### 5.1 当前基线

以下内容已经进入当前主方案基线，不应被误解为“纯可选增强”：

- `session-handoff.template.md`
- `feature-list.json`
- `smoke-check.sh`
- `evaluator-rubric.md`
- `deep-implement` 驱动的 `EXECUTE`
- Ring 驱动的 `VERIFY`
- ECC 驱动的 DONE 治理层
- `aio-reflect` 驱动的学习候选提名流程

说明：

- 这些能力在 `DEVELOPMENT-PLAN.md` 中已进入 MVP-2 / MVP-3，而不是游离在主方案之外
- 因此如果做总体排期，应该把它们视作**当前方案基线的一部分**

### 5.2 可在 MVP-1 裁掉

- Session Handoff
- smoke-check
- 漂移检测与回流 PLAN
- evaluator rubric

这些都很重要，但从阶段打通角度看，不是 `MVP-1` 的前置门槛。

也就是说：

- 它们属于**当前总方案基线**
- 但可以在**第一阶段打通主链时暂时不做**

### 5.3 后续增强

- ECC `security-reviewer`
- 双轨学习机制
- Eval Harness 数据面
- riskLevel 动态调整 reviewer 数
- token 预算管理
- 低风险路径简化

这些更适合作为“主链稳定后再加的生产强化项”。

---

## 六、工作量评估

### 6.1 按模块看


| 模块                 | 复用情况                   | 新开发量 | 复杂度 |
| ------------------ | ---------------------- | ---- | --- |
| CLARIFY            | 部分复用 Superpowers 或内联替代 | 中    | 中   |
| SPEC               | 复用 ShipSpec 主体         | 中    | 中   |
| PLAN               | 复用 deep-plan 主体        | 中    | 中   |
| EXECUTE            | 复用 deep-implement 主体   | 低    | 低   |
| VERIFY             | 复用 Ring reviewer 主体    | 中    | 中   |
| DONE/GOVERN        | 部分复用 ECC / aio-reflect | 中    | 中   |
| 编排层状态机             | 无现成实现                  | 高    | 高   |
| 桥接层                | 无现成实现                  | 中高   | 高   |
| 门禁/Decision Bundle | 无现成实现                  | 中    | 中   |
| 议会汇总层              | 部分可借底层 reviewer        | 中高   | 高   |


### 6.2 按整体判断

如果把项目拆成两部分：

#### A. 阶段执行器

- 现有复用度高
- 开发量相对可控

#### B. 阶段编排器

- 现有复用度低
- 是主要新增工作

因此整体结论是：

> **这不是“大量自研底层能力”的项目，但也绝不是“把文档和代码拼起来就行”的项目。**

更接近：

> **在成熟子系统之上，新建一个中等复杂度的 orchestration product。**

---

## 七、排期映射矩阵

下面这个矩阵可直接作为“评估报告 -> 排期输入”的桥梁。

| 能力项 | 是否 blocker | 目标 MVP | 前置依赖 | 验收物 |
|------|-------------|---------|---------|-------|
| `stage-harness` 插件骨架 | 是 | MVP-1 | 无 | 插件可被识别加载 |
| 状态机与 `state.json` | 是 | MVP-1 | 插件骨架 | 状态可读写，阶段可推进 |
| CLARIFY 接入 | 否 | MVP-1 | 状态机 | `clarification-notes.md` |
| ShipSpec 接入 | 是 | MVP-1 | 状态机 | `PRD.md` / `SDD.md` / `TASKS.json` |
| ShipSpec 钩子隔离 | 是 | MVP-1 | ShipSpec 接入 | Ralph Loop 不触发 |
| `bridge-shipspec-to-deepplan.sh` | 是 | MVP-1 | ShipSpec 接入 | `bridge-spec.md` |
| deep-plan 接入 | 是 | MVP-1 | bridge | `claude-plan.md` / `sections/*` |
| SPEC 轻议会 | 否 | MVP-1 | ShipSpec 接入 | `spec-council-verdict.json` |
| PLAN 计划议会 | 否 | MVP-1 | deep-plan 接入 | `plan-council-verdict.json` |
| `stage-gate-check.sh` | 是 | MVP-1 | 状态机 | 产物不合格时可阻断 |
| deep-implement 接入 | 是 | MVP-2 | deep-plan 接入 | section 级实现与提交 |
| Session Handoff | 否 | MVP-2 | 状态机 | handoff 文档与恢复流程 |
| `feature-list.json` | 否 | MVP-2 | deep-plan 接入 | feature 子任务与状态清单 |
| `smoke-check.sh` | 否 | MVP-2 | 状态机 | session 开始可执行冒烟检查 |
| `evaluator-rubric.md` | 否 | MVP-2 | deep-plan 接入 | evaluator 评判标准文档 |
| 漂移检测与回流 | 否 | MVP-2 | PLAN / EXECUTE 打通 | 偏离 plan 时能触发回流 |
| Ring 验收议会 | 是 | MVP-2 | EXECUTE 打通 | `verification.json` |
| FIX -> VERIFY 循环 | 是 | MVP-2 | Ring 验收议会 | FAIL 可闭环修复并重验 |
| ECC DONE 治理层 | 否 | MVP-3 | VERIFY 稳定 | DONE 阶段治理记录与交付检查 |
| ECC `security-reviewer` | 否 | MVP-3 | VERIFY 稳定 | 安全报告 |
| `aio-reflect` | 否 | MVP-3 | DONE 流程 | 学习候选清单 |
| 发布议会 | 否 | MVP-3 | VERIFY 稳定 | 发布 verdict |
| Eval Harness 数据面 | 否 | MVP-3 | 多阶段运行 | trace / metrics / outcome 数据 |
| 动态强度控制 | 否 | MVP-3 | 基础链路稳定 | reviewer 数量和成本可调 |

---

## 八、推荐实施口径

为了避免团队低估工作量，建议在后续沟通里使用下面这种表述：

### 7.1 推荐表述

`stage-harness` 后续实现应定义为：

> **基于 ShipSpec、Deep Trilogy、Ring 等现有插件能力，构建一个新的阶段化编排插件。**

而不是：

> **参考现有代码做简单拼接。**

### 7.2 原因

如果对外说“少量二开”，容易低估以下工作：

- 组件控制权冲突
- Hook 契约验证
- 规格到计划的桥接保真
- 阶段门禁与 rollback 语义
- 议会 verdict 汇总与阻断逻辑
- 多插件状态协同

这些工作不一定代码量巨大，但**设计密度高、集成风险高、调试成本高**。

---

## 九、最终结论

### 8.1 最终判断

`stage-harness` 的后续实现：

- **参考现有实现：是，而且应该大量参考**
- **是否只是拼接后少量二开：不是**

最准确的结论是：

> **纵向能力复用为主，横向编排需要中等以上自研。**

### 8.2 给排期和预期管理的建议

如果要做排期，建议把它视为两类工作并行：

1. **能力接入工作**
  - 接 ShipSpec
  - 接 deep-plan
  - 接 deep-implement
  - 接 Ring
2. **编排产品开发工作**
  - 状态机
  - 桥接
  - 门禁
  - 议会
  - 裁决
  - 恢复与回退

其中第二类才是决定项目成败的主工作量。

---

## 十、附：一句话版对外回答

如果后续需要一个非常短的结论，可以直接用这句：

> **这个插件不是简单拼装已有代码，而是要在现有成熟插件能力之上，再做一层新的编排与治理系统；底层能力复用度高，但编排层仍需中等量以上开发。**

