# gunicorn配置文件
import multiprocessing

# 服务器套接字绑定
bind = "0.0.0.0:8000"

# Worker进程数，通常设置为CPU核心数或CPU核心数+1
workers = multiprocessing.cpu_count() + 1

# Worker类型，使用uvicorn的worker类
worker_class = "uvicorn.workers.UvicornWorker"

# Worker进程的最大请求数，达到后会重启worker，防止内存泄漏
max_requests = 1000
max_requests_jitter = 100

# Worker超时时间（秒）
timeout = 300

# 保持连接的秒数
keepalive = 5

# 优雅地关闭worker的超时时间
graceful_timeout = 30

# Worker临时目录
worker_tmp_dir = "/dev/shm"

# 日志级别
loglevel = "info"

# 访问日志和错误日志
accesslog = "-"
errorlog = "-"

# 是否启用访问日志
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 后台运行时的PID文件
pidfile = "/tmp/gunicorn.pid"

# 后台运行时的工作目录
# daemon = True

# Worker进程名前缀
proc_name = "duplication_checker"