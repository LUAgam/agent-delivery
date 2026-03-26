# final-plan-v2.md 补充建议

本文档是对 `idea/final-plan-v2.md` 的逐项分析与补充建议，覆盖 V2 未涉及或浅尝辄止的维度。按优先级分为三类：**关键补充**（不补会影响落地）、**重要补充**（不补会增加风险或降低效率）、**建议补充**（锦上添花）。

---

## 一、关键补充（不补会影响落地）

### 1.1 组件能力裁剪清单缺失

**问题**：V2 只描述了"用什么组件做什么"，但没有明确说"各组件的哪些能力要**禁用**"。`final-plan.md` 第五节有详细的裁剪清单（Superpowers 禁用 writing-plans/executing-plans 等自动触发、ShipSpec 禁用 Ralph Loop 的 Stop 钩子、Ring 只启用 default 插件的 review 能力、ECC 只启用 security-reviewer/harness-optimizer 等），但 V2 完全没有保留这些内容。

**风险**：组件自动触发机制导致职责越界。例如 Superpowers 的 brainstorming 完成后会自动进入 writing-plans → subagent-driven-development，直接与 deep-plan/deep-implement 冲突。

**建议补充**：

在第四节"职责与控制权矩阵"中增加一列"显式禁用项"，至少覆盖：

| 组件 | 保留职责 | 显式禁用 |
|------|---------|---------|
| Superpowers | brainstorming 技能 | writing-plans、executing-plans、subagent-driven-development、requesting-code-review 的自动触发 |
| ShipSpec | `/feature-planning` → PRD/SDD/TASKS | `/implement-task`、`/implement-feature`、Stop 钩子（Ralph Loop） |
| Ring | `/ring:codereview` 7 路并行审查 | pm-team（15 个规划技能与 ShipSpec 重叠）、dev-team 的 dev-cycle（10 门控开发流与 deep-implement 重叠）、pmo-team、finops-team |
| ECC | security-reviewer、harness-optimizer、质量门控命令 | planner、architect、tdd-guide、code-reviewer 等全链路代理（28 个代理中仅启用 2~3 个） |
| aio-reflect | 会话分析 → 经验提名 → 人工晋升 | 自动写入 rules（必须经人工确认） |

### 1.2 ShipSpec → deep-plan 桥接的技术规格不足

**问题**：V2 在 6.3 节提到 bridge 的"必须带入信息"和"禁止状态"，但没有给出桥接的技术实现方案。`final-plan.md` 第 5.3 节有明确的桥接流程图和脚本职责定义。

**风险**：ShipSpec 输出 `TASKS.json`/`TASKS.md`（结构化 JSON + Markdown），deep-plan 期望输入为单个 spec markdown 文件。格式不兼容会导致 SPEC → PLAN 链路断裂。

**建议补充**：

在第六节 6.3 中增加：

```text
ShipSpec 输出              桥接                    deep-plan 输入
─────────────          ──────────              ──────────────
PRD.md          ──┐
SDD.md          ──┼──→ bridge-spec.md ──→ /deep-plan @bridge-spec.md
TASKS.json      ──┘
```

桥接脚本的具体职责：
1. 从 PRD.md 提取需求摘要与优先级
2. 从 SDD.md 提取架构决策、接口设计、数据模型
3. 从 TASKS.json 提取任务清单、依赖关系、验收标准
4. 合并为一份 deep-plan 可消费的 `bridge-spec.md`

备选方案：直接以 SDD.md 作为 deep-plan 输入（信息损失较大但更简单），由 deep-plan 的 Interview 阶段补充缺失信息。

### 1.3 两层审查模型未显式区分

**问题**：V2 在 EXECUTE 阶段提到 deep-implement 的"实现级审查"，在 VERIFY 阶段提到 Ring 的"验收议会"，但没有像 `final-plan.md` 那样明确建立**两层审查模型**及其分工。

**风险**：不区分两层审查会导致重复审查（同一代码被审查两次，Token 浪费）或审查漏洞（以为对方会审查的盲区）。

**建议补充**：

在第七节增加"审查分层"小节：

| 层次 | 负责组件 | 审查范围 | 触发时机 | 成本特征 |
|------|---------|---------|---------|---------|
| 实现级 | deep-implement 内置 code-reviewer | 当前 section 的 staged diff | 每个 section 实现后自动触发 | 轻量、高频 |
| 验证级 | Ring 并行 reviewer（验收议会） | 全量变更 + 跨 section 影响 | 所有 section 完成后进入 VERIFY | 重量、低频 |

### 1.4 Hooks 事件的验证状态不明确

**问题**：V2 在 9.1 节区分了"已有实践依据"和"增强项"事件，但没有给出各事件的具体验证状态。`final-plan.md` 有一张清晰的验证状态表。

**风险**：如果基于未验证的事件构建核心门禁，上线后发现行为不一致将导致门禁失效。

**建议补充**：

| 事件 | 用途 | 验证状态 | 依据 |
|------|------|---------|------|
| `SessionStart` | 加载状态、恢复阶段上下文 | ✅ 已验证 | Ring、deep-implement 都在使用 |
| `Stop` | 阶段出口门禁 | ✅ 已验证 | ShipSpec Ralph Loop 使用 |
| `UserPromptSubmit` | 阶段感知提醒 | ✅ 已验证 | Ring claude-md-reminder 使用 |
| `TaskCompleted` | 阶段出口硬门禁 | ⚠️ 需 PoC | schema 支持但仓库中无实际使用 |
| `TeammateIdle` | 空闲检测 + 补动作提醒 | ⚠️ 需 PoC | schema 支持但仓库中无实际使用 |

### 1.5 stage-harness 插件结构缺失

**问题**：V2 是"方案文档"，但没有给出 `stage-harness` 插件的推荐目录结构。`final-plan.md` 第九节有完整的目录树。

**建议补充**：

```text
stage-harness/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── harness-start.md          # 启动 stage-harness 工作流
│   ├── harness-status.md         # 查看当前阶段状态
│   └── harness-advance.md        # 手动推进阶段（需满足门禁）
├── agents/
│   └── stage-orchestrator.md     # 编排代理
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
│   ├── bridge-shipspec-to-deepplan.sh
│   ├── verify-artifacts.sh
│   └── decision-bundle.sh
├── templates/
│   ├── state.json
│   └── decision-bundle.json
└── README.md
```

---

## 二、重要补充（不补会增加风险或降低效率）

### 2.1 回滚机制的技术细节

**问题**：V2 反复强调"可回退"，但没有说明回退的具体操作是什么。

**需要回答的问题**：
- 回退时，上游阶段的 artifacts 是保留还是清除？
- 回退是回到上一阶段重新执行，还是回到上一阶段的某个检查点？
- git 历史如何处理？是 revert 还是新建 fix 分支？
- 状态文件如何记录回退事件？
- 多次回退是否有限制？

**建议补充方案**：

```json
{
  "rollbackPolicy": {
    "preserveUpstreamArtifacts": true,
    "rollbackTarget": "previous_stage_entry",
    "gitStrategy": "new_branch_from_last_good_commit",
    "stateTracking": {
      "recordRollbackEvent": true,
      "maxRollbacksPerStage": 3,
      "escalateAfterMax": "human_intervention"
    }
  }
}
```

### 2.2 上下文窗口管理策略

**问题**：整个流水线涉及大量文档（clarification-notes、PRD、SDD、TASKS、bridge-spec、plan、tdd-plan、sections、review-report……），LLM 的上下文窗口不可能同时容纳所有内容。V2 没有讨论上下文管理。

**建议补充**：

每个阶段只加载与当前阶段相关的 artifacts：
- CLARIFY：只加载初始需求描述
- SPEC：加载 clarification-notes + decision-bundle
- PLAN：加载 bridge-spec（已压缩的 PRD/SDD/TASKS 精华）
- EXECUTE：只加载当前 section 的 section-*.md + claude-plan-tdd.md 中对应部分
- VERIFY：加载 plan 基线 + 全量 diff（不加载历史对话）
- DONE：加载 verification.json + delivery-summary 模板

原则：**每个阶段的输入是上一阶段的 artifacts，而非上一阶段的完整对话上下文。**

### 2.3 多特性并行管理

**问题**：V2 的状态机是单线程的（一个 feature 走完一条线）。但实际项目中经常需要多个 feature 并行推进。

**建议补充**：

状态文件应支持多特性隔离：

```text
.harness/
├── features/
│   ├── user-auth/
│   │   ├── state.json
│   │   └── artifacts/
│   ├── payment-flow/
│   │   ├── state.json
│   │   └── artifacts/
│   └── ...
└── global-config.json
```

每个 feature 有独立的状态机实例和 artifact 目录。harness 在 SessionStart 时根据当前上下文判断激活哪个 feature 的状态。

### 2.4 DISCOVER 阶段的定义

**问题**：V2 提到 `DISCOVER -> CLARIFY` 作为可选前置，但没有给出 DISCOVER 的目标、产物、门禁和工具。

**建议补充**：

| 项目 | 内容 |
|------|------|
| 目标 | 将过大/过模糊的目标拆分为可独立推进的 feature 单元 |
| 组件 | deep-project（或 Superpowers brainstorming 的扩展模式） |
| 输出 | `discovery-report.md`、`feature-list.json`（含依赖关系和优先级） |
| 出口条件 | 至少有一个 feature 已具备进入 CLARIFY 的条件 |
| 门禁 | 无正式议会；Decision Bundle 即可 |

### 2.5 人机交互协议

**问题**：V2 明确了 Decision Bundle 的数据格式，但没有说明人机交互的具体协议：人在哪里回答？用什么格式回答？超时怎么处理？

**建议补充**：

- **交互界面**：CLI 对话窗口（当前阶段门禁阻断后，以结构化消息展示 Decision Bundle）
- **回答格式**：JSON 或简化的选择式回答（`D-PLAN-01: A`）
- **超时策略**：设置最大等待时间（如 24 小时），超时后将状态标记为 `WAITING_HUMAN`，不自动推进
- **异步模式**：支持将 Decision Bundle 写入文件，人工修改后通过 `/harness-advance` 命令继续

### 2.6 成本监控与预算控制

**问题**：V2 提到"Token 与延迟失控"风险，但没有给出监控和控制手段。

**建议补充**：

- 在状态文件中记录每个阶段的 token 消耗估算
- 为议会设置 token 预算上限（如：轻议会 ≤ 50K tokens，计划议会 ≤ 150K tokens，验收议会 ≤ 200K tokens）
- 对低风险项目允许跳过某些议会（通过状态文件中的 `riskLevel` 字段控制）
- 提供 `harness-status` 命令展示累计消耗

### 2.7 崩溃恢复与会话断裂处理

**问题**：V2 在 Hooks 9.2 节提到 `SessionStart` 负责"加载状态、恢复阶段上下文"，但没有说明如果会话在 EXECUTE 中途断裂（如网络中断、token 耗尽），如何恢复。

**建议补充**：

- EXECUTE 阶段以 section 为恢复单元：每完成一个 section 的原子提交后，立即更新状态文件
- 恢复时从最后一个已完成 section 的下一个 section 开始
- 未完成的 section 应回滚 git 变更（`git reset` 到最后一次成功提交）
- PLAN/SPEC 等文档阶段以"最后一次成功 artifact 写入"为恢复点

### 2.8 MCP 配置策略

**问题**：`final-plan.md` 有明确的 MCP 配置优先级表，V2 没有保留。

**建议补充**：

| 优先级 | 配置位置 | 用途 |
|--------|---------|------|
| 1（最高） | stage-harness 插件的 `.mcp.json` 或 manifest `mcpServers` | harness 专属 MCP 工具 |
| 2 | 用户级 `~/.claude.json` | 全局凭据与通用工具 |
| 3 | 项目级配置 | 项目特定的 MCP 集成 |

推荐用途：
- PLAN 阶段：通过 MCP 拉取外部文档、技术调研
- DONE 阶段：通过 MCP 创建 PR、收集交付信息

---

## 三、建议补充（锦上添花）

### 3.1 度量与可观测性

建议在 DONE 阶段或持续运行中收集以下指标：
- 每阶段平均耗时
- 各议会的通过率（首次通过率 vs 总通过率）
- FIX 循环平均次数
- 每个 feature 的总 token 消耗
- Decision Bundle 的平均等待时间

这些指标可以反馈到 aio-reflect 的经验提炼中，驱动流程持续优化。

### 3.2 Git 分支模型与阶段的关系

建议明确：
- 每个 feature 一个分支（如 `feature/user-auth`）
- 每个 section 一个原子提交（由 deep-implement 控制）
- VERIFY 通过后合并到主干
- FIX 阶段在同一 feature 分支上追加提交

### 3.3 Harness 本身的测试策略

stage-harness 作为编排层，自身也需要测试：
- 状态机流转的单元测试
- 门禁脚本的集成测试（模拟各种 pass/fail 场景）
- 桥接脚本的转换测试（验证 ShipSpec 产物到 bridge-spec.md 的完整性）
- 端到端冒烟测试（用一个最小 feature 跑通全流程）

### 3.4 组件版本兼容性管理

外部组件（Superpowers、ShipSpec、deep-plan/implement、Ring、ECC）会持续演进。建议：
- 在 `plugin.json` 或 `global-config.json` 中锁定依赖组件的版本或 commit hash
- 升级时做兼容性测试（特别是 hooks 契约和 artifact 格式变化）
- 设置版本检查脚本，在 `SessionStart` 时验证依赖组件是否存在且版本匹配

### 3.5 安全层补强

`1.md` 中特别提到了安全风险（prompt injection、MCP 凭据外泄），V2 未充分覆盖：
- 对 MCP 输入输出做注入扫描
- 在 DONE 阶段的发布议会中加入"安全最终签署"（V2 已提到，但建议明确包含：依赖扫描、secret 检测、OWASP 基线检查）
- 对 hooks 脚本本身做安全审计（避免在 shell 脚本中执行未转义的外部输入）

---

## 四、总结

`final-plan-v2.md` 作为方案文档，在**战略层面**（PLAN 作为控制中心、分层议会模板）做了很好的收敛。但从**工程落地**角度，需要补充的核心内容主要集中在：

1. **组件能力裁剪清单**（防止职责越界）
2. **桥接技术规格**（防止链路断裂）
3. **两层审查模型**（防止审查冗余或盲区）
4. **Hooks 验证状态表**（防止基于未验证假设建门禁）
5. **插件目录结构**（给实施者一个起点）

这五项建议优先补充到 V2 中。其余项可以在 MVP 实施过程中逐步完善。

建议的文档关系定位：
- `final-plan-v2.md`：主版本方案文档（战略 + 架构 + 治理）
- 本补充文档：工程落地补充（裁剪 + 桥接 + 技术细节）
- `final-plan.md`：保留为详细参考（含完整的裁剪清单、插件结构等）
