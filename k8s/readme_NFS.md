There are two primary ways to mount an NFSv3 share into a Kubernetes container using YAML files: 
1. Directly within the Pod Definition: 
This method involves defining the NFS share as a volume directly within your Pod's YAML definition. 

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nfs-pod
spec:
  containers:
  - name: my-container
    image: alpine # Or your desired container image
    volumeMounts:
    - name: nfs-volume
      mountPath: /mnt/nfs # The path within the container where the NFS share will be mounted
  volumes:
  - name: nfs-volume
    nfs:
      server: your-nfs-server.example.com # Replace with your NFS server's IP or hostname
      path: /path/to/your/share # Replace with the exported path on your NFS server
```
This method uses the volumeMounts and volumes fields within the Pod definition to specify the mount path inside the container and define the NFS volume, including the server IP/hostname and the path to the share. 
2. Using PersistentVolumes (PV) and PersistentVolumeClaims (PVC): 
This approach is recommended for managing the NFS share lifecycle separately from the Pod and is suitable for operators who want to offer a range of NFS shares for users to consume. It involves defining a PersistentVolume (PV) to represent the NFS share and a PersistentVolumeClaim (PVC) to request access to the PV. The Pod then references the PVC. 

PersistentVolume (PV) definition (e.g., nfs-pv.yaml):
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 10Gi # Adjust the storage size as needed
  accessModes:
    - ReadWriteMany # Or other desired access modes
  persistentVolumeReclaimPolicy: Retain # Or Recycle/Delete
  nfs:
    server: your-nfs-server.example.com # Replace with your NFS server's IP or hostname
    path: /path/to/your/share # Replace with the exported path on your NFS server
  mountOptions: # Optional mount options
    - vers=3 # Specify NFSv3 explicitly if needed
    - hard # Or soft
```
PersistentVolumeClaim (PVC) definition (e.g., nfs-pvc.yaml):
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:
    - ReadWriteMany # Match the access modes in the PV
  resources:
    requests:
      storage: 10Gi # Request the storage size
  volumeName: nfs-pv # Link to the PersistentVolume name
```

Pod definition referencing the PVC (e.g., nfs-pod-with-pvc.yaml):
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app-pod
spec:
  containers:
  - name: app-container
    image: nginx # Or your desired container image
    volumeMounts:
    - name: app-data
      mountPath: /usr/share/nginx/html # Mount point within the container
  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: nfs-pvc # Link to the PersistentVolumeClaim
```

Key Points:
Ensure your NFS server is configured to export the share and allows access from your Kubernetes cluster nodes.
Consider file permissions and user mapping between the NFS server and containers.
Optional NFS mount options like vers=3, hard, or soft can be specified in the mountOptions field of the PV.
Verify the NFS share is correctly mounted after deploying the Pod. 
Remember to replace placeholders with your actual NFS server details. 