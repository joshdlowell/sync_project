Here's a Kubernetes ConfigMap for your SQL file:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hashtable-schema
  namespace: default  # Change to your desired namespace
data:
  schema.sql: |
    CREATE TABLE IF NOT EXISTS hashtable (
        path TEXT NOT NULL,
        hashed_path VARCHAR(64) AS (SHA2(path, 256)) STORED PRIMARY KEY, -- Not case sensitive
        current_hash VARCHAR(40) NOT NULL, -- Not case sensitive
        current_dtg_latest INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),
        current_dtg_first INT UNSIGNED DEFAULT (`current_dtg_latest`),
        target_hash VARCHAR(40), -- Not case sensitive
        prev_hash VARCHAR(40), -- Not case sensitive
        prev_dtg_latest INT UNSIGNED,
        dirs TEXT,
        files TEXT,
        links TEXT
    );
```

You can also create this ConfigMap using kubectl with a command like:

```bash
kubectl create configmap hashtable-schema --from-file=schema.sql=your-sql-file.sql
```

To use this ConfigMap in a Pod, you can mount it as a volume:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
spec:
  containers:
  - name: app
    image: your-image
    volumeMounts:
    - name: schema-volume
      mountPath: /etc/sql
      readOnly: true
  volumes:
  - name: schema-volume
    configMap:
      name: hashtable-schema
```

The SQL file will be available at `/etc/sql/schema.sql` inside the container.