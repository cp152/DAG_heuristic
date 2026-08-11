# DAG Benchmark Format v1

本目录保存与编程语言无关的调度问题实例。每个 `*.json` 文件描述一个完整 DAG；算法不得依赖生成该文件的 Python 代码。

## 1. 调度语义

- 所有任务均为不可抢占任务，开始后必须运行到完成。
- `dependencies` 表示 finish-to-start 依赖，所有前驱完成后任务才 ready。
- `compute` 任务不竞争有限计算资源，ready 后立即开始；GPU 串行关系应显式编码为依赖边。
- `communication` 任务在运行期间独占其 `resources` 中的全部资源。
- resource set 不相交的通信可以并行运行。
- 调度器只在任务完成事件后作出新决策，可以主动等待。
- 目标固定为最小化 DAG makespan。
- 时间采用非负整数 tick；通信时长必须为正，计算时长可以为零。

单通道不是独立的执行模型：它只是所有通信任务都使用唯一资源 `channel:0`。多通道任务可以声明多个 link、NIC 或其它排他资源。

## 2. 顶层字段

| 字段 | 类型 | 必需 | 含义 |
|---|---|---:|---|
| `schema_version` | string | 是 | 当前固定为 `1.0` |
| `id` | string | 是 | 仓库内稳定且唯一的实例 ID |
| `scenario` | string | 是 | `single_channel` 或 `multi_channel` |
| `family` | string | 是 | `parallel_chain`、`general_dag` 或 `multi_resource_dag` |
| `category` | string | 是 | `random`、`adversarial` 或 `real` |
| `objective` | string | 是 | 当前固定为 `makespan` |
| `time_unit` | string | 是 | 通常为 `tick`，也可记录 `us` |
| `semantics` | object | 是 | 执行语义；v1 的取值由 Schema 固定 |
| `resources` | array | 是 | 可被通信任务独占的资源 |
| `tasks` | array | 是 | DAG 节点 |
| `metadata` | object | 否 | 来源、seed、生成参数等非语义信息 |

未知顶层字段不允许出现。扩展格式必须提高 `schema_version`。

## 3. Resource

```json
{"id": "channel:0", "kind": "channel"}
```

`id` 是非空字符串并在实例内唯一。算法必须把 ID 当作不透明字符串；`kind` 仅用于分析和展示，不改变排他语义。

## 4. Task

```json
{
  "id": "flow_0",
  "kind": "communication",
  "duration": 5,
  "dependencies": ["release_0"],
  "resources": ["channel:0"],
  "metadata": {"role": "pp"}
}
```

- `id` 在实例内唯一。
- `kind` 为 `compute` 或 `communication`。
- `duration` 为整数；communication 必须大于零，compute 可以为零。
- `dependencies` 中的 ID 必须存在，不能包含自身、重复项或形成环。
- compute 的 `resources` 必须为空。
- communication 必须至少声明一个已定义资源，且不能重复。

## 5. 场景附加约束

### single_channel

- resources 必须恰好包含 `channel:0`；
- 每个 communication 的 resources 必须恰好为 `["channel:0"]`。

### parallel_chain

- 每个节点的入度和出度均不超过 1；
- 每个弱连通分量是一条 compute/communication 交替链；
- 该约束用于识别可使用紧凑并行链算法的实例。

### multi_channel

- 可以定义任意数量的排他资源；
- 一个 communication 可以同时占用多个资源；
- route 只作为生成阶段的概念，算法以文件中的 resource set 为准，不重新选路。

## 6. Benchmark 与答案分离

问题文件不保存算法结果。精确最优值和基线结果放在 `benchmark/reference_results/`，并通过 `benchmark_id` 和问题文件 SHA-256 关联，防止修改问题后继续误用旧答案。

`benchmark/index.jsonl` 每行是一个 JSON object，至少包含 `id`、`path`、`scenario`、`family`、`category` 和 `sha256`。

## 7. 兼容性

- v1 reader 必须拒绝未知 major version。
- 新增可选 metadata 不需要提高 major version。
- 改变调度语义、必需字段或资源含义必须发布新 major version。
- JSON 文件使用 UTF-8、LF 和稳定 key 排序；ID 的比较区分大小写。

机器可读约束见 `schema/dag-benchmark-v1.schema.json`。JSON Schema 不能表达的 DAG 无环和 family 结构约束由 loader 的语义校验完成。
