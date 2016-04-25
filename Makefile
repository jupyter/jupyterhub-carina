default:
	@echo "Targets:"
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

test:
	python3 setup.py register -r pypitest
	python3 setup.py sdist bdist_wheel upload -r pypitest

publish: test
	python3 setup.py sdist bdist_wheel upload
