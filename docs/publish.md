# Publish process to test.pypi.org and pypi.org

## test.pypi.org

* add repository to poetry config `poetry config repositories.test-pypi https://test.pypi.org/legacy/`
* get token from https://test.pypi.org/manage/account/token/
* store token using poetry config pypi-token.test-pypi  pypi-YYYYYYYY

Note: 'test-pypi' is the name of the 'repository' aka 'index' to publish to.

## pypi.org

* get token from https://pypi.org/manage/account/token/
* store token using `poetry config pypi-token.pypi pypi-XXXXXXXX`

## Poetry Publish

### test.pypi.org

```
poetry version prerelease
poetry publish -r test-pypi
```

### pypi.org

```
poetry version patch
poetry publish
```
