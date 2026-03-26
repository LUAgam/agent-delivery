# Stage-Harness 迭代计划

> 基于 `DEVELOPMENT-PLAN.md` 的成本与风险分析，输出一份**务实的迭代计划**。

---

## 一、成本与风险总体评估

### 1.1 一句话判断

**方案的设计质量很高，但当前形态的实现成本偏高、集成风险集中在少数关键点。** 核心原因不是方案本身有问题，而是它同时依赖 7 个外部组件、4 类议会、3 种 Hook 事件和 1 个自建桥接层，任何一个集成点出问题都会阻塞整条链路。

### 1.2 成本分析

#### 开发成本

| 成本维度 | 评估 | 说明 |
|---------|------|------|
| **自建代码量** | 中等 | 主要是 shell 脚本（hooks、bridge、verify）、Markdown（skills、agents、commands）、JSON（state、templates）。无需写复杂应用代码 |
| **外部组件集成** | **高** | 7 个组件各有自己的安装方式、依赖（Python/Node/Bun/Go）、Hook 格式和产物约定。每个集成点都需要单独调试 |
| **议会系统** | **高** | 4 类议会 × 各自的 reviewer agents × 裁决汇总逻辑。每个 reviewer 都是一个 subagent 调用，prompt 设计和输出解析都需要迭代 |
| **桥接脚本** | 中等 | 核心难点不是"拼接 Markdown"，而是确保 ShipSpec 产物的关键信息（依赖、验收标准、架构决策）无损传递到 deep-plan 格式 |
| **状态管理** | 低~中等 | JSON 文件读写 + 目录管理，技术门槛不高，但状态一致性（崩溃恢复、并发、回滚）需要仔细处理 |

#### 运行时成本（Token）

| 环节 | 单次预估 Token | 频次 | 说明 |
|------|--------------|------|------|
| CLARIFY（brainstorming） | ~10K | 1 次/feature | Superpowers 对话式，成本可控 |
| SPEC（ShipSpec） | ~30K | 1 次/feature | PRD+SDD+TASKS 全套生成 |
| SPEC 轻议会 | ~50K | 1 次/feature | 3~5 个 reviewer subagent |
| PLAN（bridge + deep-plan） | ~80K | 1 次/feature | deep-plan 包含 research/interview/review/TDD/sections |
| PLAN 计划议会 | ~150K | 1 次/feature | 5~7 个 reviewer subagent，**最重的议会** |
| EXECUTE（deep-implement） | ~50K/section | N sections/feature | 含 TDD + 内置 code review |
| VERIFY 验收议会 | ~200K | 1~3 次/feature | Ring 7 路并行 reviewer，**成本最高** |
| DONE（ECC + aio-reflect） | ~30K | 1 次/feature | 安全扫描 + 会话复盘 |
| **单个 feature 总计** | **~600K~1M+** | — | 取决于 section 数量和 FIX 循环次数 |

**结论**：一个中等复杂度的 feature（5~8 个 section，1 次 FIX 循环）预计消耗 **60~100 万 tokens**。如果议会全开、高风险路径，可能超过 150 万。这个成本在商用 AI 辅助开发中算**中高水平**，但因为方案内置了动态强度控制（低风险可跳过议会），实际均摊成本可以大幅降低。

### 1.3 风险评级

按影响面和发生概率综合评定：

| 风险 | 影响 | 概率 | 等级 | 说明 |
|------|------|------|------|------|
| **Hook 事件契约不稳定** | 高 | 中 | 🔴 高 | `TaskCompleted`/`TeammateIdle` 仓库内无实际使用。如果 stdin/stdout 格式与预期不符，核心门禁无法工作。但方案已通过"先用已验证事件 + PoC"缓解 |
| **组件自动触发越界** | 高 | 中 | 🔴 高 | Superpowers 的 brainstorming 完成后会自动进入 writing-plans；ShipSpec 的 Ralph Loop 会接管执行。如果编排器截获失败，整个阶段分离就会被破坏 |
| **ShipSpec→deep-plan 桥接失真** | 高 | 中 | 🟡 中高 | 格式转换本身不难，但"信息无损传递"很难验证——丢了一个关键验收标准或依赖关系，要到 EXECUTE 阶段才会暴露 |
| **议会 reviewer 输出不稳定** | 中 | 高 | 🟡 中高 | LLM 作为 reviewer 的输出格式不总是结构化的，裁决汇总逻辑需要处理各种非标准输出。多 reviewer 并行还可能出现矛盾结论 |
| **多组件依赖环境复杂** | 中 | 高 | 🟡 中 | Python 3.11 + uv + Node.js + Bun + jq + Go（可选）。每个组件的环境配置失败都会阻塞对应阶段 |
| **Token 成本超预算** | 中 | 中 | 🟡 中 | 方案已有动态强度控制和预算上限，但实际运行中议会 Token 消耗容易超预期 |
| **上下文窗口管理** | 中 | 低 | 🟢 低 | 方案已有分阶段加载策略，且 artifacts 传递而非对话传递的原则清晰 |
| **学习产物污染** | 低 | 低 | 🟢 低 | 双轨制（机器提名 + 人工晋升）在设计上已充分缓解 |

### 1.4 总体判断

| 维度 | 评定 | 对策 |
|------|------|------|
| 设计质量 | ✅ 高 | 四层架构清晰、职责划分到位、控制机制完备 |
| 一次性全量落地可行性 | ❌ 低 | 28 个任务、7 个组件、多个未验证假设，一次性做完风险很大 |
| 渐进式迭代可行性 | ✅ 高 | 方案天然可分层——先跑通骨架，再逐步接入组件和议会 |
| Token 成本可控性 | ⚠️ 需要动态控制 | 必须从第一天就实现动态强度控制，否则全量议会成本不可持续 |

**核心建议**：不要按 MVP-1/2/3 的原始划分一步步做完再验证，而应该按"**先最小闭环 → 再逐步接入 → 最后加强治理**"的思路，每个迭代都能独立运行和验证价值。

---

## 二、迭代策略：从"最小可跑通"到"完整体系"

### 2.1 迭代原则

1. **每个迭代必须可独立运行**：不是"做完 A 等 B"，而是每个迭代结束后系统就能处理真实 feature
2. **先验证高风险假设**：把不确定的东西（Hook 契约、桥接、组件截获）放到最早的迭代验证
3. **议会渐进引入**：从"无议会"开始，到"轻量 checklist"，再到"完整 reviewer 议会"
4. **组件渐进接入**：先用编排器 + prompt 模拟组件能力，验证流程可行后再接入真实组件
5. **成本随风险升级**：低风险 feature 走轻路径，仅高风险 feature 走完整路径

### 2.2 迭代总览

```
Iter-0  基础验证与脚手架           ← 验证关键假设，搭骨架
Iter-1  最小闭环（CLARIFY→DONE）   ← 不接组件，用编排器 prompt 跑通全流程
Iter-2  接入核心组件链             ← ShipSpec + deep-plan + deep-implement
Iter-3  桥接与门禁                 ← bridge-spec + Stop 门禁 + 基础验证
Iter-4  议会体系                   ← 从 checklist 到真实 reviewer agents
Iter-5  验收与修复闭环             ← Ring + FIX 循环
Iter-6  治理与学习                 ← ECC + aio-reflect + 发布议会
Iter-7  动态控制与生产强化         ← 风险评级 + 成本监控 + 恢复机制
```

---

## 三、迭代详细计划

### Iter-0：基础验证与脚手架

> **目的**：在动手搭建前，先验证三个高风险假设，避免在错误地基上建楼。

#### 验证任务

| 序号 | 验证项 | 做法 | 通过标准 | 失败应对 |
|------|--------|------|---------|---------|
| 0.1 | **Hook 事件 PoC** | 写最小插件，分别注册 `SessionStart`/`Stop`/`UserPromptSubmit` 三个 Hook，打印 stdin JSON 到文件 | 三个事件都能触发且 JSON 格式可解析 | 如某事件不可用，标记为不依赖该事件，用替代方案 |
| 0.2 | **Superpowers 截获 PoC** | 安装 Superpowers，在 brainstorming 完成后尝试通过编排 prompt 阻止自动进入 writing-plans | 编排器能成功截获控制权，不触发后续链路 | 如截获不可靠，改为不安装 Superpowers 插件，将 brainstorming prompt 直接内联到编排器 skill 中 |
| 0.3 | **ShipSpec 无 Ralph Loop 运行** | 安装 ShipSpec 但不安装其 `hooks/hooks.json`，调用 `/feature-planning` | PRD/SDD/TASKS 正常产出，Stop 钩子不触发 | 如无法分离钩子与命令，改为提取 ShipSpec 的 agents/skills 直接嵌入 stage-harness |

#### 脚手架任务

| 序号 | 任务 | 产出 |
|------|------|------|
| 0.4 | 创建 `stage-harness/` 目录结构 | `.claude-plugin/plugin.json`、`hooks/hooks.json`、`commands/`、`agents/`、`skills/`、`scripts/`、`templates/` |
| 0.5 | 编写 `state.json` 模板 | 包含 `currentStage`、`feature`、`stageHistory`、`councilResults` 最小字段 |
| 0.6 | 编写 `stage-init.sh` 最小版 | 仅做"读取 state.json + 向 stdout 输出 additionalContext" |

#### 迭代出口

- [ ] 三个 PoC 均通过（或有明确的替代方案）
- [ ] 插件脚手架可被 Claude Code 识别加载
- [ ] `stage-init.sh` 能在 SessionStart 时正确注入上下文

#### 风险缓解记录

如果 PoC 失败，在此记录替代决策：

| 原假设 | PoC 结果 | 替代方案 |
|--------|---------|---------|
| SessionStart/Stop/UserPromptSubmit 可用 | （待填） | （待填） |
| Superpowers 可截获 | （待填） | brainstorming prompt 内联到编排器 |
| ShipSpec 可无 Ralph Loop 运行 | （待填） | 提取 agents/skills 嵌入 stage-harness |

---

### Iter-1：最小闭环（不接外部组件）

> **目的**：用编排器自身的 prompt/skill 跑通 CLARIFY→SPEC→PLAN→EXECUTE→VERIFY→DONE 全链路，验证状态机和门禁框架能工作。**不接入任何外部组件。**

#### 为什么先不接组件？

外部组件集成是最大的不确定性来源。如果在状态机还没调通的时候就接组件，出了问题分不清是"流程问题"还是"组件问题"。先用内联 prompt 模拟每个阶段的行为，验证流程骨架。

#### 任务

| 序号 | 任务 | 做法 | 产出 |
|------|------|------|------|
| 1.1 | 实现 `stage-flow/SKILL.md` | 编写状态机规则：阶段列表、流转条件、产物清单 | SKILL.md |
| 1.2 | 实现 `harness-start` 命令 | 创建 `.harness/features/{name}/state.json`，设置初始阶段为 CLARIFY | 命令 markdown |
| 1.3 | 实现 `harness-status` 命令 | 读取并展示当前状态 | 命令 markdown |
| 1.4 | 实现 `harness-advance` 命令 | 检查当前阶段门禁条件 → 推进到下一阶段 → 更新 state.json | 命令 markdown |
| 1.5 | 实现内联 CLARIFY | 在 `stage-orchestrator.md` 中写 brainstorming prompt（不依赖 Superpowers） | 产出 `clarification-notes.md` |
| 1.6 | 实现内联 SPEC | 在编排器中写 PRD/SDD 生成 prompt（不依赖 ShipSpec） | 产出简化版 PRD.md、SDD.md |
| 1.7 | 实现内联 PLAN | 在编排器中写计划生成 prompt（不依赖 deep-plan） | 产出简化版 plan.md |
| 1.8 | 实现内联 EXECUTE | 直接编写代码（不依赖 deep-implement） | 代码 + 测试 |
| 1.9 | 实现内联 VERIFY | 在编排器中写 checklist 式审查 prompt（不依赖 Ring） | 简化版 review-report.md |
| 1.10 | 实现 `stage-gate-check.sh` | 根据当前阶段检查必备文件是否存在 | Hook 脚本 |
| 1.11 | 端到端冒烟测试 | 用"添加 Hello World API endpoint"跑通全流程 | 验证报告 |

#### 迭代出口

- [ ] `/harness-start` → `/harness-advance` 能从 CLARIFY 推进到 DONE
- [ ] 每个阶段产出对应 artifact
- [ ] `stage-gate-check.sh` 能在产物缺失时阻断
- [ ] state.json 正确记录全部阶段历史

#### 此迭代结束后系统能力

一个人可以使用 `/harness-start` 启动工作流，系统会引导经过全部阶段，每个阶段有基本的产物检查门禁。**没有外部组件依赖，没有议会，没有桥接**——但流程骨架是完整的。

---

### Iter-2：接入核心组件链

> **目的**：用真实组件替换 Iter-1 中的内联 prompt，打通 ShipSpec + deep-plan + deep-implement 主链路。

#### 前置条件

- Iter-0 的 PoC 已通过（或有替代方案）
- Iter-1 的状态机和门禁框架可运行

#### 任务

| 序号 | 任务 | 替换内容 | 验收标准 |
|------|------|---------|---------|
| 2.1 | 接入 Superpowers brainstorming | 替换 Iter-1.5 的内联 CLARIFY prompt | brainstorming 能完成，编排器能截获控制权 |
| 2.2 | 接入 ShipSpec `/feature-planning` | 替换 Iter-1.6 的内联 SPEC prompt | PRD/SDD/TASKS 产出且 Ralph Loop 未触发 |
| 2.3 | 接入 deep-plan | 替换 Iter-1.7 的内联 PLAN prompt | plan/tdd/sections 全套产出 |
| 2.4 | 接入 deep-implement | 替换 Iter-1.8 的内联 EXECUTE | 按 section TDD 实现 + 原子提交 |
| 2.5 | 环境依赖自动检查 | 在 `stage-init.sh` 中检查 Python/uv/jq/Node 等 | 缺少依赖时给出明确提示 |

#### 关键风险点

- **2.1 的截获风险**：如果 Iter-0.2 的 PoC 证明截获不可靠，此处改用"内联 brainstorming prompt"方案，不安装 Superpowers 插件
- **2.2 的 Hook 隔离**：必须确认 ShipSpec 的 Stop 钩子未被加载。验证方法：在 SPEC 阶段完成后检查 `.shipspec/` 下是否存在 Ralph Loop 状态文件（不应存在）
- **2.3 的输入格式**：此迭代先用 **SDD.md 直接作为 deep-plan 输入**（备选方案），不做桥接。桥接放到 Iter-3

#### 迭代出口

- [ ] 真实组件产出替换内联 prompt 产出
- [ ] CLARIFY→SPEC→PLAN→EXECUTE 链路用真实组件跑通
- [ ] VERIFY 和 DONE 仍使用 Iter-1 的内联方式（下个迭代处理）

---

### Iter-3：桥接与门禁强化

> **目的**：实现 ShipSpec→deep-plan 的正式桥接，强化阶段门禁。

#### 任务

| 序号 | 任务 | 说明 | 验收标准 |
|------|------|------|---------|
| 3.1 | 实现 `bridge-shipspec-to-deepplan.sh` | 从 PRD/SDD/TASKS 提取关键信息合并为 `bridge-spec.md` | deep-plan 能消费 bridge-spec.md 且计划质量不低于直接用 SDD.md |
| 3.2 | 桥接完整性测试 | 对比 bridge-spec.md 与源 PRD/SDD/TASKS 的信息覆盖度 | 需求摘要、架构决策、任务依赖、验收标准均无丢失 |
| 3.3 | 实现 Decision Bundle | CLARIFY→SPEC 和 SPEC→PLAN 出口的 Decision Bundle 生成 | 汇总待决策问题并展示给用户 |
| 3.4 | 强化 `stage-gate-check.sh` | 不只检查文件存在，还检查内容完整性（如 TASKS.json 非空、sections 数量 > 0） | 空文件或格式错误也能被拦截 |
| 3.5 | 实现 `stage-reminder.sh` | UserPromptSubmit 时注入当前阶段提醒 | 用户收到阶段感知提示 |

#### 迭代出口

- [ ] bridge-spec.md 信息无损可验证
- [ ] Decision Bundle 在至少两个出口正常工作
- [ ] 门禁能拦截内容不合格的产物（不只是文件缺失）

---

### Iter-4：议会体系

> **目的**：从 checklist 升级到真实的 reviewer agent 议会，分步实现四类议会。

#### 4.1 分步策略

不一次实现四类议会，而是分三步：

**Step 4a：Checklist 式议会（prompt 模拟）**

用单个 LLM 调用模拟多 reviewer 的效果——在 prompt 中要求 LLM 从多个视角（完整性、一致性、可落地性）审查产物并输出结构化裁决。成本约为完整议会的 1/5。

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 4a.1 | 实现 SPEC checklist 审查 | 产出 `spec-council-verdict.json`，含 GO/REVISE/HOLD |
| 4a.2 | 实现 PLAN checklist 审查 | 产出 `plan-council-verdict.json`，含 READY/READY_WITH_CONDITIONS/BLOCK |
| 4a.3 | 将 checklist 裁决接入门禁 | verdict 为阻断时 `stage-gate-check.sh` 阻止推进 |

**Step 4b：轻议会 + 计划议会（真实 subagent）**

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 4b.1 | 编写 `spec-reviewer.md` agent | 能作为 subagent 独立审查 SPEC 产物 |
| 4b.2 | 编写 `plan-reviewer.md` agent | 能作为 subagent 独立审查 PLAN 产物 |
| 4b.3 | 实现 `council-dispatch` skill | 能并行启动多个 reviewer subagent 并汇总结果 |
| 4b.4 | 实现裁决汇总逻辑 | 处理 reviewer 输出不一致的情况（多数决 vs 一票否决） |

**Step 4c：完整四类议会**

| 序号 | 任务 | 验收标准 |
|------|------|---------|
| 4c.1 | 编写验收议会 reviewer agents（如果不用 Ring，见 Iter-5） | 7 路并行审查 |
| 4c.2 | 编写 `release-reviewer.md` agent | 发布议会 3~4 reviewer |
| 4c.3 | 实现议会规模动态调整 | 根据 state.json 的 riskLevel 调整 reviewer 数量 |

#### 迭代出口

- [ ] 至少 SPEC 和 PLAN 阶段有可工作的议会（checklist 或 subagent）
- [ ] 议会裁决正确接入门禁
- [ ] 阻断时用户能收到明确的裁决报告

---

### Iter-5：验收与修复闭环

> **目的**：接入 Ring 做正式验收，实现 FIX→VERIFY 循环。

#### 任务

| 序号 | 任务 | 说明 | 验收标准 |
|------|------|------|---------|
| 5.1 | 安装 ring-default 插件 | 仅安装 default，不安装 dev-team/pm-team/pmo-team/finops-team | Ring 的 `/ring:codereview` 可调用 |
| 5.2 | 接入 Ring 替换内联 VERIFY | 调用 `/ring:codereview` 做 7 路并行审查 | 审查结果产出 review-report.md |
| 5.3 | 实现 VERIFY 结果解析 | 将 Ring 审查结果转为 `verification.json` 的 PASS/FAIL 格式 | 裁决格式标准化 |
| 5.4 | 实现 FIX 阶段 | deep-implement 针对 FAIL 问题修复 → 重跑 Ring 审查 | 修复后能重新触发验收 |
| 5.5 | 实现 FIX 轮次控制 | state.json 记录 verifyAttempts，达到 3 次上限升级 | 循环正确终止或升级人工 |
| 5.6 | 实现 VERIFY→DONE Decision Bundle | 在 VERIFY 通过后触发最终决策包 | 人工确认后进入 DONE |

#### 迭代出口

- [ ] Ring 7 路审查可运行
- [ ] FIX→VERIFY 循环最多 3 轮后自动终止
- [ ] 全链路（CLARIFY→DONE）可端到端跑通

---

### Iter-6：治理与学习

> **目的**：接入 ECC + aio-reflect，实现 DONE 阶段的治理、安全扫描与持续学习。

#### 任务

| 序号 | 任务 | 说明 | 验收标准 |
|------|------|------|---------|
| 6.1 | 接入 ECC `security-reviewer` | 在 DONE 阶段调用做最终安全扫描 | 安全报告产出 |
| 6.2 | 接入 aio-reflect | 在 DONE 阶段做会话复盘 | 经验候选列表产出 |
| 6.3 | 实现发布议会 | `release-reviewer.md` agents + 裁决汇总 | 3~4 reviewer 评审交付产出 verdict |
| 6.4 | 实现双轨学习 | 候选经验 → 展示给人工 → 确认后写入 | 自动写入被阻止，人工晋升可操作 |
| 6.5 | 自动生成交付包 | `release-notes.md`、`delivery-summary.md` | 交付包内容完整 |

#### 迭代出口

- [ ] DONE 阶段有安全扫描和学习复盘
- [ ] 发布议会可运行
- [ ] 交付包自动生成

---

### Iter-7：动态控制与生产强化

> **目的**：让系统可持续运行——成本可控、崩溃可恢复、风险可分级。

#### 任务

| 序号 | 任务 | 说明 | 验收标准 |
|------|------|------|---------|
| 7.1 | 实现风险等级自动评估 | CLARIFY 阶段根据需求特征设置 riskLevel | 评估结果写入 state.json |
| 7.2 | 实现动态强度控制 | 根据 riskLevel 调整议会规模和是否跳过 | 低风险 feature 自动简化流程 |
| 7.3 | 实现成本监控 | `harness-status` 展示各阶段 token 预估 | 数据可读 |
| 7.4 | 实现 Session Handoff | `session-handoff` skill + 模板 | 跨 session 恢复工作上下文 |
| 7.5 | 实现 smoke-check | Session 开始时执行基础验证 | 能检测到前序 session 的破坏性变更 |
| 7.6 | 实现崩溃恢复 | 未完成 section 回滚 + 从最后成功 section 恢复 | 中断后能无损恢复 |
| 7.7 | 实现回滚命令 | `/harness-rollback` 回退到上一阶段 | state.json + git 都正确回退 |
| 7.8 | Eval Harness 数据面 | trace、metrics、outcome-check 收集 | 数据可用于后续分析 |

#### 迭代出口

- [ ] 低风险 feature 走轻路径，高风险走完整路径
- [ ] 中断后能恢复工作
- [ ] 运行数据可追踪

---

## 四、迭代依赖关系

```
Iter-0 ──→ Iter-1 ──→ Iter-2 ──→ Iter-3 ──→ Iter-5
              │                      │           ↑
              │                      │           │
              │                      └── Iter-4 ─┘
              │
              └── (Iter-4 的 Step 4a 可与 Iter-2 并行)

Iter-5 ──→ Iter-6 ──→ Iter-7
```

关键路径：`Iter-0 → Iter-1 → Iter-2 → Iter-3 → Iter-5`

Iter-4（议会）可以在 Iter-2 完成后的任何时间点开始，不阻塞主链路。Iter-6、Iter-7 是增强项，不影响核心流程可用性。

---

## 五、各迭代的可交付价值

| 迭代 | 完成后能做什么 | 还不能做什么 |
|------|--------------|------------|
| **Iter-0** | 确认技术假设是否成立 | 不能跑任何 feature |
| **Iter-1** | 用编排器引导走完全流程（内联 prompt） | 没有真实组件能力，产出质量有限 |
| **Iter-2** | 用真实组件（ShipSpec/deep-plan/deep-implement）产出高质量规格和代码 | 没有桥接（用备选方案），没有议会，没有正式验收 |
| **Iter-3** | 桥接无损 + 门禁拦截不合格产物 + Decision Bundle | 没有多 reviewer 议会审查 |
| **Iter-4** | 关键节点有议会审查把控质量 | 没有 Ring 正式验收 |
| **Iter-5** | **完整 CLARIFY→DONE 全链路可运行**，含 Ring 验收和 FIX 循环 | 没有安全扫描、学习复盘、动态控制 |
| **Iter-6** | 安全扫描 + 学习复盘 + 发布议会 | 没有动态强度控制、崩溃恢复 |
| **Iter-7** | **生产级系统**：成本可控、可恢复、可分级 | — |

**实用建议**：大部分场景下，完成到 **Iter-5** 就已经是一个可用的系统。Iter-6/7 是锦上添花，可以根据实际使用反馈再决定优先级。

---

## 六、快速启动建议

如果想最快验证方案可行性，建议的执行顺序：

1. **先做 Iter-0**（0.5 天），验证 Hook 和组件截获是否可行
2. **跳到 Iter-1**（1~2 天），跑通全流程骨架
3. **做 Iter-2 + Iter-4 Step 4a 并行**（1~2 天），接入组件 + checklist 式议会
4. 到这一步就有一个**可用的最小系统**了

后续的 Iter-3/4b/5/6/7 可以根据实际痛点按需推进。

---

## 七、成本控制检查点

每个迭代结束时做一次成本检查：

| 检查项 | 阈值 | 超出怎么办 |
|--------|------|-----------|
| 单次议会 Token 消耗 | 轻议会 ≤ 50K、计划议会 ≤ 150K、验收议会 ≤ 200K | 减少 reviewer 数量或改用 checklist 模式 |
| 单 feature 全流程 Token | ≤ 1M（中等复杂度） | 启用动态强度控制，低风险跳过议会 |
| 单次桥接脚本 Token | ≤ 5K（脚本本身不调 LLM） | 如桥接脚本需要调 LLM，考虑用更简单的模板拼接 |
| 单次 Hook 执行时间 | ≤ 5 秒 | Hook 只做文件检查，不调 LLM |

---

## 八、退出条件与降级策略

如果某个迭代遇到无法解决的阻塞，不应停止整个项目，而是降级：

| 阻塞场景 | 降级策略 |
|---------|---------|
| Superpowers 截获不可靠 | 不安装 Superpowers 插件，将 brainstorming prompt 内联到编排器 skill |
| ShipSpec 无法分离 Ralph Loop | 提取 ShipSpec 的 agent 定义（prd-gatherer、design-architect、task-planner）嵌入 stage-harness |
| bridge-spec 信息丢失严重 | 用 SDD.md 直接作为 deep-plan 输入（备选方案），接受 Interview 阶段补充 |
| Ring 安装/运行困难 | 用内联 checklist 审查 prompt 替代 Ring 7-reviewer |
| 议会 reviewer 输出格式不稳定 | 降级为 checklist 模式（单 LLM 调用多视角审查） |
| deep-plan 环境配置复杂 | 先用编排器内联 prompt 做轻量计划，后续逐步接入 |
| Token 成本超预算 | 全面启用动态强度控制 + 将所有议会降级为 checklist |

**核心思想**：每个组件都有"内联 prompt 替代"的降级路径，确保系统不会因单点依赖而整体不可用。
