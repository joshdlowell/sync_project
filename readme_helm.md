I'll convert this to a Helm chart structure. Here's how it would look:

## Chart Structure
```
squishy-app/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── mysql-statefulset.yaml
│   ├── mysql-service.yaml
│   ├── rest-api-deployment.yaml
│   ├── rest-api-service.yaml
│   ├── integrity-cronjob.yaml
│   └── NOTES.txt
└── charts/
```

## Chart.yaml
```yaml
apiVersion: v2
name: squishy-app
description: A Helm chart for Squishy application with MySQL, REST API, and integrity checks
type: application
version: 0.1.0
appVersion: "1.0.0"
```

## values.yaml
```yaml
# Global configuration
global:
  location: "default"  # This will be the variable that changes per deployment
  namespace: squishy

# Application configuration
app:
  name: squishy-app
  version: v1.0

# MySQL configuration
mysql:
  image:
    repository: mysql
    tag: "9.3"
    pullPolicy: IfNotPresent
  
  database: squishy_db
  user: your_app_user
  
  # Secrets (these should be overridden)
  rootPassword: your_root_password
  userPassword: your_user_password
  
  storage:
    size: 10Gi
    storageClass: ""  # Use default storage class
  
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

# REST API configuration
restApi:
  image:
    repository: squishy-rest-api
    tag: v1.0
    pullPolicy: IfNotPresent
  
  replicas: 1
  port: 5000
  
  # Secret configuration
  secretKey: squishy_key_12345
  
  service:
    type: LoadBalancer
    port: 5000
    targetPort: 5000
  
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

# Integrity job configuration
integrity:
  image:
    repository: squishy-integrity
    tag: v1.0
    pullPolicy: IfNotPresent
  
  schedule: "0 2 * * *"  # Daily at 2 AM
  
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "200m"

# Init scripts configuration
initScripts:
  enabled: false
  scripts: {}
    # init.sql: |
    #   CREATE TABLE IF NOT EXISTS example_table (
    #     id INT AUTO_INCREMENT PRIMARY KEY,
    #     name VARCHAR(255),
    #     location VARCHAR(255)
    #   );
```

## templates/namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    location: {{ .Values.global.location }}
```

## templates/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "squishy-app.fullname" . }}-config
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
data:
  MYSQL_DATABASE: {{ .Values.mysql.database | quote }}
  MYSQL_USER: {{ .Values.mysql.user | quote }}
  LOCATION: {{ .Values.global.location | quote }}
---
{{- if .Values.initScripts.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "squishy-app.fullname" . }}-init-scripts
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
data:
  {{- toYaml .Values.initScripts.scripts | nindent 2 }}
{{- end }}
```

## templates/secret.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "squishy-app.fullname" . }}-secrets
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
type: Opaque
data:
  MYSQL_ROOT_PASSWORD: {{ .Values.mysql.rootPassword | b64enc | quote }}
  MYSQL_PASSWORD: {{ .Values.mysql.userPassword | b64enc | quote }}
  API_SECRET_KEY: {{ .Values.restApi.secretKey | b64enc | quote }}
```

## templates/mysql-service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "squishy-app.fullname" . }}-mysql
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: database
spec:
  selector:
    {{- include "squishy-app.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: database
  ports:
    - port: 3306
      targetPort: 3306
  clusterIP: None
```

## templates/mysql-statefulset.yaml
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "squishy-app.fullname" . }}-mysql
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: database
spec:
  serviceName: {{ include "squishy-app.fullname" . }}-mysql
  replicas: 1
  selector:
    matchLabels:
      {{- include "squishy-app.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: database
  template:
    metadata:
      labels:
        {{- include "squishy-app.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: database
        location: {{ .Values.global.location }}
    spec:
      containers:
      - name: mysql
        image: "{{ .Values.mysql.image.repository }}:{{ .Values.mysql.image.tag }}"
        imagePullPolicy: {{ .Values.mysql.image.pullPolicy }}
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "squishy-app.fullname" . }}-secrets
              key: MYSQL_ROOT_PASSWORD
        - name: MYSQL_DATABASE
          valueFrom:
            configMapKeyRef:
              name: {{ include "squishy-app.fullname" . }}-config
              key: MYSQL_DATABASE
        - name: MYSQL_USER
          valueFrom:
            configMapKeyRef:
              name: {{ include "squishy-app.fullname" . }}-config
              key: MYSQL_USER
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "squishy-app.fullname" . }}-secrets
              key: MYSQL_PASSWORD
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
        {{- if .Values.initScripts.enabled }}
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        {{- end }}
        resources:
          {{- toYaml .Values.mysql.resources | nindent 10 }}
      volumes:
      {{- if .Values.initScripts.enabled }}
      - name: init-scripts
        configMap:
          name: {{ include "squishy-app.fullname" . }}-init-scripts
      {{- end }}
  volumeClaimTemplates:
  - metadata:
      name: mysql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      {{- if .Values.mysql.storage.storageClass }}
      storageClassName: {{ .Values.mysql.storage.storageClass }}
      {{- end }}
      resources:
        requests:
          storage: {{ .Values.mysql.storage.size }}
```

## templates/rest-api-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "squishy-app.fullname" . }}-rest-api
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: api
spec:
  replicas: {{ .Values.restApi.replicas }}
  selector:
    matchLabels:
      {{- include "squishy-app.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: api
  template:
    metadata:
      labels:
        {{- include "squishy-app.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: api
        location: {{ .Values.global.location }}
    spec:
      containers:
      - name: rest-api
        image: "{{ .Values.restApi.image.repository }}:{{ .Values.restApi.image.tag }}"
        imagePullPolicy: {{ .Values.restApi.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.restApi.port }}
        env:
        - name: LOCAL_MYSQL_USER
          valueFrom:
            configMapKeyRef:
              name: {{ include "squishy-app.fullname" . }}-config
              key: MYSQL_USER
        - name: LOCAL_MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "squishy-app.fullname" . }}-secrets
              key: MYSQL_PASSWORD
        - name: API_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: {{ include "squishy-app.fullname" . }}-secrets
              key: API_SECRET_KEY
        - name: LOCATION
          valueFrom:
            configMapKeyRef:
              name: {{ include "squishy-app.fullname" . }}-config
              key: LOCATION
        resources:
          {{- toYaml .Values.restApi.resources | nindent 10 }}
```

## templates/rest-api-service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "squishy-app.fullname" . }}-rest-api
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: api
spec:
  selector:
    {{- include "squishy-app.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: api
  ports:
    - port: {{ .Values.restApi.service.port }}
      targetPort: {{ .Values.restApi.service.targetPort }}
  type: {{ .Values.restApi.service.type }}
```

## templates/integrity-cronjob.yaml
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ include "squishy-app.fullname" . }}-integrity
  namespace: {{ .Values.global.namespace }}-{{ .Values.global.location }}
  labels:
    {{- include "squishy-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: integrity
spec:
  schedule: {{ .Values.integrity.schedule | quote }}
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            {{- include "squishy-app.selectorLabels" . | nindent 12 }}
            app.kubernetes.io/component: integrity
            location: {{ .Values.global.location }}
        spec:
          containers:
          - name: integrity
            image: "{{ .Values.integrity.image.repository }}:{{ .Values.integrity.image.tag }}"
            imagePullPolicy: {{ .Values.integrity.image.pullPolicy }}
            env:
            - name: LOCAL_MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: {{ include "squishy-app.fullname" . }}-config
                  key: MYSQL_USER
            - name: LOCAL_MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ include "squishy-app.fullname" . }}-secrets
                  key: MYSQL_PASSWORD
            - name: LOCATION
              valueFrom:
                configMapKeyRef:
                  name: {{ include "squishy-app.fullname" . }}-config
                  key: LOCATION
            resources:
              {{- toYaml .Values.integrity.resources | nindent 14 }}
          restartPolicy: OnFailure
```

## templates/_helpers.tpl
```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "squishy-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "squishy-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "squishy-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "squishy-app.labels" -}}
helm.sh/chart: {{ include "squishy-app.chart" . }}
{{ include "squishy-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
location: {{ .Values.global.location }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "squishy-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "squishy-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

## templates/NOTES.txt
```txt
1. Get the application URL by running these commands:
{{- if eq .Values.restApi.service.type "LoadBalancer" }}
  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
        You can watch the status of by running 'kubectl get --namespace {{ .Values.global.namespace }}-{{ .Values.global.location }} svc -w {{ include "squishy-app.fullname" . }}-rest-api'
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Values.global.namespace }}-{{ .Values.global.location }} {{ include "squishy-app.fullname" . }}-rest-api --template "{{"{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}"}}")
  echo http://$SERVICE_IP:{{ .Values.restApi.service.port }}
{{- else if eq .Values.restApi.service.type "ClusterIP" }}
  export POD_NAME=$(kubectl get pods --namespace {{ .Values.global.namespace }}-{{ .Values.global.location }} -l "app.kubernetes.io/name={{ include "squishy-app.name" . }},app.kubernetes.io/instance={{ .Release.Name }},app.kubernetes.io/component=api" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace {{ .Values.global.namespace }}-{{ .Values.global.location }} $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace {{ .Values.global.namespace }}-{{ .Values.global.location }} port-forward $POD_NAME 8080:$CONTAINER_PORT
{{- end }}

2. Location: {{ .Values.global.location }}

3. Database connection details:
   - Host: {{ include "squishy-app.fullname" . }}-mysql.{{ .Values.global.namespace }}-{{ .Values.global.location }}.svc.cluster.local
   - Database: {{ .Values.mysql.database }}
   - User: {{ .Values.mysql.user }}

4. Integrity job schedule: {{ .Values.integrity.schedule }}
```

## Usage Examples

### Deploy to production location:
```bash
helm install squishy-prod ./squishy-app \
  --set global.location=us-east-1 \
  --set mysql.rootPassword=prod_root_password \
  --set mysql.userPassword=prod_user_password \
  --set restApi.secretKey=prod_secret_key_xyz789
```

### Deploy to staging location:
```bash
helm install squishy-staging ./squishy-app \
  --set global.location=us-west-2 \
  --set mysql.rootPassword=staging_root_password \
  --set mysql.userPassword=staging_user_password \
  --set restApi.secretKey=staging_secret_key_abc123
```

### Using values files:
Create `values-production.yaml`:
```yaml
global:
  location: us-east-1

mysql:
  rootPassword: prod_root_password
  userPassword: prod_user_password
  storage:
    size: 50Gi

restApi:
  secretKey: prod_secret_key_xyz789
  replicas: 3

integrity:
  schedule: "0 1 * * *"  # 1 AM daily
```

Then deploy:
```bash
helm install squishy-prod ./squishy-app -f values-production.yaml
```

This Helm chart provides:
- Location-based deployments with the `global.location` variable
- Flexible configuration through values.yaml
- Resource management and limits
- Proper labeling for different components
- Template helpers for consistency
- Easy secret management per environment