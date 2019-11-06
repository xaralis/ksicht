
#!/bin/sh

# Create log dirs and files
mkdir -p $( dirname $(cat /etc/supervisor/conf.d/supervisor.conf | grep logfile= | grep "\.log" | sed s/.*logfile=// ) )
touch $( cat /etc/supervisor/conf.d/supervisor.conf | grep logfile= | grep "\.log" | sed s/.*logfile=// )

export WORKERS=${WORKERS:-2}
export WORKER_TIMEOUT=${WORKER_TIMEOUT:-60}
export WORKER_CLASS=${WORKER_CLASS:-sync}
export WORKER_NAME=${WORKER_NAME:-ksicht-worker}
export WORKER_MAX_REQUESTS=${WORKER_MAX_REQUESTS:-0}
export WORKER_LOG_LEVEL=${WORKER_LOG_LEVEL:-info}

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisor.conf --nodaemon
