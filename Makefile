# Define variables
PYTHON = python3.9
VERSION = 2.4.3

# Define targets and dependencies
all: frontend docker

init:
	@echo 开始安装环境
	${PYTHON} -m pip install -r requirements.txt
	${PYTHON} -m pip install -r req.txt
	
frontend: init
	${PYTHON} mfb.py frontend -p tjs -p rjs --dist files -d version=${VERSION} -d type=rel
	
docker:
	docker build -t fireflyench:${VERSION} .

run:
	${PYTHON} app.py
	
clean:
	rm -rf uploads/
	rm -rf db/
	rm -rf files/
	rm -rf .cache/
	rm -rf cache/
	rm -rf __pycache__/