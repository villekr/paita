# Development instructions

## Required tools
* Hatch - for packaging and publishing https://hatch.pypa.io

## Basic hatch commands

Create (default) environment:
```
hatch env create
```

Activate (default) environment:
```
hatch shell
```

## PyCharm

When opening 'paita' in PyCharm do the following:
* Right click 'src'-folder and select 'Mark Directory as'->'Sources Root'
* Configure virtualenv:
  * Find virtual environment path: `hatch env find default` or `hatch env find <env>` e.g `hatch env find all.py3.12`
  * Set Python interpreter based on above path + `/bin/python`

## Other hatch commands

Activate (specific version) environment:
```
hatch -e <env> shell
```

where env is one of the envs listed by `hatch env show` command.

Run paita application:
```
python -m paita.tui.app
```

Debugging requires textual console on **separate terminal** window/tab:
```
hatch run textual console
```

Run paita application in dev-mode:
```
hatch run textual run src/paita/tui/app.py --dev
```

Run formatter and linter:
```
hatch fmt
```

Run type checker:
```
hatch run mypy src tests
```

Run tests for current (default) env
```
hatch run test
```

Run tests for all configured envs
```
hatch run all:test
```

Run test with coverage
```
hatch run cov
```