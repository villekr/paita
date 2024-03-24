# Publish process to test.pypi.org and pypi.org

## Version

Check the current version:
```
hatch version
```

Increment version:
```
hatch version <major|minor|patch>
```

Create a new branch with a name from new version:
```
git checkout -b release-<version>
```

## Build

```
hatch build
```

## Publish

```
hatch publish -u __token__ -a <auth-token> -r <test|main>
```

You can configure repository and authentication also using the following env variables:
* HATCH_INDEX_REPO
* HATCH_INDEX_USER
* HATCH_INDEX_AUTH