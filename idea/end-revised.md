# Claude Code 阶段化 AI Harness 落地方案（修订版）

## 一、文档目的

本文档用于替代 `idea/end.md` 中偏概念化、部分实现细节不够准确的版本，输出一份**更贴近当前代码与插件生态现实**的阶段化 AI Harness 方案。

目标不是推翻原方案，而是：

1. 保留原方案中正确的总体方向；
2. 修正插件结构、Hooks、MCP、Agents 安装方式等实现细节；
3. 明确各开源组件的职责边界，避免能力重叠；
4. 给出一条更容易从 MVP 演进到稳定系统的主干路线。

---

## 二、结论摘要

### 1. 总体判断

原方案的**组件选型方向基本正确**，但需要对“谁负责哪个阶段”进行收敛。

最推荐的主干组合是：

- **Superpowers**：负责需求澄清方法与早期思考引导
- **ShipSpec**：负责规格产物化（PRD / SDD / TASKS）
- **Deep Trilogy（以 deep-plan / deep-implement 为主）**：负责计划与实施主干
- **Ring**：负责并行审查与验证门禁
- **ECC + aio-reflect**：负责治理、审计与持续学习

### 2. 核心建议

> **规格归 ShipSpec，执行归 Deep，审查归 Ring，治理归 ECC / aio-reflect。**

也就是说：

- 不建议同时让 **ShipSpec** 和 **deep-implement** 都承担“执行主循环”；
- 不建议把 **ECC** 当成一个很薄的即插即用小模块；
- 不建议在未验证前，把“插件内 agents 会忽略某些 frontmatter”当成已知事实写进设计前提。

---

## 三、推荐架构

采用四层而不是三层描述，更利于后续拆分责任：

1. **阶段编排层（Orchestration）**
   - 维护状态机；
   - 决定当前阶段调用哪个插件能力；
   - 汇总阶段产物与阶段出口的审批项。

2. **产物生成层（Spec & Plan Generation）**
   - 负责 PRD、SDD、TASKS、计划文档、section 文档等；
   - 由 Superpowers、ShipSpec、deep-plan 共同提供能力。

3. **执行与验证层（Execution & Verification）**
   - 负责 TDD、编码、实现、代码审查、测试报告；
   - 由 deep-implement、Ring 提供主能力。

4. **治理与学习层（Governance & Learning）**
   - 负责 hooks、质量门禁、质量审计、经验提炼；
   - 由 ECC、aio-reflect、自建脚本共同实现。

---

## 四、推荐阶段流转

建议采用如下阶段状态机：

```text
IDEA
  -> CLARIFY
  -> SPEC
  -> PLAN
  -> EXECUTE
  -> VERIFY
  -> FIX
  -> DONE
```

如果面对的是“大而模糊”的产品级目标，可在 `CLARIFY` 前增加：

```text
DISCOVER -> CLARIFY
```

这个前置阶段可以由 `deep-project` 或类似拆解器处理，把“大目标”先拆成若干 feature/spec，再进入后续链路。

---

## 五、各阶段推荐组件分工

## 5.1 CLARIFY：需求澄清

### 目标

- 把模糊需求变成可确认的问题空间；
- 汇总关键决策点，而不是频繁打断用户；
- 形成 PRD 的输入素材。

### 推荐组件

- **Superpowers**
  - 使用其 `brainstorming` 一类能力做苏格拉底式提问与问题收敛；
  - 适合控制对话节奏、补齐边界与约束。

### 输出产物

- `clarification-notes.md`
- `decision-bundle.json`
- 初始 feature 简述

### 不建议

- 不建议在这一阶段直接让 Deep 或 Ring 介入主流程；
- 不建议在澄清阶段就进入实现级 task 拆分。

---

## 5.2 SPEC：规格定义

### 目标

- 产出结构化、可审查、可继续向下游传递的规格文档；
- 固化需求、设计决策与任务边界。

### 推荐组件

- **ShipSpec**
  - 负责 PRD / SDD / TASKS 的规范化输出；
  - 很适合做“规格权威来源”。

### 输出产物

- `PRD.md`
- `SDD.md`
- `TASKS.json`
- `TASKS.md`

### 推荐定位

这里建议把 ShipSpec 定位为：

> **规格生成器，而不是默认的执行主循环。**

原因是它虽然自带任务执行与验证循环，但如果后续已选择 `deep-plan / deep-implement` 作为实施主干，就应避免两套执行范式并存。

---

## 5.3 PLAN：实施计划

### 目标

- 把规格转化为能执行的计划；
- 引入研究、技术校验、多模型复核和 TDD 视角；
- 切分出可并行、可提交、可恢复的 section。

### 推荐组件

- **deep-plan**
  - 作为实施计划主干；
  - 负责研究、访谈、外部复核、TDD planning、section splitting。

### 输出产物

- `plan.md`
- `research.md`
- `review-notes.md`
- `sections/*.md`
- `test-stubs-plan.md`

### 说明

如果系统目标是“计划质量优先”，那么 `deep-plan` 比单纯让 ShipSpec 直接把 TASKS 交给实现更稳。

---

## 5.4 EXECUTE：开发执行

### 目标

- 按 section 推进实现；
- 强制 TDD；
- 每段实现可追溯、可恢复、可独立提交。

### 推荐组件

- **deep-implement**
  - 执行 section 级实现；
  - 控制 TDD、代码修改、文档回写、原子提交。

### 输出产物

- 代码变更
- 测试文件
- section 实现记录
- 分段提交历史

### 关键原则

- 一次只允许一个主执行器负责推进代码；
- 如果已采用 `deep-implement`，则**不要再启用 ShipSpec 的全量实现闭环作为并行主流程**。

---

## 5.5 VERIFY：验证与审查

### 目标

- 防止“口头完成”；
- 引入并行审查，扩大问题覆盖面；
- 将测试、审查、静态检查统一到可阻断门禁中。

### 推荐组件

- **Ring**
  - 用于并行 code review；
  - 适合作为多 reviewer gate。
- **自建验证脚本 / hooks**
  - 负责读取测试结果、报告路径、review verdict；
  - 形成统一的 pass/fail 结果。

### 输出产物

- `review-report.md`
- `test-report.md`
- `verification.json`

### 推荐规则

- 测试不通过，不能结束阶段；
- 任意关键 reviewer 输出 reject，回退到 `FIX`；
- 只有验证产物齐全，才允许 `VERIFY -> DONE`。

---

## 5.6 FIX：问题修复

### 目标

- 处理 VERIFY 阶段打回的问题；
- 保留问题来源、修复记录与复验证据。

### 推荐组件

- `deep-implement` 继续承担修复执行；
- `Ring` 重跑关键 reviewer；
- hooks 重新校验。

### 输出产物

- `fix-log.md`
- 更新后的 `verification.json`

---

## 5.7 DONE：交付与沉淀

### 目标

- 输出交付包；
- 汇总变更、验证结论与上线说明；
- 从会话中提炼长期可复用经验。

### 推荐组件

- **ECC**
  - 做质量门控与治理审计；
  - 按需吸收 `/quality-gate` 一类能力。
- **aio-reflect**
  - 从会话中抽取经验；
  - 产出 CLAUDE.md 更新建议或 skills 候选。

### 输出产物

- `release-notes.md`
- `delivery-summary.md`
- `learning-candidates.md`

### 说明

这里建议采用“双轨制”：

1. 机器负责提名候选经验；
2. 人工决定是否晋升为长期规则或技能。

---

## 六、职责边界与取舍建议

为了避免组件互相覆盖，建议按下表裁边：

| 组件 | 保留职责 | 不作为主职责 |
| --- | --- | --- |
| Superpowers | 需求澄清、思考引导、前期问题收敛 | 不作为最终执行主循环 |
| ShipSpec | PRD / SDD / TASKS 规格产出 | 不作为与 deep-implement 并行的执行器 |
| deep-plan | 实施计划主干、section 切分、研究与复核 | 不负责最终并行审查门禁 |
| deep-implement | 执行主干、TDD、原子提交 | 不负责规格权威定义 |
| Ring | 并行审查、验证放大器 | 不负责规格生成或执行主循环 |
| ECC | 治理、审计、质量门控参考与能力集 | 不作为唯一编排器 |
| aio-reflect | 会话复盘、经验提炼 | 不直接作为 rules 自动写入器 |

---

## 七、推荐插件与目录结构

修订后的自建插件建议采用如下结构：

```text
stage-harness/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
├── hooks/
│   ├── hooks.json
│   ├── task-check.sh
│   └── idle-check.sh
├── scripts/
├── templates/
├── .mcp.json            # 可选
└── README.md
```

### 说明

- `plugin.json` 建议放在 `.claude-plugin/` 下；
- `commands/`、`agents/`、`skills/`、`hooks/` 位于插件根目录；
- MCP 更推荐使用 `.mcp.json` 或 manifest 的 `mcpServers`；
- 不建议再写成 `harness-plugin/plugin.json` 直接位于根目录。

---

## 八、Hooks 设计修订

## 8.1 推荐思路

保留原文“硬门禁”思想，但修正配置方式：

- 用 `TaskCompleted` 做任务完成阻断；
- 用 `TeammateIdle` 做空闲阻断或补动作提醒；
- 用 `Stop` / `SubagentStop` 做阶段性检查；
- 用状态文件记录当前阶段、必备产物和验证要求。

## 8.2 推荐配置格式

不要使用：

```json
{
  "hooks": [
    { "event": "TaskCompleted", "script": "./hooks/task-check.sh" }
  ]
}
```

应使用类似：

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/task-check.sh"
          }
        ]
      }
    ],
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/idle-check.sh"
          }
        ]
      }
    ]
  }
}
```

## 8.3 重要注意事项

- 在部分现有插件实践中，Claude Code v2.1+ 会自动加载 `hooks/hooks.json`；
- 因此不建议默认把 hooks 再显式写入 `.claude-plugin/plugin.json`；
- hooks 的 stdin/stdout JSON 结构，在真正实现前必须用最小 PoC 验证，不应仅依据示意脚本假设字段存在。

---

## 九、Decision Bundle 机制保留，但表达方式升级

原方案中的 `Decision Bundle` 思想是正确的，建议保留。

### 原则

- 不在流程中间频繁打断用户；
- 把必须由人拍板的问题统一汇总到阶段出口；
- 输出机器可解析结果，供状态机继续推进。

### 推荐格式

```json
{
  "stage": "SPEC",
  "decisionBundle": [
    {
      "id": "D1",
      "question": "数据库选型",
      "options": ["PostgreSQL", "MongoDB"],
      "default": "PostgreSQL",
      "impact": "影响数据模型与部署方式"
    },
    {
      "id": "D2",
      "question": "是否要求高可用",
      "options": ["是", "否"],
      "default": "否",
      "impact": "影响部署与成本"
    }
  ]
}
```

### 建议触发点

- `CLARIFY -> SPEC`
- `SPEC -> PLAN`
- `VERIFY -> DONE`

---

## 十、MCP 配置策略修订

原方案里“在 `.claude/mcp-servers.json` 中配置”的表述过于单一，修订建议如下。

### 推荐优先级

1. **插件级**
   - `.mcp.json`
   - 或 `.claude-plugin/plugin.json` 中的 `mcpServers`

2. **用户级**
   - `~/.claude.json`

3. **项目级**
   - 按 Claude Code 当前支持方式配置到项目范围

### 建议用途

- `PLAN` 阶段：文档研究、任务同步、外部信息拉取
- `DONE` 阶段：PR、变更摘要、交付信息收集

### 风险提示

- 不要在未确认配置作用域前，把单一文件路径写成唯一标准；
- MCP 涉及凭据时，必须走最小权限与显式密钥管理。

---

## 十一、关于 Agents 安装方式的修订判断

原文中“插件内 subagent 会忽略 hooks / mcpServers frontmatter，因此必须复制到 `.claude/agents/`”这个前提，当前不应作为确定事实写入。

### 更稳妥的结论

- 将 agents 复制到 `~/.claude/agents/` 或 `.claude/agents/`，可以作为一种**安装策略**；
- 这样做的价值主要在于：
  - 用户级或项目级覆盖；
  - 更方便手工维护；
  - 与已有本地 agents 体系统一管理。

### 但不应默认断言

- “插件内 agents 一定忽略 frontmatter”

这类结论应以官方插件行为验证为准，而不是作为体系前提。

---

## 十二、最小可用版本（MVP）建议

不建议第一版就做完整大而全系统，建议按以下顺序逐步落地：

### MVP-1：规格与计划打通

- Superpowers 做澄清
- ShipSpec 产出 PRD / SDD / TASKS
- deep-plan 产出 section 级计划
- 仅做简单状态流转，不上复杂 hooks

### MVP-2：执行与验证闭环

- 接入 deep-implement
- 加入 Ring 并行审查
- 引入 `TaskCompleted` 的硬门禁

### MVP-3：治理与学习

- 引入 ECC 的质量门控子集
- 引入 aio-reflect 的会话复盘
- 上线“候选经验 -> 人工晋升”的持续学习流程

---

## 十三、关键风险与缓解措施

## 13.1 组件职责冲突

### 风险

- ShipSpec、Superpowers、Deep 在计划与执行环节有重叠；
- 同时启用会导致权威产物不清晰。

### 缓解

- 明确唯一权威：
  - 规格权威 = ShipSpec
  - 执行权威 = deep-implement
  - 审查权威 = Ring

## 13.2 Hooks 输入输出假设错误

### 风险

- 仅凭文档示意写脚本，真实运行时字段名不一致。

### 缓解

- 先做最小 PoC；
- 把 hook 的 JSON 契约纳入自动化测试。

## 13.3 规则与经验膨胀

### 风险

- 持续学习产物不断增长，互相冲突。

### 缓解

- 只允许机器提名候选；
- 人工审核后再晋升为规则或技能。

## 13.4 Token 与延迟成本

### 风险

- 多阶段、多 reviewer、多模型复核成本高。

### 缓解

- 限制并发 reviewer 数量；
- 对低风险环节使用小模型；
- 分阶段清理上下文与中间产物。

---

## 十四、最终推荐版本

如果要把这个方案写成一句工程化建议，可以表述为：

> 构建一个自建 `stage-harness` 插件作为编排外壳：  
> 用 **Superpowers** 做澄清引导，  
> 用 **ShipSpec** 产出规格，  
> 用 **deep-plan / deep-implement** 承担计划与执行主干，  
> 用 **Ring** 做并行审查，  
> 用 **ECC + aio-reflect** 做治理与学习，  
> 并通过 `hooks/hooks.json`、状态文件和 Decision Bundle 在阶段出口实施硬门禁。

---

## 十五、附录：与现有代码/文档的对应关系

以下仓库内容支撑了本修订版结论：

- `shipspec-claude-code-plugin/README.md`
  - ShipSpec 的 PRD / SDD / TASKS 与 Ralph Loop 定位
- `deep-plan/README.md`
  - `Research -> Interview -> External LLM Review -> TDD Plan -> Section Splitting`
- `deep-implement/README.md`
  - `Read Section -> TDD Implementation -> Code Review -> Interview -> Commit -> Next`
- `ring/README.md`
  - 并行 reviewer 与 `/ring:codereview`
- `everything-claude-code/schemas/hooks.schema.json`
  - 当前 hooks 事件与配置结构
- `everything-claude-code/docs/zh-CN/README.md`
  - hooks 自动加载、手动安装方式、MCP 配置说明
- `compound-engineering-plugin/docs/specs/claude-code.md`
  - 插件目录、manifest、hooks、MCP 的规范描述
- `SuperClaude_Framework/docs/user-guide/claude-code-integration.md`
  - Claude Code agents / skills / hooks / MCP 集成点说明
- `claude-plugins/plugins/aio-reflect/skills/aio-reflect/SKILL.md`
  - 反思与经验提炼的真实输出方向

---

## 十六、后续动作建议

建议下一步从以下两件事中二选一：

1. 继续补一份 `stage-harness` 的**目录脚手架与配置草案**；
2. 基于本方案输出一份**MVP 实施清单**，把每一步拆成可执行任务。
