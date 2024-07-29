version=1.0.1

py = python3.9

echo 开始安装环境
${py} -m pip install -r requirements.txt
${py} -m pip install libsass==0.23.0

echo 开始构建前端
${py} mfb.py frontend -p tjs -p rjs -p sass --dist files 

echo 开始构建镜像

docker build -t fireflyench:${version} .