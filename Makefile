# Define variables
PYTHON = python3
VERSION = 2.4.6

# Define targets and dependencies
all: frontend docker

init:
	@echo 开始安装环境
	uv sync

frontend: init
	uv run python mfb.py frontend -p tjs -p rjs --dist files -d version=${VERSION} -d type=rel

docker:
	docker build -t fireflyench:${VERSION} .

run:
	uv run python app.py

clean:
	rm -rf uploads/
	rm -rf db/
	rm -rf files/
	rm -rf .cache/
	rm -rf cache/
	rm -rf __pycache__/
	rm -rf .venv/
	rm -rf fireflyench.egg-info/
