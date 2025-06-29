I'll convert your docker-compose.yaml to Kubernetes manifests. Here's the complete conversion:

## 1. Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: squishy
---
```

## 2. ConfigMap and Secret
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: squishy-config
  namespace: squishy
data:
  MYSQL_DATABASE: "squishy_db"
  MYSQL_USER: "your_app_user"
---
apiVersion: v1
kind: Secret
metadata:
  name: squishy-secrets
  namespace: squishy
type: Opaque
data:
  MYSQL_ROOT_PASSWORD: eW91cl9yb290X3Bhc3N3b3Jk  # base64 encoded "your_root_password"
  MYSQL_PASSWORD: eW91cl91c2VyX3Bhc3N3b3Jk      # base64 encoded "your_user_password"
  API_SECRET_KEY: c3F1aXNoeV9rZXlfMTIzNDU=      # base64 encoded "squishy_key_12345"
---
```

## 3. MySQL StatefulSet
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-squishy-db
  namespace: squishy
spec:
  selector:
    app: mysql-squishy-db
  ports:
    - port: 3306
      targetPort: 3306
  clusterIP: None  # Headless service for StatefulSet
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-squishy-db
  namespace: squishy
spec:
  serviceName: mysql-squishy-db
  replicas: 1
  selector:
    matchLabels:
      app: mysql-squishy-db
  template:
    metadata:
      labels:
        app: mysql-squishy-db
    spec:
      containers:
      - name: mysql
        image: mysql:9.3
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: squishy-secrets
              key: MYSQL_ROOT_PASSWORD
        - name: MYSQL_DATABASE
          valueFrom:
            configMapKeyRef:
              name: squishy-config
              key: MYSQL_DATABASE
        - name: MYSQL_USER
          valueFrom:
            configMapKeyRef:
              name: squishy-config
              key: MYSQL_USER
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: squishy-secrets
              key: MYSQL_PASSWORD
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: init-scripts
        configMap:
          name: mysql-init-scripts  # You'll need to create this ConfigMap with your init scripts
  volumeClaimTemplates:
  - metadata:
      name: mysql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
```

## 4. REST API Deployment and Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: squishy-rest-api
  namespace: squishy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: squishy-rest-api
  template:
    metadata:
      labels:
        app: squishy-rest-api
    spec:
      containers:
      - name: rest-api
        image: squishy-rest-api:v1.0
        ports:
        - containerPort: 5000
        env:
        - name: LOCAL_MYSQL_USER
          valueFrom:
            configMapKeyRef:
              name: squishy-config
              key: MYSQL_USER
        - name: LOCAL_MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: squishy-secrets
              key: MYSQL_PASSWORD
        - name: API_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: squishy-secrets
              key: API_SECRET_KEY
---
apiVersion: v1
kind: Service
metadata:
  name: squishy-rest-api-service
  namespace: squishy
spec:
  selector:
    app: squishy-rest-api
  ports:
    - port: 5000
      targetPort: 5000
  type: LoadBalancer  # Makes it accessible from outside
---
```

## 5. Integrity CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: squishy-integrity
  namespace: squishy
spec:
  schedule: "0 2 * * *"  # Run daily at 2 AM - adjust as needed
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: integrity
            image: squishy-integrity:v1.0
            env:
            - name: LOCAL_MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: squishy-config
                  key: MYSQL_USER
            - name: LOCAL_MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: squishy-secrets
                  key: MYSQL_PASSWORD
          restartPolicy: OnFailure
---
```

## 6. ConfigMap for MySQL Init Scripts (if needed)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-init-scripts
  namespace: squishy
data:
  # Add your init script content here
  # init.sql: |
  #   CREATE TABLE IF NOT EXISTS example_table (
  #     id INT AUTO_INCREMENT PRIMARY KEY,
  #     name VARCHAR(255)
  #   );
---
```

## Key Changes Made:

1. **StatefulSet for MySQL**: Provides persistent storage and stable network identity
2. **CronJob for Integrity**: Runs on a schedule instead of continuously
3. **Secrets and ConfigMaps**: Environment variables are now sourced from Kubernetes secrets and configmaps
4. **Service Types**: 
   - MySQL: ClusterIP (internal only)
   - REST API: LoadBalancer (externally accessible)
5. **Persistent Storage**: Added PersistentVolumeClaim for MySQL data
6. **Namespace**: All resources are organized under the `squishy` namespace

## Additional Notes:

- You'll need to create the ConfigMap for MySQL init scripts with your actual SQL files
- The base64 encoded secrets can be generated with: `echo -n "your_password" | base64`
- Adjust the CronJob schedule (`0 2 * * *`) to match your requirements
- Consider using an Ingress instead of LoadBalancer for the REST API if you need more advanced routing
- You may want to add resource limits and requests to the containers
- Consider adding health checks (readiness and liveness probes)

To deploy this, save each section to separate files or combine them with `---` separators and apply with:
```bash
kubectl apply -f your-k8s-manifests.yaml