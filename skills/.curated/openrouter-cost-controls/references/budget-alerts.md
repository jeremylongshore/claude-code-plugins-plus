# Budget Alerts

## Budget Alerts

### Alert System

```python
class BudgetAlertSystem:
    def __init__(self, daily_limit: float, monthly_limit: float):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.alert_thresholds = [0.5, 0.75, 0.9, 1.0]  # 50%, 75%, 90%, 100%
        self.alerts_sent = set()

    def check_and_alert(self, tracker: CostTracker):
        daily = tracker.get_daily_cost()
        monthly = tracker.get_monthly_cost()

        alerts = []

        # Daily alerts
        for threshold in self.alert_thresholds:
            if daily >= self.daily_limit * threshold:
                alert_key = f"daily_{threshold}_{date.today().isoformat()}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "daily",
                        "threshold": threshold,
                        "current": daily,
                        "limit": self.daily_limit
                    })
                    self.alerts_sent.add(alert_key)

        # Monthly alerts
        month = date.today().isoformat()[:7]
        for threshold in self.alert_thresholds:
            if monthly >= self.monthly_limit * threshold:
                alert_key = f"monthly_{threshold}_{month}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "monthly",
                        "threshold": threshold,
                        "current": monthly,
                        "limit": self.monthly_limit
                    })
                    self.alerts_sent.add(alert_key)

        return alerts

    def send_alert(self, alert: dict):
        # Implement your alerting (Slack, email, etc.)
        pct = alert["threshold"] * 100
        print(f"ALERT: {alert['type']} budget at {pct}% "
              f"(${alert['current']:.2f} / ${alert['limit']:.2f})")

alerts = BudgetAlertSystem(daily_limit=50.0, monthly_limit=500.0)
```

### Slack Alert Integration

```python
import requests

def send_slack_alert(webhook_url: str, message: str, level: str = "warning"):
    color = {
        "info": "#36a64f",
        "warning": "#ff9800",
        "critical": "#f44336"
    }.get(level, "#ff9800")

    payload = {
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "OpenRouter Cost Monitor"
        }]
    }

    requests.post(webhook_url, json=payload)

# Usage in alert system
def send_alert(self, alert: dict):
    pct = alert["threshold"] * 100
    level = "critical" if alert["threshold"] >= 0.9 else "warning"

    message = (
        f"*{alert['type'].title()} Budget Alert*\n"
        f"Usage: ${alert['current']:.2f} / ${alert['limit']:.2f} ({pct:.0f}%)"
    )

    send_slack_alert(
        os.environ["SLACK_WEBHOOK_URL"],
        message,
        level
    )
```
