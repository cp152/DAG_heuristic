# Benchmark generators

生成器只负责离线产生 `benchmark/` 中的语言无关 JSON。算法评测读取已生成文件，不在运行时调用这些函数。

在独立仓库根目录、安装本项目后运行：

```powershell
python -m benchmark_generate all --samples 10 --seed 260819
```

`simai/` 将保存依赖 SimAI submodule 的 workload、pipeline 和 topology 转换；其它生成器必须保持无 SimAI 依赖。
