PYTHON ?= python3

.PHONY: test run examples

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) src/main.py $(ARGS)

examples:
	mkdir -p build
	$(PYTHON) src/main.py -i examples/web_server.conf -o build/web_server.xml
	$(PYTHON) src/main.py -i examples/game_level.conf -o build/game_level.xml
	$(PYTHON) src/main.py -i examples/pendulum_lab.conf -o build/pendulum_lab.xml
