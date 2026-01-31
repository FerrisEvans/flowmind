# Plan 校验设计：输入 / 输出与校验规则

本文档定义对 Planner 产出的 **Structured Plan**（符合 `plan.dsl.yaml`）进行校验的输入、输出与规则，便于在 Executor 执行前发现格式错误与语义错误。

---

## 1. 输入（Validator Input）

| 名称 | 类型 | 说明 |
|------|------|------|
| **plan_doc** | `object` | 解析后的 Plan 文档（来自 YAML/JSON），结构需符合 `plan.dsl.yaml`。 |
| **atoms_registry** | `object` 或 `list` | 当前可用的原子服务注册表，用于校验 `step.id` 及 input/output 字段。建议结构：`{ "<atom_id>": <atom_def> }` 或由 `atoms/*.json` 合并得到的 atom 列表（每个元素含 `id`、`inputs`、`outputs` 等）。 |

- **plan_doc** 根结构示例：
  - `target`: string（用户意图摘要）
  - `plan`: object
    - `plan.steps`: array of step
    - `plan.outputs`: object（可选，最终展示给用户的结果）
- 每个 **step** 需含：`id`（atom id）、`target`、`inputs`；可选：`step_id`、`depends_on`。

---

## 2. 输出（Validator Output）

校验结果统一为结构化对象，便于调用方解析与展示。

### 2.1 成功时

```json
{
  "valid": true,
  "warnings": [
    { "code": "UNUSED_STEP_OUTPUT", "message": "...", "path": "plan.steps[1]" }
  ],
  "execution_order": ["step_1", "step_2"]
}
```

- **valid**: `true`
- **warnings**: 可选，非阻塞性提示（如某 step 的 output 未被引用）。可为空数组。
- **execution_order**: 可选，按依赖关系拓扑排序后的 `step_id` 列表（无 `step_id` 时用 step 在数组中的下标，如 `"0"`, `"1"`）。供 Executor 使用。

### 2.2 失败时

```json
{
  "valid": false,
  "errors": [
    {
      "code": "UNKNOWN_ATOM_ID",
      "message": "Unknown atom id: xxx",
      "path": "plan.steps[2].id"
    },
    {
      "code": "MISSING_REQUIRED_INPUT",
      "message": "Required input 'user_id' is missing",
      "path": "plan.steps[0].inputs"
    }
  ]
}
```

- **valid**: `false`
- **errors**: 至少一条错误；每条包含：
  - **code**: 错误码（见下表）
  - **message**: 人类可读描述
  - **path**: 出错字段路径（如 `plan.steps[1].inputs.file_path`），便于定位。

---

## 3. 校验规则（Validation Rules）

按执行顺序列出；一旦某条不通过即可记录错误并继续检查其余规则（或短路返回，由实现决定）。

### 3.1 结构与类型（Schema）

| 规则 ID | 检查项 | 错误码 | 说明 |
|---------|--------|--------|------|
| S1 | 根对象含 `target`（string） | `MISSING_FIELD` / `INVALID_TYPE` | 必填。 |
| S2 | 根对象含 `plan`（object） | `MISSING_FIELD` / `INVALID_TYPE` | 必填。 |
| S3 | `plan.steps` 存在且为**非空数组** | `MISSING_FIELD` / `INVALID_TYPE` / `EMPTY_STEPS` | 至少一个 step。 |
| S4 | 每个 step 为 object，且含 `id`（string）、`target`（string）、`inputs`（object） | `MISSING_FIELD` / `INVALID_TYPE` | `inputs` 可为空对象 `{}`。 |
| S5 | 若 step 含 `step_id`，则为非空 string | `INVALID_TYPE` / `EMPTY_STEP_ID` | 可选字段。 |
| S6 | 若 step 含 `depends_on`，则为 string 数组 | `INVALID_TYPE` | 可选；元素为 step 的 `step_id`（或见下文「step 标识」约定）。 |
| S7 | 若存在 `plan.outputs`，则为 object | `INVALID_TYPE` | 可选；仅做类型校验。 |

**step 标识约定**：在 `depends_on` 与输入引用（`${step_id.outputs.xxx}`）中，若某 step 显式写了 `step_id`，则用该值；若未写，则用该 step 在 `plan.steps` 中的**下标**（转为 string，如 `"0"`, `"1"`）。校验时需统一：同一 plan 内不能有两个 step 使用相同的有效标识（显式 `step_id` 不得重复；隐式下标天然唯一）。

### 3.2 step_id 唯一性

| 规则 ID | 检查项 | 错误码 | 说明 |
|---------|--------|--------|------|
| U1 | 所有显式 `step_id` 两两不同 | `DUPLICATE_STEP_ID` | 若存在重复，报错并指出重复的 `step_id`。 |

### 3.3 原子服务引用（Atom Registry）

| 规则 ID | 检查项 | 错误码 | 说明 |
|---------|--------|--------|------|
| A1 | 每个 `step.id` 均存在于 `atoms_registry` | `UNKNOWN_ATOM_ID` | 精确匹配 atom 的 `id` 字段。 |
| A2 | 每个 step 的 `inputs` 的 **key** 必须出现在对应 atom 定义的 `inputs` 中 | `UNKNOWN_INPUT_FIELD` | 不允许 atom 未声明的 input 字段。 |
| A3 | 对 atom 中 `required: true` 的 input，该 step 的 `inputs` 中必须有对应 key，且 value 非 null/未定义 | `MISSING_REQUIRED_INPUT` | value 可以是字面量或引用字符串（如 `${step_id.outputs.xxx}`）。 |

### 3.4 输入引用（Reference Resolution）

对每个 step 的每个 input value，若为**引用**（如 `${step_id.outputs.output_name}` 或约定格式）：

| 规则 ID | 检查项 | 错误码 | 说明 |
|---------|--------|--------|------|
| R1 | 引用中的 `step_id` 必须对应本 plan 内某个 step 的有效标识 | `UNKNOWN_STEP_REF` | 即该 step 的显式 `step_id` 或下标。 |
| R2 | 引用中的 `output_name` 必须在该 step 对应 atom 的 `outputs` 中存在 | `UNKNOWN_OUTPUT_FIELD` | 按 atom 定义的 `outputs[].name` 校验。 |
| R3 | 被引用 step 必须在**拓扑序**上位于当前 step 之前（即当前 step 直接或间接依赖该 step） | `REF_BEFORE_DEPENDENCY` | 保证执行时上游 output 已存在。若未显式 `depends_on`，则按引用隐式建立依赖后再做拓扑校验。 |

引用格式建议：统一为 `${step_id.outputs.output_name}`，解析时用正则或简单 parser 提取 `step_id` 与 `output_name`。其他格式可后续扩展并在此补充。

### 3.5 依赖图（depends_on）

| 规则 ID | 检查项 | 错误码 | 说明 |
|---------|--------|--------|------|
| D1 | `depends_on` 中每个元素必须是本 plan 内某 step 的有效标识 | `UNKNOWN_DEPENDENCY` | 同「step 标识约定」。 |
| D2 | 依赖图无环（从 steps 与 depends_on 构建有向图，做拓扑排序；若存在环则失败） | `CIRCULAR_DEPENDENCY` | 报错时可列出参与环的 step 标识。 |

### 3.6 可选：outputs 与执行顺序

- **plan.outputs**：当前仅做类型校验（S7）；是否要求其 key 来自某 step 的 output 可留作后续扩展。
- **execution_order**：校验通过后，由 `depends_on`（及引用隐式依赖）构建 DAG，做拓扑排序得到 `execution_order`，写入成功时的输出，供 Executor 使用。

---

## 4. 错误码汇总

| 错误码 | 含义 |
|--------|------|
| `MISSING_FIELD` | 缺少必填字段 |
| `INVALID_TYPE` | 类型不符合（如应为 string 却是 number） |
| `EMPTY_STEPS` | `plan.steps` 为空 |
| `EMPTY_STEP_ID` | `step_id` 为空字符串 |
| `DUPLICATE_STEP_ID` | 重复的 step_id |
| `UNKNOWN_ATOM_ID` | step.id 不在 atoms 注册表中 |
| `UNKNOWN_INPUT_FIELD` | input 的 key 在 atom 中未定义 |
| `MISSING_REQUIRED_INPUT` | 必填 input 缺失或值为空 |
| `UNKNOWN_STEP_REF` | 引用中的 step_id 不存在 |
| `UNKNOWN_OUTPUT_FIELD` | 引用中的 output 在对应 atom 中不存在 |
| `REF_BEFORE_DEPENDENCY` | 引用的 step 未在依赖链前序 |
| `UNKNOWN_DEPENDENCY` | depends_on 中的标识不存在 |
| `CIRCULAR_DEPENDENCY` | 依赖图存在环 |

---

## 5. 校验顺序建议

1. **Schema（S1–S7）**：先做结构和类型，避免后续访问未定义字段。
2. **U1**：step_id 唯一性。
3. **A1–A3**：atom 存在性与 input 合法性。
4. **R1–R3**：解析所有引用并校验 step_id、output_name、依赖顺序（可与 D 一起做图分析）。
5. **D1–D2**：构建依赖图，校验 depends_on 引用与无环；同时可计算 execution_order。

实现时可在第一次遇到错误时短路返回，也可收集同一类错误再返回，视需求而定。
