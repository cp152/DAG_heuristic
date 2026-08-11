# DAG Heuristic Benchmark and Algorithms

本仓库研究不可抢占 DAG 通信调度，并提供语言无关的 benchmark。问题数据、数据生成和算法实现彼此分离：只想使用数据的开发者可以直接读取 `benchmark/*.json`，不需要安装 Python、SimAI 或本仓库算法。

## 调度场景

所有场景遵循相同基础语义：

- compute 和 communication 一旦开始就连续执行到完成；
- `dependencies` 是 finish-to-start 依赖；
- ready compute 自动开始，计算资源串行关系由 DAG 边表示；
- communication 在整个传输期间独占其 resource set；
- 调度器只在任务完成事件后决策，允许主动等待；
- 目标是最小化 makespan。

当前提供三类问题：

| 场景 | 含义 | 主要限制 |
|---|---|---|
| `single_channel/parallel_chain` | 多条计算—通信交替链共享一个 channel | 没有 fork/join |
| `single_channel/general_dag` | 任意 DAG 的通信共享一个 channel | compute 不竞争有限 GPU 资源 |
| `multi_channel/multi_resource_dag` | flow 可同时占用多个固定 link/NIC 资源 | 不联合选路，不模拟带宽比例共享 |

多通道中，resource set 不相交的 flow 可以并行。route 只在 benchmark 生成阶段计算；算法只处理文件中已经给出的资源集合。

## 仓库结构

```text
benchmark/
  SPECIFICATION.md                # 文件格式和调度语义
  schema/                         # JSON Schema
  index.jsonl                     # benchmark 索引和 SHA-256
  single_channel/
    parallel_chain/{random,adversarial,real}/
    general_dag/{random,adversarial,real}/
  multi_channel/
    multi_resource_dag/{random,adversarial,real}/
  reference_results/              # 与问题文件分离的最优值/参考结果

benchmark_generate/
  convert.py                      # 内部实例到标准文件的转换
  export_current.py               # 固定种子 suite 生成
  scenarios.py                    # 纯随机/攻击实例生成函数
  reference_results.py            # Exact Oracle sidecar 生成
  legacy_dag.py                   # 历史 fixture，仅供离线生成
  simai/                          # 可选 SimAI workload/topology adapter

src/dag_heuristic/
  benchmark/                      # 中立模型、Loader、Validator
  core/                           # 不可抢占状态机和 Exact Oracle
  algorithms/
    single_channel/parallel_chain/
    single_channel/general_dag/
    multi_channel/
  registry.py                     # 算法注册表
  cli.py                          # 文件驱动 CLI

tests/
  algorithms/                     # 算法回归
  core/                           # 状态机和 Oracle
  integration/                    # 可选 SimAI 集成
```

算法核心位于 `src/dag_heuristic`，禁止导入 SimAI 的 `src.*`、旧包路径或修改 `sys.path`。该约束有自动测试。

## Benchmark 格式

每个实例是 UTF-8 JSON。完整定义见 [benchmark/SPECIFICATION.md](benchmark/SPECIFICATION.md)，机器可读约束见 [dag-benchmark-v1.schema.json](benchmark/schema/dag-benchmark-v1.schema.json)。

最小示例：

```json
{
  "schema_version": "1.0",
  "id": "two_flows",
  "scenario": "single_channel",
  "family": "general_dag",
  "category": "adversarial",
  "objective": "makespan",
  "time_unit": "tick",
  "semantics": {
    "preemptive": false,
    "decision_epoch": "task_completion",
    "optional_idle": true,
    "compute_model": "unbounded_parallel",
    "resource_model": "exclusive"
  },
  "resources": [{"id": "channel:0", "kind": "channel"}],
  "tasks": [
    {
      "id": "flow0",
      "kind": "communication",
      "duration": 3,
      "dependencies": [],
      "resources": ["channel:0"]
    }
  ]
}
```

C++ 实现只需按照 specification 解析 JSON，并完成 ID 唯一性、依赖存在性、无环和 resource 引用检查。Python Loader 不是格式定义本身。

## 安装与运行

在独立仓库根目录安装：

```powershell
python -m pip install -e ".[dev]"
```

直接运行一个文件：

```powershell
dag-heuristic benchmark/single_channel/parallel_chain/adversarial/tight_optional_wait_m20.json `
  --algorithm longest_tail
```

未安装命令行入口时：

```powershell
python -m dag_heuristic benchmark/multi_channel/multi_resource_dag/adversarial/nonmaximal_start_np.json `
  --algorithm rollout_optional2
```

列出适用于某个实例的算法：

```powershell
python -m dag_heuristic path/to/case.json --list-algorithms
```

Python 中加载：

```python
from dag_heuristic.benchmark import load_benchmark

benchmark = load_benchmark("benchmark/example.json")
```

## 生成 Benchmark

随机、攻击和结构样例由离线生成器产生，算法运行时不调用生成器：

```powershell
python -m benchmark_generate all --samples 10 --seed 260819 --output benchmark
```

为小型攻击实例更新 Exact Oracle sidecar：

```powershell
python -m benchmark_generate reference --output benchmark
```

生成器采用稳定序列化，记录 seed 和参数，并更新 `index.jsonl` 与 SHA-256。已发布 benchmark 应提交到 Git，保证 Python/C++ 使用完全相同的问题。

问题文件不保存算法答案。Exact Oracle 和 baseline 结果写入 `benchmark/reference_results/`，并通过 benchmark ID 和 SHA-256 关联。

## SimAI 集成与 Submodule

`benchmark_generate/simai/` 是唯一允许依赖 SimAI 的区域，用于：

- AICB workload 和 pipeline DAG 展开；
- effective DAG 审计；
- BFS route 与 link/NIC resource 转换；
- 生成可提交的真实派生 JSON snapshot。

独立仓库创建后，SimAI 固定在：

```text
third_party/simai-flow-scheduler/
```

初始化方式：

```bash
git submodule update --init --recursive
```

路径发现顺序为：

1. 环境变量 `SIMAI_FLOW_SCHEDULER_ROOT`；
2. `third_party/simai-flow-scheduler`；
3. 当前嵌套开发阶段的父仓库。

未初始化 SimAI 时，Loader、静态 benchmark 和全部核心算法仍必须正常工作。只有 `tests/integration/` 和 `benchmark_generate.simai` 需要 SimAI。

## 扩展算法

1. 在对应 `src/dag_heuristic/algorithms/` 目录实现算法。
2. 输入使用公开 `Benchmark`，或通过 `core/conversion.py` 转成场景内部状态。
3. 返回结果必须公开整数 `makespan`；建议同时提供动作和任务时间线。
4. 在 `registry.py` 注册名称、场景、family、WAIT 和 exact 能力。
5. 添加一个能区分新算法和已有 baseline 的固定测试。
6. 若算法针对某类反例，将问题文件加入 `benchmark/**/adversarial/`。
7. 理论近似比必须附证明；有限样本最坏值不能写成理论保证。

算法不得读取 benchmark metadata 来获得答案，也不得导入 `benchmark_generate` 或 SimAI。

## 扩展 Benchmark Generator

新增生成器时必须：

- 接受显式 seed 和输出目录；
- 记录来源、生成参数和版本；
- 输出后通过公共 Validator；
- 保证同版本、同 seed、同参数逐字节可复现；
- 将 route、带宽和 workload 语义完全投影到标准 task/resource 字段；
- 不把私有 workload 或大型输入提交到仓库。

真实 SimAI 转换放入 `benchmark_generate/simai/`；纯随机和攻击生成器不能导入 SimAI。

## 测试

核心与当前可用集成测试：

```powershell
python -m pytest -q
```

当前基线：

```text
45 standalone tests
54 tests when the SimAI integration checkout is available
57 benchmark JSON files validated
15 adversarial instances have exact reference results
```

发布独立仓库前还应在未初始化 submodule 的干净环境中运行核心测试，并在递归 clone 的 CI job 中单独运行 `tests/integration/`。

研究过程、理论证明和反例说明保存在 `docs/`。其中部分历史段落引用迁移前路径，应以本 README 和当前代码结构为准。
