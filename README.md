# ospsd-team-03
Team 3 Repository for Open Source &amp; Professional Software Development class Spring 2026

## Team Members
- ys4780	Yanka Sikder @yawnka
- fas6488	Farhen Shefa @farhen-shefa
- zz10803	Zunyu Zhang @zhangyushao0
- yk3183	Yusuke Katsuki @katsukii
- hr2712	Hyun Sang (Hayden) Ryu @hayden-hs

TA's:
- @adithyab-20
- @ivanearisty
- @AranyaAryaman

## What This Repo Provides

Two installable packages under `src/` using a `uv` workspace:

| Package | Purpose |
|---------|---------|
| `issue_tracker_client_api` | Provider-agnostic abstract interface (ABC) + DI hooks |
| `issue_tracker_client_impl` | Concrete implementation; reads token from `ISSUE_TRACKER_TOKEN` env var |

## Quickstart

```sh
uv sync             # install workspace + dev deps
uv run ruff check . # lint  (select = ALL)
uv run mypy .       # type-check (strict = true)
uv run pytest       # test + coverage
```

## How DI Works

Importing `issue_tracker_client_impl` auto-registers its factory into the API package:

```python
import issue_tracker_client_impl          # side-effect: registers DefaultIssueTrackerClient
from issue_tracker_client_api.client import get_client

client = get_client()                     # returns a DefaultIssueTrackerClient
```
