# Deployment Strategy & Production Guide

## Executive Summary

This document outlines comprehensive deployment strategies for the Self-Evolving CLI Platform, covering development, staging, and production environments. It includes containerization, orchestration, monitoring, and scaling strategies for enterprise AGI platform deployment.

## Deployment Architecture Overview

### Multi-Environment Strategy
```
Development → Testing → Staging → Production
     ↓           ↓        ↓          ↓
Local Dev → CI/CD → Pre-Prod → Live System
     ↓           ↓        ↓          ↓
   Docker → Kubernetes → Monitoring → Scaling
```

### Infrastructure Components
- **Container Runtime**: Docker/Podman
- **Orchestration**: Kubernetes
- **Service Mesh**: Istio (optional)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Caching**: Redis Cluster
- **Database**: PostgreSQL (for metadata)
- **Load Balancer**: NGINX/HAProxy

## Containerization Strategy

### 1. Multi-Stage Docker Builds

#### Python Implementation Dockerfile
```dockerfile
# Dockerfile.python
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy application code
COPY --chown=app:app . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import src.cli; print('OK')" || exit 1

# Default command
CMD ["python", "main.py", "--help"]
```

#### C++ Implementation Dockerfile
```dockerfile
# Dockerfile.cpp
FROM gcc:11 as builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy source code
COPY cpp_cli_tools/ .

# Build application
WORKDIR /build/cli11_demo
RUN ./build.sh

# Production stage
FROM debian:bullseye-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy built binary
COPY --from=builder /build/cli11_demo/build/cli_demo ./cli_demo
COPY --from=builder /build/cli11_demo/config_example.txt ./config_example.txt

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ./cli_demo --help || exit 1

# Default command
CMD ["./cli_demo", "--help"]
```

### 2. Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  cli-python:
    build:
      context: .
      dockerfile: Dockerfile.python
    volumes:
      - ./src:/home/app/src:ro
      - ./config:/home/app/config:ro
      - cli-data:/home/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    networks:
      - cli-network

  cli-cpp:
    build:
      context: .
      dockerfile: Dockerfile.cpp
    volumes:
      - cli-data:/home/app/data
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - cli-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - cli-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=cli_platform
      - POSTGRES_USER=cli_user
      - POSTGRES_PASSWORD=cli_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - cli-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - cli-python
      - cli-cpp
    networks:
      - cli-network

volumes:
  cli-data:
  redis-data:
  postgres-data:

networks:
  cli-network:
    driver: bridge
```

## Kubernetes Deployment

### 1. Namespace and ConfigMaps
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cli-platform
  labels:
    name: cli-platform
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cli-config
  namespace: cli-platform
data:
  config.yaml: |
    version: "1.0.0"
    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.7
      timeout: 30
    validation:
      enabled: true
      strict_mode: true
    security:
      sandbox_enabled: true
      max_execution_time: 60
    redis:
      host: "redis-service"
      port: 6379
    postgres:
      host: "postgres-service"
      port: 5432
      database: "cli_platform"
```

### 2. Deployments
```yaml
# k8s/deployment-python.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cli-python
  namespace: cli-platform
  labels:
    app: cli-python
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cli-python
  template:
    metadata:
      labels:
        app: cli-python
        version: v1
    spec:
      containers:
      - name: cli-python
        image: cli-platform/python:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-api-key
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: POSTGRES_URL
          value: "postgresql://cli_user:cli_password@postgres-service:5432/cli_platform"
        volumeMounts:
        - name: config-volume
          mountPath: /home/app/config
        - name: data-volume
          mountPath: /home/app/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: cli-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: cli-data-pvc

---
# k8s/deployment-cpp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cli-cpp
  namespace: cli-platform
  labels:
    app: cli-cpp
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cli-cpp
  template:
    metadata:
      labels:
        app: cli-cpp
        version: v1
    spec:
      containers:
      - name: cli-cpp
        image: cli-platform/cpp:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        volumeMounts:
        - name: data-volume
          mountPath: /home/app/data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          exec:
            command:
            - ./cli_demo
            - --help
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - ./cli_demo
            - status
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: cli-data-pvc
```

### 3. Services and Ingress
```yaml
# k8s/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: cli-python-service
  namespace: cli-platform
spec:
  selector:
    app: cli-python
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: cli-cpp-service
  namespace: cli-platform
spec:
  selector:
    app: cli-cpp
  ports:
  - port: 80
    targetPort: 8001
    protocol: TCP
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cli-platform-ingress
  namespace: cli-platform
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - cli.yourdomain.com
    secretName: cli-platform-tls
  rules:
  - host: cli.yourdomain.com
    http:
      paths:
      - path: /python
        pathType: Prefix
        backend:
          service:
            name: cli-python-service
            port:
              number: 80
      - path: /cpp
        pathType: Prefix
        backend:
          service:
            name: cli-cpp-service
            port:
              number: 80
```

## CI/CD Pipeline

### 1. GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy CLI Platform

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME_PYTHON: ${{ github.repository }}/python
  IMAGE_NAME_CPP: ${{ github.repository }}/cpp

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov
    
    - name: Run Python tests
      run: |
        pytest tests/ --cov=src/ --cov-report=xml
    
    - name: Set up C++
      run: |
        sudo apt-get update
        sudo apt-get install -y build-essential cmake
    
    - name: Build and test C++
      run: |
        cd cpp_cli_tools/cli11_demo
        ./build.sh
        ./test_cli.sh

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Python image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.python
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_PYTHON }}:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_PYTHON }}:${{ github.sha }}
    
    - name: Build and push C++ image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.cpp
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_CPP }}:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_CPP }}:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy to Kubernetes
      run: |
        export KUBECONFIG=kubeconfig
        
        # Update image tags
        sed -i "s|image: cli-platform/python:latest|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_PYTHON }}:${{ github.sha }}|" k8s/deployment-python.yaml
        sed -i "s|image: cli-platform/cpp:latest|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_CPP }}:${{ github.sha }}|" k8s/deployment-cpp.yaml
        
        # Apply configurations
        kubectl apply -f k8s/
        
        # Wait for rollout
        kubectl rollout status deployment/cli-python -n cli-platform
        kubectl rollout status deployment/cli-cpp -n cli-platform
```

## Monitoring and Observability

### 1. Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "cli_platform_rules.yml"

scrape_configs:
  - job_name: 'cli-python'
    kubernetes_sd_configs:
    - role: endpoints
      namespaces:
        names:
        - cli-platform
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: cli-python-service
    - source_labels: [__meta_kubernetes_endpoint_port_name]
      action: keep
      regex: metrics

  - job_name: 'cli-cpp'
    kubernetes_sd_configs:
    - role: endpoints
      namespaces:
        names:
        - cli-platform
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: cli-cpp-service

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093
```

### 2. Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "CLI Platform Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      },
      {
        "title": "Code Generation Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(code_generation_success_total[5m]) / rate(code_generation_attempts_total[5m]) * 100",
            "legendFormat": "Success Rate %"
          }
        ]
      }
    ]
  }
}
```

### 3. Application Metrics
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter('cli_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('cli_request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = Gauge('cli_active_connections', 'Active connections')
CODE_GENERATION_ATTEMPTS = Counter('code_generation_attempts_total', 'Code generation attempts')
CODE_GENERATION_SUCCESS = Counter('code_generation_success_total', 'Successful code generations')
VALIDATION_LATENCY = Histogram('validation_duration_seconds', 'Validation latency')

class MetricsCollector:
    def __init__(self, port: int = 8080):
        self.port = port
        start_http_server(port)
    
    def track_request(self, method: str, endpoint: str):
        """Decorator for tracking HTTP requests"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "200"
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "500"
                    raise
                finally:
                    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                    REQUEST_LATENCY.observe(time.time() - start_time)
            
            return wrapper
        return decorator
    
    def track_code_generation(self, func):
        """Decorator for tracking code generation"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            CODE_GENERATION_ATTEMPTS.inc()
            
            try:
                result = func(*args, **kwargs)
                if result:
                    CODE_GENERATION_SUCCESS.inc()
                return result
            except Exception:
                raise
        
        return wrapper
    
    def track_validation(self, func):
        """Decorator for tracking validation performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                VALIDATION_LATENCY.observe(time.time() - start_time)
        
        return wrapper

# Usage in application
metrics = MetricsCollector()

@metrics.track_request("POST", "/evolve")
def evolve_command(description: str):
    # Implementation
    pass

@metrics.track_code_generation
def generate_code(description: str):
    # Implementation
    pass
```

## Security Hardening

### 1. Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cli-platform-network-policy
  namespace: cli-platform
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: cli-python
    - podSelector:
        matchLabels:
          app: cli-cpp
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 8001
  
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53  # DNS
    - protocol: UDP
      port: 53  # DNS
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 5432  # PostgreSQL
```

### 2. Pod Security Standards
```yaml
# k8s/pod-security-policy.yaml
apiVersion: v1
kind: Pod
metadata:
  name: cli-python
  namespace: cli-platform
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: cli-python
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: var-tmp-volume
      mountPath: /var/tmp
  
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: var-tmp-volume
    emptyDir: {}
```

## Scaling Strategies

### 1. Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cli-python-hpa
  namespace: cli-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cli-python
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: code_generation_requests_per_second
      target:
        type: AverageValue
        averageValue: "10"
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 2. Cluster Autoscaler Configuration
```yaml
# k8s/cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/cli-platform
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
        - --scale-down-delay-after-add=10m
        - --scale-down-unneeded-time=10m
```

This comprehensive deployment strategy provides a robust foundation for deploying the Self-Evolving CLI Platform in production environments with proper security, monitoring, and scaling capabilities. 