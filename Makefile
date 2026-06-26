VERSION = $(shell cat VERSION)

# Define targets and dependencies
all: docker

init:
	@echo 开始安装环境
	uv sync
	cd frontend && pnpm i

frontend:
	pnpm -C frontend run build

docker:
	docker build -t fireflyench:${VERSION} .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

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
