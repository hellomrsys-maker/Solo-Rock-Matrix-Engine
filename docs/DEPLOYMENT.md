# SOLO ROCK Deployment Guide

Production deployment of SOLO ROCK Hardware Orchestrator on Linux (systemd), Windows (Service), and Kubernetes.

## Prerequisites

- **Python 3.10+** (Linux/Windows/macOS)
- **Dependencies**: `pip install -r requirements.txt` (psutil, pyyaml)
- **Hardware Access**: CPU temperature sensor access (may require permissions)
- **Optional**: Email SMTP server for alerting, Slack webhook, or custom monitoring integration

### Permissions Required

**Linux/macOS:**
- Read-only telemetry: No special permissions needed
- CPU throttling (EMERGENCY mode): May require `sudo` or CAP_SYS_ADMIN capability

**Windows:**
- Read-only telemetry: Standard user permissions
- CPU throttling (EMERGENCY mode): Administrator privileges or SYSTEM account

---

## Linux/systemd Deployment

### Installation

```bash
# Clone repository
git clone https://github.com/hellomrsys-maker/solo-rock-matrix-engine.git
cd solo-rock-matrix-engine
pip install -r requirements.txt

# Create systemd service
sudo cp docs/systemd/solo-rock.service /etc/systemd/system/
sudo systemctl daemon-reload

# Create solo-rock user (optional, for security)
sudo useradd -r -s /bin/false solo-rock 2>/dev/null || true

# Set permissions
sudo chown solo-rock:solo-rock /opt/solo-rock/
sudo mkdir -p /var/log/solo-rock/
sudo chown solo-rock:solo-rock /var/log/solo-rock/
```

### Configuration

Create `/etc/solo-rock/config.yaml`:

```yaml
thermal:
  warning_celsius: 80
  critical_celsius: 90
cpu:
  load_high_percent: 85
ram:
  critical_percent: 97

# Optional: Configure alerting
alerting:
  enabled: true
  backends:
    - type: email
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      sender: "alerts@example.com"
      recipients: ["ops@example.com"]
```

### Starting the Service

```bash
# Enable on boot
sudo systemctl enable solo-rock

# Start immediately
sudo systemctl start solo-rock

# Monitor logs
sudo journalctl -u solo-rock -f

# Check status
sudo systemctl status solo-rock
```

### Environment Variables

Set in `/etc/systemd/system/solo-rock.service.d/override.conf`:

```ini
[Service]
Environment="SOLO_ROCK_EMAIL_USER=your-email@gmail.com"
Environment="SOLO_ROCK_EMAIL_PASS=your-app-password"
Environment="SOLO_ROCK_SLACK_WEBHOOK=https://hooks.slack.com/services/..."
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart solo-rock
```

### Managing the Service

```bash
# Stop
sudo systemctl stop solo-rock

# Restart
sudo systemctl restart solo-rock

# Disable on boot
sudo systemctl disable solo-rock

# View recent logs
sudo journalctl -u solo-rock -n 50

# View since last boot
sudo journalctl -u solo-rock -b
```

---

## Windows Service Deployment

### Installation

```powershell
# Run PowerShell as Administrator
# Navigate to repository directory
cd C:\path\to\solo-rock-matrix-engine

# Install service
.\docs\windows\install-service.ps1

# Verify installation
Get-Service SoloRock
```

### Configuration

Create `C:\Program Files\Solo-Rock\config.yaml`:

```yaml
thermal:
  warning_celsius: 80
  critical_celsius: 90
cpu:
  load_high_percent: 85
ram:
  critical_percent: 97

alerting:
  enabled: true
  backends:
    - type: email
      smtp_server: "smtp.office365.com"
      smtp_port: 587
      sender: "alerts@example.com"
      recipients: ["ops@example.com"]
```

### Environment Variables

Set via PowerShell (as Administrator):

```powershell
# Set for SYSTEM account (used by service)
[Environment]::SetEnvironmentVariable(
    "SOLO_ROCK_EMAIL_USER",
    "your-email@domain.com",
    "Machine"
)

[Environment]::SetEnvironmentVariable(
    "SOLO_ROCK_EMAIL_PASS",
    "your-app-password",
    "Machine"
)

[Environment]::SetEnvironmentVariable(
    "SOLO_ROCK_SLACK_WEBHOOK",
    "https://hooks.slack.com/services/...",
    "Machine"
)

# Restart service for env vars to take effect
Restart-Service SoloRock
```

### Managing the Service

```powershell
# Start
Start-Service SoloRock

# Stop
Stop-Service SoloRock

# Restart
Restart-Service SoloRock

# Check status
Get-Service SoloRock

# View logs (Event Viewer)
# Windows Logs → Application → Source: SoloRock

# Uninstall
.\docs\windows\uninstall-service.ps1
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.20+
- `kubectl` configured with cluster access
- Sufficient resources: 100m CPU, 128Mi memory per pod (minimum)

### Quick Start

```bash
# Apply manifests
kubectl apply -f docs/kubernetes/configmap.yaml
kubectl apply -f docs/kubernetes/deployment.yaml
kubectl apply -f docs/kubernetes/service.yaml

# Verify deployment
kubectl get deployment solo-rock
kubectl get pods -l app=solo-rock

# View logs
kubectl logs -f deployment/solo-rock

# Port-forward (optional, if using dashboard)
kubectl port-forward svc/solo-rock 8080:8080
```

### Configuration

Edit `docs/kubernetes/configmap.yaml` before deploying:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: solo-rock-config
  namespace: default
data:
  config.yaml: |
    thermal:
      warning_celsius: 80
      critical_celsius: 90
    cpu:
      load_high_percent: 85
    ram:
      critical_percent: 97
    alerting:
      enabled: true
      backends:
        - type: slack
          webhook_url: ${SOLO_ROCK_SLACK_WEBHOOK}
```

### Secrets Management

Store sensitive data (credentials) as Kubernetes Secrets:

```bash
# Create secret from literals
kubectl create secret generic solo-rock-alerts \
  --from-literal=email-user=your-email@gmail.com \
  --from-literal=email-pass=your-app-password \
  --from-literal=slack-webhook=https://hooks.slack.com/...

# Or from env file
kubectl create secret generic solo-rock-alerts --from-env-file=.env.secret
```

Reference in deployment via environment variables.

### Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment solo-rock --replicas=3

# Watch scaling
kubectl get pods -l app=solo-rock -w
```

### Updating Configuration

```bash
# Edit ConfigMap
kubectl edit configmap solo-rock-config

# Rolling restart to apply changes
kubectl rollout restart deployment/solo-rock

# Monitor rollout
kubectl rollout status deployment/solo-rock
```

### Monitoring

```bash
# Get pod details
kubectl describe pod <pod-name>

# Get deployment details
kubectl describe deployment solo-rock

# Check resource usage
kubectl top pod -l app=solo-rock

# Stream logs from all pods
kubectl logs -f deployment/solo-rock --all-containers=true --timestamps=true
```

### Helm Charts (Optional)

For larger deployments, create a Helm chart:

```bash
helm create solo-rock
# Edit helm/values.yaml for your environment
helm install solo-rock ./helm
```

---

## Troubleshooting

### Issue: Service Won't Start

**Linux:**
```bash
# Check for errors
sudo journalctl -u solo-rock -n 20
sudo systemctl status solo-rock -l

# Verify config file syntax
python -c "from config import load_config; load_config('/etc/solo-rock/config.yaml')"
```

**Windows:**
```powershell
# Check Event Viewer: Windows Logs → Application
Get-EventLog Application -Source SoloRock -Newest 10

# Test config
python -c "from config import load_config; load_config('C:\\Program Files\\Solo-Rock\\config.yaml')"
```

### Issue: Alerts Not Sending

1. **Check configuration**: Verify alerting section in config.yaml
2. **Check credentials**: Ensure environment variables are set
3. **Test email**: 
   ```bash
   python -c "
   from alerting.email_alerter import EmailAlerter
   alerter = EmailAlerter(config={'smtp_server': 'smtp.gmail.com', 'smtp_port': 587})
   print('Email alerter loaded successfully')
   "
   ```
4. **Check firewall**: SMTP (port 587), Slack webhooks must be accessible
5. **Check logs**: Look for "[AlertManager]" entries

### Issue: High CPU/Memory Usage

1. **Check database size**: `ls -lh solo_rock.db`
2. **Run cleanup**: Database auto-rotates events older than 30 days
3. **Reduce refresh interval**: Increase `refresh_interval` in config if needed
4. **Check telemetry**: Verify hardware sensor reads aren't expensive

### Issue: Permission Denied (CPU Temperature)

**Linux:**
```bash
# Check sensor permissions
cat /proc/stat  # Should be readable

# Grant permissions (if using coretemp)
sudo chmod +r /sys/class/thermal/thermal_zone*/temp

# Or run as root (less secure)
sudo -u solo-rock ...
```

**Windows:**
- Run service as SYSTEM (default) or Administrator account
- Check antivirus isn't blocking sensor access

---

## Performance Tuning

### Database Size Management

```bash
# Check database size
sqlite3 solo_rock.db "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"

# Manual cleanup (keeps last 30 days)
python -c "
from diagnostics.logger import EventLogger
logger = EventLogger()
logger.cleanup_old_entries(days=30)
"

# Archive old events (weekly backup)
sqlite3 solo_rock.db "SELECT COUNT(*) FROM events WHERE timestamp < datetime('now', '-7 days');"
```

### Monitoring Overhead

Default refresh interval: 2.0 seconds. Adjust in config or CLI:

```bash
# Longer interval = lower overhead
python monitor_realtime.py --interval 5.0 --duration 3600

# Lower refresh = more responsive
python monitor_realtime.py --interval 0.5 --duration 3600
```

### Alerting Rate Limiting

Default: max 1 alert per minute per backend (prevents spam). Modify in `alerting/base.py` if needed.

---

## Security Considerations

### API Keys & Credentials

**Never commit secrets to git:**
```bash
# Use environment variables
export SOLO_ROCK_EMAIL_USER="..."
export SOLO_ROCK_EMAIL_PASS="..."
export SOLO_ROCK_SLACK_WEBHOOK="..."

# Or create .env file (add to .gitignore)
source .env
```

### Linux Service Isolation

```bash
# Run as unprivileged user
sudo useradd -r -s /bin/false solo-rock

# Restrict file permissions
sudo chmod 600 /etc/solo-rock/config.yaml
sudo chown solo-rock:solo-rock /var/log/solo-rock/
```

### Windows Service Isolation

- Run as SYSTEM (default, highest privilege, needed for throttling)
- Or: Create service account with CAP_SYS_ADMIN equivalent privileges
- Restrict access to config files via NTFS permissions

### HTTPS for Webhooks

Ensure custom webhook URLs use HTTPS with valid certificates. Webhook alerter validates TLS certificates by default.

---

## Backup & Recovery

### Database Backup

```bash
# Copy database (while service running)
cp solo_rock.db solo_rock.db.$(date +%Y%m%d_%H%M%S).bak

# Or SQL export
sqlite3 solo_rock.db ".mode list" "SELECT * FROM events;" > events_backup.sql
```

### Configuration Backup

```bash
# Linux
sudo cp /etc/solo-rock/config.yaml config.yaml.bak

# Windows
Copy-Item "C:\Program Files\Solo-Rock\config.yaml" "config.yaml.bak"

# Git (for version control)
git add docs/examples/config.*.yaml
```

### Disaster Recovery

1. Restore config.yaml
2. Delete or archive solo_rock.db (will recreate on restart)
3. Restart service
4. Verify with: `python solo_rock_cli.py diagnose`

---

## Monitoring & Observability

### System Health Checks

```bash
# CLI diagnostics
python solo_rock_cli.py diagnose

# Benchmark test
python solo_rock_cli.py benchmark --ticks 20

# Real-time monitoring
python solo_rock_cli.py monitor --duration 60
```

### Log Analysis

**Linux:**
```bash
# Real-time tail
sudo journalctl -u solo-rock -f

# Search for EMERGENCY events
sudo journalctl -u solo-rock | grep EMERGENCY

# Export to file
sudo journalctl -u solo-rock > solo-rock.log
```

**Windows:**
```powershell
# Get recent events
Get-EventLog Application -Source SoloRock -Newest 20

# Export to CSV
Get-EventLog Application -Source SoloRock | Export-Csv -Path solo-rock-events.csv
```

### Database Analytics

```python
from analytics.query import TelemetryAnalyzer
analyzer = TelemetryAnalyzer()

# Last hour statistics
stats = analyzer.get_performance_metrics(hours=1)
print(stats)

# Thermal trend
trend = analyzer.detect_thermal_trend(minutes=30)
print(f"Temperature rising: {trend}")

# Decision distribution
dist = analyzer.get_decision_distribution(hours=1)
print(f"Decision breakdown: {dist}")
```

---

## Upgrading

### Update to Latest

```bash
# Pull latest code
git fetch origin
git checkout origin/main

# Install updated dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart solo-rock  # Linux
Restart-Service SoloRock           # Windows
kubectl rollout restart deployment/solo-rock  # K8s
```

### Breaking Changes

Check GitHub releases and migration guide before updating.

---

## Support & Troubleshooting

- **Issues**: https://github.com/hellomrsys-maker/solo-rock-matrix-engine/issues
- **Documentation**: https://github.com/hellomrsys-maker/solo-rock-matrix-engine/wiki
- **CLI Help**: `python solo_rock_cli.py --help`

---

## Quick Reference

| Platform | Start | Stop | Logs | Config |
|----------|-------|------|------|--------|
| **Linux (systemd)** | `sudo systemctl start solo-rock` | `sudo systemctl stop solo-rock` | `sudo journalctl -u solo-rock -f` | `/etc/solo-rock/config.yaml` |
| **Windows (Service)** | `Start-Service SoloRock` | `Stop-Service SoloRock` | Event Viewer | `C:\Program Files\Solo-Rock\config.yaml` |
| **Kubernetes** | `kubectl apply -f ...` | `kubectl delete deployment solo-rock` | `kubectl logs -f deployment/solo-rock` | ConfigMap: `solo-rock-config` |

---

**Last Updated:** 2026-01-16  
**Version:** 1.0  
**License:** MIT
