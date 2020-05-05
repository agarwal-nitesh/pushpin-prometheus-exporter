### pushpin-metrics
Pushpin prometheus metrics exporter

####
Push metrics to pushgateway and scrape using prometheus

### Installation

#### pushpin-metrics
```bash
pyenv global 3.8.2
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
``` 

#### run service
```bash
python metrics_push.py
```

#### prom config
```
- job_name: prometheus_pushgateway
    scrape_interval: 10s
    metrics_path: /metrics
    honor_labels: true
    static_configs:
      - targets: ['localhost:9091']
```
