
## Here is how to setup with puppet to run the docker-compose automatically

Create a systemd service to automatically start the compose stack on boot. 
Create `/etc/systemd/system/squishy-app.service`:

```ini
[Unit]
Description=Squishy Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/your/docker-compose/directory
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Then enable it:
```bash
sudo systemctl enable squishy-app.service
sudo systemctl start squishy-app.service
```

And add these entries to the host's crontab:

```cron
0 * * * * docker start squishy_integrity
*/10 * * * * docker start squishy_coordinator
```