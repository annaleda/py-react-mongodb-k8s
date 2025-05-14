# py-react-mongodb-k8s
Full Kubernetes WebApp Stack (Python + React + MongoDB + Nginx)

        # PowerShell Script: Setup Python (Flask) + React + MongoDB + Nginx Reverse Proxy on Kubernetes
        
        # ===========================
        # STEP 1: Create Directory Structure
        # ===========================
        New-Item -ItemType Directory -Force -Path app-py-react\backend
        New-Item -ItemType Directory -Force -Path app-py-react\frontend
        New-Item -ItemType Directory -Force -Path app-py-react\nginx
        New-Item -ItemType Directory -Force -Path app-py-react\k8s
        
        # ===========================
        # STEP 2: Create Flask App
        # ===========================
        @"
        from flask import Flask
        from pymongo import MongoClient
        import os
        
        app = Flask(__name__)
        client = MongoClient(f"mongodb://{os.environ.get('MONGO_USER')}:{os.environ.get('MONGO_PASS')}@mongodb-service:27017/")
        db = client.testdb
        
        @app.route("/api/hello")
        def hello():
            return {"message": "Hello from Flask + Mongo"}
        
        if __name__ == "__main__":
            app.run(host="0.0.0.0", port=5000)
        "@ | Set-Content app-py-react\backend\app.py
        
        "flask\npymongo" | Set-Content app-py-react\backend\requirements.txt
        
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
        # STEP 4: React Frontend
        # ===========================
        npx create-react-app app-py-react\frontend
        
        # Modify App.js
        @"
        import { useEffect, useState } from "react";
        
        function App() {
          const [msg, setMsg] = useState("");
        
          useEffect(() => {
            fetch("/api/hello")
              .then(res => res.json())
              .then(data => setMsg(data.message))
              .catch(console.error);
          }, []);
        
          return (
            <div>
              <h1>React + Flask + Mongo + Nginx</h1>
              <p>Message: {msg}</p>
            </div>
          );
        }
        
        export default App;
        "@ | Set-Content app-py-react\frontend\src\App.js
        
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
        # STEP 7: Dockerfile for Nginx
        # ===========================
        @"
        FROM nginx:alpine
        COPY nginx.conf /etc/nginx/conf.d/default.conf
        "@ | Set-Content app-py-react\nginx\Dockerfile
        
        # ===========================
        # STEP 8: Kubernetes Manifests
        # ===========================
        
        # --- MongoDB with Secret
        @"
        apiVersion: v1
        kind: Secret
        metadata:
          name: mongo-secret
        type: Opaque
        data:
          mongo-user: bW9uZ291c2Vy
          mongo-pass: bW9uZ29wYXNz
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: mongodb-service
        spec:
          selector:
            app: mongodb
          ports:
            - port: 27017
        ---
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: mongodb
        spec:
          replicas: 1
          selector:
            matchLabels:
              app: mongodb
          template:
            metadata:
              labels:
                app: mongodb
            spec:
              containers:
                - name: mongodb
                  image: mongo
                  ports:
                    - containerPort: 27017
                  env:
                    - name: MONGO_INITDB_ROOT_USERNAME
                      valueFrom:
                        secretKeyRef:
                          name: mongo-secret
                          key: mongo-user
                    - name: MONGO_INITDB_ROOT_PASSWORD
                      valueFrom:
                        secretKeyRef:
                          name: mongo-secret
                          key: mongo-pass
        "@ | Set-Content app-py-react\k8s\mongodb.yaml
        
        # --- Backend
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
                          name: mongo-secret
                          key: mongo-user
                    - name: MONGO_PASS
                      valueFrom:
                        secretKeyRef:
                          name: mongo-secret
                          key: mongo-pass
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
        
        # --- Frontend
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
          type: ClusterIP
        "@ | Set-Content app-py-react\k8s\frontend.yaml
        
        # --- Nginx Reverse Proxy
        @"
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: nginx
        spec:
          replicas: 1
          selector:
            matchLabels:
              app: nginx
          template:
            metadata:
              labels:
                app: nginx
            spec:
              containers:
                - name: nginx
                  image: annaleda/nginx:latest
                  ports:
                    - containerPort: 80
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: nginx-service
        spec:
          selector:
            app: nginx
          ports:
            - port: 80
              targetPort: 80
              nodePort: 30090
          type: NodePort
        "@ | Set-Content app-py-react\k8s\nginx.yaml
        
        # ===========================
        # STEP 9: Build and Push Docker Images
        # ===========================
        docker build -t annaleda/backend:latest ./app-py-react/backend
        
        docker build -t annaleda/frontend:latest ./app-py-react/frontend
        
        docker build -t annaleda/nginx:latest ./app-py-react/nginx
        
        docker push annaleda/backend:latest
        docker push annaleda/frontend:latest
        docker push annaleda/nginx:latest
        
        # ===========================
        # STEP 10: Deploy to Kubernetes
        # ===========================
        kubectl apply -f ./app-py-react/k8s/mongodb.yaml
        kubectl apply -f ./app-py-react/k8s/backend.yaml
        kubectl apply -f ./app-py-react/k8s/frontend.yaml
        kubectl apply -f ./app-py-react/k8s/nginx.yaml
