default: install

version_synced:
	[[ $$(grep -A1 '# version-marker' nvr/nvr.py | tail -n1 | grep -o '[0-9\.]\+') = $$(grep version setup.py | grep -o '[0-9\.]\+') ]]

install: version_synced
	python3 setup.py install

test:
	pytest -v tests

upload: clean version_synced
	python3 setup.py sdist bdist_wheel upload

clean:
	rm -rf build dist neovim_remote.egg-info

.PHONY: install test upload
