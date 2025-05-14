# py-react-mongodb-k8s
Full Kubernetes WebApp Stack (Python + React + MongoDB + Nginx)

    # PowerShell Script: Full Kubernetes WebApp Stack (Python + React + MongoDB + Nginx)
    
    # ===========================
    # STEP 1: Create Directory Structure
    # ===========================
    New-Item -ItemType Directory -Force -Path app-py-react\backend
    New-Item -ItemType Directory -Force -Path app-py-react\frontend
    New-Item -ItemType Directory -Force -Path app-py-react\nginx
    New-Item -ItemType Directory -Force -Path app-py-react\k8s
    
    # ===========================
    # STEP 2: Create Backend Flask App
    # ===========================
    @"
    from flask import Flask
    from pymongo import MongoClient
    import os
    
    app = Flask(__name__)
    
    MONGO_USER = os.environ.get("MONGO_USER", "admin")
    MONGO_PASS = os.environ.get("MONGO_PASS", "admin123")
    MONGO_HOST = os.environ.get("MONGO_HOST", "mongo-service")
    
    client = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:27017/")
    db = client["mydb"]
    
    @app.route("/api/hello")
    def hello():
        collection = db["greetings"]
        collection.insert_one({"message": "Hello from Flask with MongoDB"})
        return {"message": "Inserted into MongoDB"}
    
    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
    "@ | Set-Content app-py-react\backend\app.py
    
    "flask`npymongo" | Set-Content app-py-react\backend\requirements.txt
    
    # ===========================
    # STEP 3: Dockerfile for Backend
    # ===========================
    @"
    FROM python:3.10-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    CMD ["python", "app.py"]
    "@ | Set-Content app-py-react\backend\Dockerfile
    
    # ===========================
    # STEP 4: Create React Frontend
    # ===========================
    npx create-react-app app-py-react\frontend
    
    # ===========================
    # STEP 5: Dockerfile for Frontend
    # ===========================
    @"
    FROM node:16 as build
    WORKDIR /app
    COPY . .
    RUN npm install && npm run build
    
    FROM nginx:alpine
    COPY --from=build /app/build /usr/share/nginx/html
    "@ | Set-Content app-py-react\frontend\Dockerfile
    
    # ===========================
    # STEP 6: Nginx Config
    # ===========================
    @"
    server {
        listen 80;
    
        location /api/ {
            proxy_pass http://backend-service;
        }
    
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }
    }
    "@ | Set-Content app-py-react\nginx\nginx.conf
    
    # ===========================
    # STEP 7: Dockerfile for Nginx Reverse Proxy
    # ===========================
    @"
    FROM nginx:alpine
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    "@ | Set-Content app-py-react\nginx\Dockerfile
    
    # ===========================
    # STEP 8: Kubernetes Secrets for MongoDB
    # ===========================
    @"
    apiVersion: v1
    kind: Secret
    metadata:
      name: mongodb-secret
    type: Opaque
    data:
      mongo-user: $( [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("admin")) )
      mongo-password: $( [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("admin123")) )
    "@ | Set-Content app-py-react\k8s\mongo-secret.yaml
    
    # ===========================
    # STEP 9: Kubernetes Deployment for MongoDB
    # ===========================
    @"
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: mongo
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: mongo
      template:
        metadata:
          labels:
            app: mongo
        spec:
          containers:
          - name: mongo
            image: mongo:5
            ports:
            - containerPort: 27017
            env:
            - name: MONGO_INITDB_ROOT_USERNAME
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: mongo-user
            - name: MONGO_INITDB_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: mongo-password
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: mongo-service
    spec:
      selector:
        app: mongo
      ports:
      - port: 27017
        targetPort: 27017
    "@ | Set-Content app-py-react\k8s\mongo.yaml
    
    # ===========================
    # STEP 10: Kubernetes Deployment for Backend
    # ===========================
    @"
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: backend
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: backend
      template:
        metadata:
          labels:
            app: backend
        spec:
          containers:
          - name: backend
            image: annaleda/backend:latest
            ports:
            - containerPort: 5000
            env:
            - name: MONGO_USER
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: mongo-user
            - name: MONGO_PASS
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: mongo-password
            - name: MONGO_HOST
              value: mongo-service
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: backend-service
    spec:
      selector:
        app: backend
      ports:
      - port: 80
        targetPort: 5000
    "@ | Set-Content app-py-react\k8s\backend.yaml
    
    # ===========================
    # STEP 11: Kubernetes Deployment for Frontend
    # ===========================
    @"
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: frontend
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: frontend
      template:
        metadata:
          labels:
            app: frontend
        spec:
          containers:
          - name: frontend
            image: annaleda/frontend:latest
            ports:
            - containerPort: 80
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: frontend-service
    spec:
      selector:
        app: frontend
      ports:
      - port: 80
        targetPort: 80
        nodePort: 30080
      type: NodePort
    "@ | Set-Content app-py-react\k8s\frontend.yaml
    
    # ===========================
    # STEP 12: Build Docker Images
    # ===========================
    docker build -t annaleda/backend:latest ./app-py-react/backend
    docker build -t annaleda/frontend:latest ./app-py-react/frontend
    
    # ===========================
    # STEP 13: Deploy to Kubernetes
    # ===========================
    kubectl apply -f ./app-py-react/k8s/mongo-secret.yaml
    kubectl apply -f ./app-py-react/k8s/mongo.yaml
    kubectl apply -f ./app-py-react/k8s/backend.yaml
    kubectl apply -f ./app-py-react/k8s/frontend.yaml

