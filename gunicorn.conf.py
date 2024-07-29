import multiprocessing
import gevent.monkey

gevent.monkey.patch_all()

cpu_count = multiprocessing.cpu_count()
bind = "0.0.0.0:8896"

workers = 2 * cpu_count + 1
threads = int(1.5 * cpu_count)

loglevel = "info"

worker_connections = 2500
worker_class = "gunicorn.workers.ggevent.GeventWorker"

x_forwarded_for_header = "X-FORWARDED-FOR"
preload_app = True

pidfile = "gunicorn.pid"
# 设置访问日志和错误信息日志路径
errorlog = "-"
max_requests = 2500