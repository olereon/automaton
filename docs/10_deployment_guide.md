# Automaton Deployment Guide

## Introduction

This guide provides comprehensive information on deploying Automaton in various environments, from local setups to cloud-based production deployments. It covers different deployment strategies, configuration management, and best practices for maintaining reliable automation workflows.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Local Deployment](#local-deployment)
3. [Server Deployment](#server-deployment)
4. [Container Deployment](#container-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [CI/CD Integration](#cicd-integration)
7. [Configuration Management](#configuration-management)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Scaling Strategies](#scaling-strategies)
10. [Security Considerations](#security-considerations)

## Deployment Overview

### Deployment Models

Automaton supports several deployment models depending on your needs:

- **Local Deployment**: Run Automaton on your local machine for development and testing
- **Server Deployment**: Deploy on a dedicated server or virtual machine
- **Container Deployment**: Use Docker containers for consistent environments
- **Cloud Deployment**: Deploy to cloud platforms like AWS, Azure, or GCP
- **Serverless Deployment**: Run Automaton in response to events without managing servers

### Deployment Components

A typical Automaton deployment includes:

- **Automaton Core**: The main automation engine
- **Configuration Files**: JSON/YAML files defining automation workflows
- **Browser Dependencies**: Playwright browser binaries
- **Execution Environment**: Python runtime and dependencies
- **Storage**: For logs, screenshots, and extracted data
- **Monitoring**: Tools to track execution status and performance

## Local Deployment

### Development Setup

For local development, follow the [Installation Guide](2_installation_setup.md):

```bash
# Create and activate a virtual environment
python -m venv automaton-env
source automaton-env/bin/activate  # On Windows: automaton-env\Scripts\activate

# Install Automaton and dependencies
pip install automaton
python -m playwright install

# Run a simple automation
automaton run examples/simple.json
```

### IDE Configuration

For development with VS Code:

1. Install the Python extension
2. Create a `.vscode/settings.json` file:
   ```json
   {
     "python.defaultInterpreterPath": "./automaton-env/bin/python",
     "python.linting.enabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true
   }
   ```
3. Install recommended extensions:
   - Python
   - Pylance
   - Black Formatter

### Local Development Workflow

1. Create automation configurations in a dedicated directory:
   ```
   project/
   ├── automations/
   │   ├── login.json
   │   ├── data_extraction.json
   │   └── report_generation.json
   └── output/
       ├── logs/
       ├── screenshots/
       └── data/
   ```

2. Test automations individually:
   ```bash
   automaton run automations/login.json --output-dir output/
   ```

3. Run multiple automations with a script:
   ```python
   # run_automations.py
   import subprocess
   import os
   
   automations = [
       "automations/login.json",
       "automations/data_extraction.json",
       "automations/report_generation.json"
   ]
   
   for automation in automations:
       print(f"Running {automation}...")
       subprocess.run(["automaton", "run", automation, "--output-dir", "output/"])
   ```

## Server Deployment

### Server Requirements

- Operating System: Linux (Ubuntu 20.04+ recommended), Windows Server 2019+, or macOS
- Python: 3.11 or higher
- RAM: Minimum 2GB, 4GB+ recommended
- Storage: Minimum 5GB free space, more depending on automation needs
- Network: Stable internet connection for web automation

### Installation on Linux

1. Update system packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install Python and dependencies:
   ```bash
   sudo apt install python3.11 python3.11-venv python3.11-pip -y
   ```

3. Create a dedicated user:
   ```bash
   sudo useradd -m -s /bin/bash automaton
   sudo su - automaton
   ```

4. Set up a virtual environment:
   ```bash
   cd ~
   python3.11 -m venv automaton-env
   source automaton-env/bin/activate
   ```

5. Install Automaton:
   ```bash
   pip install automaton
   python -m playwright install
   ```

### Systemd Service Configuration

Create a systemd service file `/etc/systemd/system/automaton.service`:

```ini
[Unit]
Description=Automaton Service
After=network.target

[Service]
Type=simple
User=automaton
WorkingDirectory=/home/automaton
Environment=PATH=/home/automaton/automaton-env/bin
ExecStart=/home/automaton/automaton-env/bin/automaton-server --config /home/automaton/config/server.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable automaton
sudo systemctl start automaton
```

### Windows Service Configuration

1. Install NSSM (Non-Sucking Service Manager):
   ```powershell
   cd C:\automaton
   curl -L -o nssm.zip https://nssm.cc/release/nssm-2.24.zip
   Expand-Archive -Path nssm.zip -DestinationPath .
   .\nssm-2.24\win64\nssm.exe install Automaton C:\automaton\automaton-env\Scripts\python.exe C:\automaton\run_server.py
   ```

2. Configure the service:
   ```powershell
   .\nssm-2.24\win64\nssm.exe set Automaton AppDirectory C:\automaton
   .\nssm-2.24\win64\nssm.exe set Automaton AppEnvironmentExtra "PYTHONPATH=C:\automaton"
   .\nssm-2.24\win64\nssm.exe set Automaton Start SERVICE_AUTO_START
   ```

3. Start the service:
   ```powershell
   .\nssm-2.24\win64\nssm.exe start Automaton
   ```

## Container Deployment

### Docker Setup

1. Create a Dockerfile:
   ```dockerfile
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       wget \
       gnupg \
       ca-certificates \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Playwright
   RUN pip install playwright
   RUN playwright install --with-deps chromium
   
   # Install Automaton
   RUN pip install automaton
   
   # Create app directory
   WORKDIR /app
   
   # Copy configuration files
   COPY ./automations /app/automations
   COPY ./config /app/config
   
   # Create output directory
   RUN mkdir -p /app/output
   
   # Set up a non-root user
   RUN useradd --create-home --shell /bin/bash automaton
   RUN chown -R automaton:automaton /app
   USER automaton
   
   # Expose port for web interface (if using)
   EXPOSE 8080
   
   # Default command
   CMD ["automaton-server", "--config", "/app/config/server.json"]
   ```

2. Create a .dockerignore file:
   ```
   .git
   .gitignore
   .vscode
   __pycache__
   *.pyc
   *.pyo
   *.pyd
   .Python
   env
   pip-log.txt
   output/
   ```

3. Build the Docker image:
   ```bash
   docker build -t automaton:latest .
   ```

### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  automaton:
    image: automaton:latest
    container_name: automaton
    restart: unless-stopped
    volumes:
      - ./automations:/app/automations:ro
      - ./config:/app/config:ro
      - ./output:/app/output
    environment:
      - TZ=UTC
    networks:
      - automaton-network

  # Optional: Add a database for storing results
  postgres:
    image: postgres:13
    container_name: automaton-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=automaton
      - POSTGRES_USER=automaton
      - POSTGRES_PASSWORD=automaton_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - automaton-network

  # Optional: Add Redis for caching and job queuing
  redis:
    image: redis:6-alpine
    container_name: automaton-redis
    restart: unless-stopped
    networks:
      - automaton-network

volumes:
  postgres_data:

networks:
  automaton-network:
    driver: bridge
```

Start the services:

```bash
docker-compose up -d
```

### Kubernetes Deployment

1. Create a ConfigMap for configurations:
   ```yaml
   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: automaton-config
   data:
     server.json: |
       {
         "host": "0.0.0.0",
         "port": 8080,
         "log_level": "info"
       }
   ```

2. Create a PersistentVolumeClaim for output storage:
   ```yaml
   # pvc.yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: automaton-output-pvc
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 10Gi
   ```

3. Create a Deployment:
   ```yaml
   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: automaton
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: automaton
     template:
       metadata:
         labels:
           app: automaton
       spec:
         containers:
         - name: automaton
           image: automaton:latest
           ports:
           - containerPort: 8080
           volumeMounts:
           - name: config-volume
             mountPath: /app/config
           - name: output-volume
             mountPath: /app/output
         volumes:
         - name: config-volume
           configMap:
             name: automaton-config
         - name: output-volume
           persistentVolumeClaim:
             claimName: automaton-output-pvc
   ```

4. Create a Service:
   ```yaml
   # service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: automaton-service
   spec:
     selector:
       app: automaton
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8080
     type: LoadBalancer
   ```

Apply the configurations:

```bash
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Cloud Deployment

### AWS Deployment

#### Using EC2

1. Launch an EC2 instance:
   - Choose Amazon Linux 2 or Ubuntu
   - Configure security groups to allow necessary ports
   - Attach an IAM role with appropriate permissions

2. Install dependencies:
   ```bash
   # For Amazon Linux 2
   sudo yum update -y
   sudo yum install python3.11 python3.11-pip -y
   
   # For Ubuntu
   sudo apt update && sudo apt install python3.11 python3.11-pip -y
   ```

3. Install Automaton:
   ```bash
   pip3.11 install automaton
   python3.11 -m playwright install
   ```

4. Set up systemd service as described in the [Server Deployment](#server-deployment) section.

#### Using ECS (Elastic Container Service)

1. Create a task definition:
   ```json
   {
     "family": "automaton",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "automaton",
         "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/automaton:latest",
         "portMappings": [
           {
             "containerPort": 8080,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "TZ",
             "value": "UTC"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/automaton",
             "awslogs-region": "REGION",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

2. Create a service using the task definition.

#### Using Lambda (Serverless)

1. Create a Lambda function with the following structure:
   ```python
   # lambda_function.py
   import json
   import subprocess
   import os
   import tempfile
   import boto3
   
   s3 = boto3.client('s3')
   
   def lambda_handler(event, context):
       # Download configuration from S3
       config_bucket = event['config_bucket']
       config_key = event['config_key']
       
       with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
           s3.download_file(config_bucket, config_key, tmp.name)
           config_path = tmp.name
       
       # Run Automaton
       try:
           result = subprocess.run(
               ['automaton', 'run', config_path, '--output-dir', '/tmp'],
               capture_output=True,
               text=True,
               timeout=context.get_remaining_time_in_millis() / 1000 - 10
           )
           
           if result.returncode == 0:
               # Upload output to S3
               output_bucket = event['output_bucket']
               output_prefix = event['output_prefix']
               
               for root, dirs, files in os.walk('/tmp'):
                   for file in files:
                       local_path = os.path.join(root, file)
                       s3_key = f"{output_prefix}/{file}"
                       s3.upload_file(local_path, output_bucket, s3_key)
               
               return {
                   'statusCode': 200,
                   'body': json.dumps({
                       'message': 'Automation completed successfully',
                       'output': f"s3://{output_bucket}/{output_prefix}"
                   })
               }
           else:
               return {
                   'statusCode': 500,
                   'body': json.dumps({
                       'message': 'Automation failed',
                       'error': result.stderr
                   })
               }
       except subprocess.TimeoutExpired:
           return {
               'statusCode': 500,
               'body': json.dumps({
                   'message': 'Automation timed out'
               })
           }
       except Exception as e:
           return {
               'statusCode': 500,
               'body': json.dumps({
                   'message': f'Error running automation: {str(e)}'
               })
           }
       finally:
           os.unlink(config_path)
   ```

2. Package the function with dependencies and deploy to Lambda.

### Azure Deployment

#### Using Virtual Machines

1. Create a Virtual Machine in the Azure portal:
   - Choose Ubuntu or Windows Server
   - Configure networking and security groups
   - Set up managed identities for accessing Azure resources

2. Connect to the VM and install Automaton as described in the [Server Deployment](#server-deployment) section.

#### Using Azure Container Instances

1. Build and push your Docker image to Azure Container Registry:
   ```bash
   az acr build --registry <registry-name> --image automaton:latest .
   ```

2. Deploy to Azure Container Instances:
   ```bash
   az container create \
     --resource-group <resource-group> \
     --name automaton \
     --image <registry-name>.azurecr.io/automaton:latest \
     --cpu 2 \
     --memory 4 \
     --ports 8080 \
     --azure-file-volume-account-name <storage-account> \
     --azure-file-volume-account-key <storage-key> \
     --azure-file-volume-share-name automaton-output \
     --azure-file-volume-mount-path /app/output
   ```

#### Using Azure Functions (Serverless)

1. Create an Azure Function with a Timer trigger:
   ```python
   # __init__.py
   import logging
   import subprocess
   import os
   import json
   import azure.functions as func
   
   app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
   
   @app.timer_trigger(schedule="0 0 8 * * *", arg_name="mytimer", run_on_startup=False,
               use_monitor=False) 
   def automaton_timer(mytimer: func.TimerRequest) -> func.HttpResponse:
       logging.info('Automaton timer trigger function executed.')
       
       # Run Automaton
       try:
           result = subprocess.run(
               ['automaton', 'run', 'automations/daily.json', '--output-dir', 'output'],
               capture_output=True,
               text=True,
               timeout=300  # 5 minutes timeout
           )
           
           if result.returncode == 0:
               logging.info('Automation completed successfully')
               return func.HttpResponse(
                   "Automation completed successfully",
                   status_code=200
               )
           else:
               logging.error(f'Automation failed: {result.stderr}')
               return func.HttpResponse(
                   f"Automation failed: {result.stderr}",
                   status_code=500
               )
       except subprocess.TimeoutExpired:
           logging.error('Automation timed out')
           return func.HttpResponse(
               "Automation timed out",
               status_code=500
           )
       except Exception as e:
           logging.error(f'Error running automation: {str(e)}')
           return func.HttpResponse(
               f"Error running automation: {str(e)}",
               status_code=500
           )
   ```

2. Deploy the function to Azure Functions.

### GCP Deployment

#### Using Compute Engine

1. Create a VM instance in Google Cloud Console:
   - Choose a machine type with sufficient resources
   - Configure firewall rules to allow necessary traffic
   - Set up service accounts for accessing GCP resources

2. Connect to the instance and install Automaton as described in the [Server Deployment](#server-deployment) section.

#### Using Cloud Run

1. Build and push your Docker image to Google Container Registry:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/automaton
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy automaton \
     --image gcr.io/PROJECT_ID/automaton \
     --platform managed \
     --memory 4Gi \
     --cpu 2 \
     --set-cloudsql-instances INSTANCE_CONNECTION_NAME \
     --allow-unauthenticated
   ```

#### Using Cloud Functions (Serverless)

1. Create a Cloud Function with an HTTP trigger:
   ```python
   # main.py
   import subprocess
   import json
   import os
   import tempfile
   from google.cloud import storage
   
   def automaton_http(request):
       # Parse request
       request_json = request.get_json(silent=True)
       if request_json and 'config_bucket' in request_json and 'config_key' in request_json:
           config_bucket = request_json['config_bucket']
           config_key = request_json['config_key']
           output_bucket = request_json.get('output_bucket', config_bucket)
           output_prefix = request_json.get('output_prefix', 'output/')
       else:
           return json.dumps({'error': 'Missing required parameters'}), 400
       
       # Download configuration from GCS
       storage_client = storage.Client()
       bucket = storage_client.bucket(config_bucket)
       blob = bucket.blob(config_key)
       
       with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
           blob.download_to_filename(tmp.name)
           config_path = tmp.name
       
       # Run Automaton
       try:
           result = subprocess.run(
               ['automaton', 'run', config_path, '--output-dir', '/tmp'],
               capture_output=True,
               text=True,
               timeout=300  # 5 minutes timeout
           )
           
           if result.returncode == 0:
               # Upload output to GCS
               output_bucket_obj = storage_client.bucket(output_bucket)
               
               for root, dirs, files in os.walk('/tmp'):
                   for file in files:
                       local_path = os.path.join(root, file)
                       blob_name = f"{output_prefix}{file}"
                       blob = output_bucket_obj.blob(blob_name)
                       blob.upload_from_filename(local_path)
               
               return json.dumps({
                   'message': 'Automation completed successfully',
                   'output': f"gs://{output_bucket}/{output_prefix}"
               }), 200
           else:
               return json.dumps({
                   'message': 'Automation failed',
                   'error': result.stderr
               }), 500
       except subprocess.TimeoutExpired:
           return json.dumps({'message': 'Automation timed out'}), 500
       except Exception as e:
           return json.dumps({
               'message': f'Error running automation: {str(e)}'
           }), 500
       finally:
           os.unlink(config_path)
   ```

2. Deploy the function to Cloud Functions.

## CI/CD Integration

### GitHub Actions

Create a workflow file `.github/workflows/automaton.yml`:

```yaml
name: Automaton CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

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
        pip install automaton
        python -m playwright install --with-deps chromium
    
    - name: Run tests
      run: |
        automaton validate examples/
    
    - name: Run example automation
      run: |
        automaton run examples/simple.json

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: your-username/automaton:latest
    
    - name: Deploy to production server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/automaton
          docker-compose pull
          docker-compose up -d
```

### GitLab CI

Create a `.gitlab-ci.yml` file:

```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_REGISTRY: registry.gitlab.com
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE

test:
  stage: test
  image: python:3.11
  
  before_script:
    - pip install automaton
    - python -m playwright install --with-deps chromium
  
  script:
    - automaton validate examples/
    - automaton run examples/simple.json

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: alpine:latest
  
  before_script:
    - apk add --no-cache openssh-client
  
  script:
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh -o StrictHostKeyChecking=no $PRODUCTION_USER@$PRODUCTION_HOST "cd /opt/automaton && docker-compose pull && docker-compose up -d"
  
  only:
    - main
```

### Jenkins Pipeline

Create a `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        DOCKER_IMAGE = 'automaton'
    }
    
    stages {
        stage('Test') {
            steps {
                sh '''
                    python3.11 -m venv venv
                    source venv/bin/activate
                    pip install automaton
                    python -m playwright install --with-deps chromium
                    automaton validate examples/
                    automaton run examples/simple.json
                '''
            }
        }
        
        stage('Build') {
            steps {
                script {
                    docker.build("$DOCKER_IMAGE:$BUILD_ID")
                    docker.withRegistry("https://$DOCKER_REGISTRY", "docker-credentials") {
                        docker.image("$DOCKER_IMAGE:$BUILD_ID").push()
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                sshagent(['production-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no user@production-server "cd /opt/automaton && docker-compose pull && docker-compose up -d"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

## Configuration Management

### Environment-Specific Configurations

Organize configurations by environment:

```
config/
├── base.json              # Base configuration
├── development.json      # Development overrides
├── staging.json          # Staging overrides
└── production.json       # Production overrides
```

Use a configuration merging strategy:

```python
# config_loader.py
import json
import os

def load_config(environment):
    # Load base configuration
    with open('config/base.json', 'r') as f:
        config = json.load(f)
    
    # Load environment-specific overrides
    env_file = f'config/{environment}.json'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_config = json.load(f)
        
        # Merge configurations (deep merge would be better for nested objects)
        config.update(env_config)
    
    return config
```

### Secrets Management

Never store secrets in configuration files. Use environment variables or a secrets manager:

```json
{
  "name": "Secure Automation",
  "url": "https://example.com",
  "actions": [
    {
      "type": "input_text",
      "selector": "#username",
      "value": "${USERNAME}"
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "${PASSWORD}"
    }
  ]
}
```

Set environment variables:

```bash
# For local development
export USERNAME="your_username"
export PASSWORD="your_password"

# For systemd service
# Edit /etc/systemd/system/automaton.service
[Service]
Environment="USERNAME=your_username"
Environment="PASSWORD=your_password"
```

For cloud deployments, use the respective secrets management service:
- AWS Secrets Manager
- Azure Key Vault
- Google Cloud Secret Manager

### Configuration Validation

Validate configurations before deployment:

```python
# validate_config.py
import json
import sys
from jsonschema import validate, ValidationError

# Define schema for configuration validation
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "url": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "selector": {"type": "string"}
                },
                "required": ["type"]
            }
        }
    },
    "required": ["name", "url", "actions"]
}

def validate_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        validate(config, schema)
        print(f"Configuration {config_file} is valid")
        return True
    except ValidationError as e:
        print(f"Configuration {config_file} is invalid: {e.message}")
        return False
    except Exception as e:
        print(f"Error validating {config_file}: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_config.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    if not validate_config(config_file):
        sys.exit(1)
```

## Monitoring and Logging

### Logging Configuration

Configure logging in your deployment:

```json
{
  "name": "Monitored Automation",
  "url": "https://example.com",
  "logging": {
    "level": "info",
    "file": "/var/log/automaton/automation.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "max_size": "10MB",
    "backup_count": 5
  },
  "actions": []
}
```

### Structured Logging

Use structured logging for better analysis:

```json
{
  "name": "Structured Logging",
  "url": "https://example.com",
  "logging": {
    "level": "info",
    "structured": true,
    "fields": ["timestamp", "level", "message", "action", "duration", "status"]
  },
  "actions": []
}
```

### Monitoring with Prometheus

Expose metrics for Prometheus monitoring:

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
AUTOMATION_RUNS_TOTAL = Counter('automaton_runs_total', 'Total number of automation runs', ['status', 'automation'])
AUTOMATION_DURATION_SECONDS = Histogram('automaton_duration_seconds', 'Time spent on automation', ['automation'])
ACTIVE_AUTOMATIONS = Gauge('active_automations', 'Number of currently running automations')

def start_metrics_server(port=8000):
    start_http_server(port)

def record_automation_start(automation_name):
    ACTIVE_AUTOMATIONS.inc()
    return time.time()

def record_automation_completion(automation_name, start_time, status):
    duration = time.time() - start_time
    AUTOMATION_DURATION_SECONDS.labels(automation=automation_name).observe(duration)
    AUTOMATION_RUNS_TOTAL.labels(status=status, automation=automation_name).inc()
    ACTIVE_AUTOMATIONS.dec()
```

### Health Checks

Implement health check endpoints:

```python
# health_check.py
from flask import Flask, jsonify
import subprocess
import os
import psutil

app = Flask(__name__)

@app.route('/health')
def health_check():
    # Check if Automaton process is running
    automaton_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'python' and 'automaton' in proc.info['cmdline']:
            automaton_running = True
            break
    
    # Check disk space
    disk_usage = psutil.disk_usage('/')
    disk_ok = disk_usage.percent < 90
    
    # Check memory usage
    memory = psutil.virtual_memory()
    memory_ok = memory.percent < 90
    
    status = {
        'status': 'healthy' if automaton_running and disk_ok and memory_ok else 'unhealthy',
        'automaton_running': automaton_running,
        'disk_usage_percent': disk_usage.percent,
        'memory_usage_percent': memory.percent
    }
    
    return jsonify(status), 200 if status['status'] == 'healthy' else 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Alerting

Set up alerts for critical issues:

```yaml
# prometheus-alerts.yml
groups:
- name: automaton.alerts
  rules:
  - alert: AutomatonDown
    expr: up{job="automaton"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Automaton instance is down"
      description: "Automaton instance {{ $labels.instance }} has been down for more than 5 minutes"
  
  - alert: HighDiskUsage
    expr: 100 - (disk_free{mountpoint="/"} / disk_size{mountpoint="/"} * 100) > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High disk usage on Automaton server"
      description: "Disk usage on {{ $labels.instance }} is {{ $value }}%"
  
  - alert: HighMemoryUsage
    expr: 100 - (memory_free / memory_total * 100) > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on Automaton server"
      description: "Memory usage on {{ $labels.instance }} is {{ $value }}%"
  
  - alert: AutomationFailureRate
    expr: rate(automaton_runs_total{status="failed"}[5m]) / rate(automaton_runs_total[5m]) > 0.1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High automation failure rate"
      description: "Automation failure rate is {{ $value }}% over the last 5 minutes"
```

## Scaling Strategies

### Horizontal Scaling

Scale out by running multiple Automaton instances:

1. Use a load balancer to distribute requests
2. Implement a queue system for job distribution
3. Use shared storage for configuration and output

Example with Redis queue:

```python
# queue_worker.py
import redis
import json
import subprocess
import time
from automaton import Automaton

# Connect to Redis
r = redis.Redis(host='redis', port=6379, db=0)

def process_queue():
    while True:
        # Get job from queue
        job_data = r.blpop('automaton_jobs', timeout=0)
        if job_data:
            _, job_json = job_data
            job = json.loads(job_json)
            
            # Update job status
            job_id = job['id']
            r.hset(f'job:{job_id}', 'status', 'running')
            r.hset(f'job:{job_id}', 'started_at', time.time())
            
            try:
                # Run automation
                automaton = Automaton(job['config'])
                result = automaton.run()
                
                # Update job status
                r.hset(f'job:{job_id}', 'status', 'completed')
                r.hset(f'job:{job_id}', 'result', json.dumps(result))
                r.hset(f'job:{job_id}', 'completed_at', time.time())
            except Exception as e:
                # Update job status
                r.hset(f'job:{job_id}', 'status', 'failed')
                r.hset(f'job:{job_id}', 'error', str(e))
                r.hset(f'job:{job_id}', 'completed_at', time.time())
            
            # Notify of completion (optional)
            r.publish(f'job_completed:{job_id}', json.dumps({
                'id': job_id,
                'status': r.hget(f'job:{job_id}', 'status').decode()
            }))

if __name__ == "__main__":
    process_queue()
```

### Vertical Scaling

Increase resources for a single instance:

1. Upgrade server specifications (CPU, RAM)
2. Optimize browser resource usage
3. Implement resource limits

Example configuration for resource limits:

```json
{
  "name": "Resource Limited Automation",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": true,
    "args": [
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-software-rasterizer",
      "--disable-extensions"
    ]
  },
  "resource_limits": {
    "memory_mb": 2048,
    "cpu_percent": 80,
    "timeout_ms": 300000
  },
  "actions": []
}
```

### Geographic Distribution

For global deployments:

1. Deploy instances in multiple regions
2. Use a CDN for static resources
3. Route requests to the nearest instance

Example with regional deployment:

```yaml
# docker-compose.geo.yml
version: '3.8'

services:
  automaton-us:
    image: automaton:latest
    container_name: automaton-us
    restart: unless-stopped
    environment:
      - REGION=us-east-1
      - TZ=America/New_York
    volumes:
      - ./automations:/app/automations:ro
      - ./config:/app/config:ro
      - us-output:/app/output
    networks:
      - automaton-network

  automaton-eu:
    image: automaton:latest
    container_name: automaton-eu
    restart: unless-stopped
    environment:
      - REGION=eu-west-1
      - TZ=Europe/London
    volumes:
      - ./automations:/app/automations:ro
      - ./config:/app/config:ro
      - eu-output:/app/output
    networks:
      - automaton-network

volumes:
  us-output:
  eu-output:

networks:
  automaton-network:
    driver: bridge
```

## Security Considerations

### Secure Configuration

1. Use environment variables for sensitive data
2. Restrict file permissions on configuration files
3. Validate all external inputs

Example secure configuration:

```json
{
  "name": "Secure Automation",
  "url": "https://example.com",
  "security": {
    "validate_ssl": true,
    "strict_content_security_policy": true,
    "disable_web_security": false,
    "ignore_https_errors": false
  },
  "actions": [
    {
      "type": "input_text",
      "selector": "#username",
      "value": "${USERNAME}"
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "${PASSWORD}",
      "secure": true
    }
  ]
}
```

### Network Security

1. Use VPNs or private networks for internal communications
2. Implement firewall rules to restrict access
3. Use TLS/SSL for all network communications

Example network configuration:

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  automaton:
    image: automaton:latest
    container_name: automaton
    restart: unless-stopped
    networks:
      - automaton-internal
    ports:
      - "127.0.0.1:8080:8080"  # Only accessible from localhost
    environment:
      - AUTOMATON_API_KEY=${AUTOMATON_API_KEY}
    volumes:
      - ./automations:/app/automations:ro
      - ./config:/app/config:ro
      - ./output:/app/output
    secrets:
      - db_password
      - api_key

  reverse-proxy:
    image: nginx:alpine
    container_name: automaton-proxy
    restart: unless-stopped
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - automaton-internal
    depends_on:
      - automaton

networks:
  automaton-internal:
    driver: bridge
    internal: true  # No external access

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
```

### Access Control

1. Implement authentication for API access
2. Use role-based access control (RBAC)
3. Audit access logs regularly

Example authentication middleware:

```python
# auth_middleware.py
from functools import wraps
import jwt
import os
from flask import request, jsonify

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Remove "Bearer " prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # Add user info to request
            request.user = payload
            
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
    
    return decorated

def authorize(roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'message': 'Authentication required'}), 401
            
            user_roles = request.user.get('roles', [])
            
            if not any(role in user_roles for role in roles):
                return jsonify({'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator
```

### Data Protection

1. Encrypt sensitive data at rest
2. Use secure protocols for data in transit
3. Implement data retention policies

Example encryption utility:

```python
# encryption.py
from cryptography.fernet import Fernet
import os
import base64

class DataEncryptor:
    def __init__(self, key=None):
        if key is None:
            key = os.environ.get('ENCRYPTION_KEY')
            if key is None:
                # Generate a new key if none is provided
                key = Fernet.generate_key()
                print(f"Generated new encryption key: {key.decode()}")
        
        # Ensure key is 32 bytes and URL-safe base64-encoded
        if isinstance(key, str):
            key = key.encode()
        
        if len(key) != 32:
            # Derive a 32-byte key from the provided key
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
            
            salt = b'automaton_salt'  # In production, use a random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key))
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_file(self, input_file, output_file):
        with open(input_file, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encrypt(data)
        
        with open(output_file, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_file(self, input_file, output_file):
        with open(input_file, 'rb') as f:
            encrypted_data = f.read()
        
        data = self.decrypt(encrypted_data)
        
        with open(output_file, 'wb') as f:
            f.write(data)
```

## Next Steps

After setting up your deployment:

1. Review the [main README](../README.md) for an overview of the project
2. Check the [Contributing Guide](9_contributing_guide.md) if you want to help improve Automaton
3. Explore [Advanced Usage](7_advanced_usage.md) for more complex automation scenarios

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*