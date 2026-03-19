.PHONY: install test run clean

install:
	pip install -e .
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	python3 -m unittest discover tests

run:
	python3 src/mansur_bot/bot.py

clean:
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -exec rm -rf {} +
