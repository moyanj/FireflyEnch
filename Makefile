VERSION = $(shell cat VERSION)

# Define targets and dependencies
all: frontend docker

init:
	@echo 开始安装环境
	uv sync
	cd frontend && pnpm i

frontend: init
	pnpm -C frontend run build

docker:
	docker build -t fireflyench:${VERSION} .

run:
	uv run app.py

clean:
	rm -rf uploads/
	rm -rf db/
	rm -rf files/
	rm -rf .cache/
	rm -rf cache/
	rm -rf __pycache__/
	rm -rf .venv/
	rm -rf fireflyench.egg-info/
