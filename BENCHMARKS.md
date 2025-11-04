# Benchmarks

This document benchmarks diffhouse against [PyDriller](https://github.com/ishepard/pydriller), a popular Python-based repository mining tool. Benchmarks were run with [pyperf](https://pyperf.readthedocs.io/en/latest/) on GitHub Actions runners running Ubuntu 24.04.

Please note the following caveats:

- Repositories vary greatly in content and structure, so these benchmarks are intended as general performance indicators rather than definitive results.
- Each run executes `git clone`, so runtimes may fluctuate due to network speed and can introduce additional sampling noise.

In all charts, **lower is better**.

## Mid-Sized Repositories[^1]

We used the 1,000-commit tween.js repo as a representative case. diffhouse was **2x+ faster** overall; commit extraction took about **75% less time** than PyDriller.

<p align="center">
  <img src="https://raw.githubusercontent.com/vupdivup/diffhouse/assets/benchmarks/benchmark_tweenjs.png" alt="tweenjs/tween.js benchmark results" width="480px">
  <br/>
  <em><a href="https://github.com/tweenjs/tween.js">tweenjs/tween.js</a></em>
</p>

## Large Codebases[^2]

For the repo with ~10k commits, PyDriller slowed down significantly, while diffhouse kept a good pace, leading to **major runtime improvements**.

<p align="center">
  <img src="https://raw.githubusercontent.com/vupdivup/diffhouse/assets/benchmarks/benchmark_scrapy.png" alt="scrapy/scrapy benchmark results" width="480px">
  <br/>
  <em><a href="https://github.com/scrapy/scrapy">scrapy/scrapy</a></em>
</p>

## Binary Stores[^3]

For repositories with lots of binary content, the gap narrowed; the speedup gained via diffhouse was **less than 2x**.

<p align="center">
  <img src="https://raw.githubusercontent.com/vupdivup/diffhouse/assets/benchmarks/benchmark_sqlflow_public.png" alt="sqlparser/sqlflow_public benchmark results" width="480px">
  <br/>
  <em><a href="https://github.com/sqlparser/sqlflow_public">sqlparser/sqlflow_public</a></em>
</p>

## Tiny Projects[^4]

Small repos finish in a few seconds with either tool; PyDriller is still slower, but only slightly.

<p align="center">
  <img src="https://raw.githubusercontent.com/vupdivup/diffhouse/assets/benchmarks/benchmark_detours.png" alt="microsoft/Detours benchmark results" width="480px">
  <br/>
  <em><a href="https://github.com/microsoft/Detours">microsoft/Detours</a></em>
</p>

[^1]: [tweenjs/tween.js benchmark run](https://github.com/vupdivup/diffhouse/actions/runs/19018335542/job/54309480583)
[^2]: [scrapy/scrapy benchmark run](https://github.com/vupdivup/diffhouse/actions/runs/19018542074)
[^3]: [sqlparser/sqlflow_public benchmark run](https://github.com/vupdivup/diffhouse/actions/runs/19026625465/job/54331411177)
[^4]: [microsoft/Detours benchmark run](https://github.com/vupdivup/diffhouse/actions/runs/19026510189/job/54331102684)
