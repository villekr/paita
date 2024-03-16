# Development instructions

## Required tools
* Hatch - for packaging and publishing https://hatch.pypa.io

## PyCharm

When opening 'paita' in PyCharm do the following:
* Right click 'src'-folder and select 'Mark Directory as'->'Sources Root'
* Configure virtualenv:
  * `hatch env find default`
  * Set Python interpreter based on above path

Create environment:
```
hatch env create
```

Activate environment:
```
hatch shell
```

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
mypy src tests
```

Run tests
```
hatch run test
```

Run test with coverage
```
hatch run cov
```