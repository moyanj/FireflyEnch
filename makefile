# Define variables
PYTHON = python3.9
VERSION = 1.2.2

# Define targets and dependencies
all: frontend docker

init:
	@echo 开始安装环境
	${PYTHON} -m pip install -r requirements.txt
	${PYTHON} -m pip install libsass==0.23.0

frontend: init
	${PYTHON} mfb.py frontend -p tjs -p rjs -p sass --dist files -d version=${VERSION} -d type=rel
	
docker:
	docker build -t fireflyench:${VERSION} .

run:
	gunicorn app:app
clean:
	rm -rf uploads/
	rm -rf db/
	rm -rf files/
	rm -rf .cache/
	rm -rf cache/
	rm -rf __pycache__/