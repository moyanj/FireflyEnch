version=1.0.0

echo 开始安装环境
pip install -r requirements.txt
pip install libsass==0.23.0

echo 开始构建前端
python mfb.py frontend -p tjs -p rjs -p sass --dist files 

echo 开始构建镜像

docker build -t fireflyench:${version} .