# SimAI integration

这里的代码可以依赖 `third_party/simai-flow-scheduler`，但生成出的 JSON 必须符合 `benchmark/SPECIFICATION.md`。核心 loader 和算法不得导入本模块。

当 `DAG_heuristic` 提取为独立仓库后，在 `third_party/simai-flow-scheduler` 固定 SimAI submodule commit。当前嵌套开发状态直接使用父仓库，仅作为迁移过渡。
