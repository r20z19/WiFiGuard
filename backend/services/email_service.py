import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import get_db
from utils.time_utils import now_str


def get_config():
    conn = get_db()
    row = conn.execute("SELECT * FROM email_config WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return {
            "smtpHost": "smtp.qq.com",
            "smtpPort": 465,
            "email": "",
            "authorizationCode": "",
            "recipientEmail": "",
            "enabled": False,
        }
    return {
        "smtpHost": row["smtp_host"],
        "smtpPort": row["smtp_port"],
        "email": row["email"],
        "authorizationCode": row["authorization_code"],
        "recipientEmail": row["recipient_email"],
        "enabled": bool(row["enabled"]),
    }


def update_config(data):
    conn = get_db()
    conn.execute(
        """UPDATE email_config
           SET smtp_host = ?, smtp_port = ?, email = ?,
               authorization_code = ?, recipient_email = ?, enabled = ?
           WHERE id = 1""",
        (
            data.get("smtpHost", "smtp.qq.com"),
            data.get("smtpPort", 465),
            data.get("email", ""),
            data.get("authorizationCode", ""),
            data.get("recipientEmail", ""),
            1 if data.get("enabled") else 0,
        ),
    )
    conn.commit()
    conn.close()
    return get_config()


def send_test(config):
    try:
        _send_email(
            smtp_host=config["smtpHost"],
            smtp_port=config["smtpPort"],
            sender=config["email"],
            auth_code=config["authorizationCode"],
            recipient=config.get("recipientEmail", config["email"]),
            subject="WiFiGuard 邮箱连接测试",
            body="这是一封来自 WiFiGuard 无线安全防御系统的测试邮件。\n\n如果您收到此邮件，说明邮箱配置成功。",
        )
        return True, "连接测试成功"
    except Exception as e:
        return False, f"连接失败: {str(e)}"


def send_alert(alert_type, severity, source_mac, target_mac, timestamp, suggestion):
    config = get_config()
    if not config["enabled"]:
        return

    subject = f"[WiFiGuard] {alert_type} 告警"
    body = f"""WiFiGuard 检测到无线安全告警：

攻击类型: {alert_type}
严重等级: {severity}
源MAC地址: {source_mac}
目标MAC地址: {target_mac}
告警时间: {timestamp}

处理建议:
{suggestion}

---
此邮件由 WiFiGuard 无线安全防御系统自动发送。
"""

    try:
        _send_email(
            smtp_host=config["smtpHost"],
            smtp_port=config["smtpPort"],
            sender=config["email"],
            auth_code=config["authorizationCode"],
            recipient=config["recipientEmail"],
            subject=subject,
            body=body,
        )
        _record_email(alert_type, config["recipientEmail"], "成功")
    except Exception as e:
        _record_email(alert_type, config["recipientEmail"], "失败")


def get_records():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM email_records ORDER BY time DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [
        {
            "time": r["time"],
            "alertType": r["alert_type"],
            "recipient": r["recipient"],
            "status": r["status"],
        }
        for r in rows
    ]


def _send_email(smtp_host, smtp_port, sender, auth_code, recipient, subject, body):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()

    server.login(sender, auth_code)
    server.sendmail(sender, recipient, msg.as_string())
    server.quit()


def _record_email(alert_type, recipient, status):
    conn = get_db()
    conn.execute(
        "INSERT INTO email_records (time, alert_type, recipient, status) VALUES (?, ?, ?, ?)",
        (now_str(), alert_type, recipient, status),
    )
    conn.commit()
    conn.close()
