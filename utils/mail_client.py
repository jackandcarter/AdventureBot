import logging
import smtplib
import ssl
from typing import Optional

logger = logging.getLogger("MailClient")


class MailClient:
    """Simple SMTP client wrapper configured from loaded settings."""

    def __init__(self, mail_config: dict):
        self.host: Optional[str] = mail_config.get("host")
        self.port: Optional[int] = mail_config.get("port")
        self.username: Optional[str] = mail_config.get("username")
        self.password: Optional[str] = mail_config.get("password")
        self.use_tls: bool = bool(mail_config.get("use_tls"))
        self.use_ssl: bool = bool(mail_config.get("use_ssl"))
        self.timeout: int = int(mail_config.get("timeout", 5))

    def _connect(self):
        if not self.host or not self.port:
            raise ValueError("Mail host and port are required for connection")

        context = ssl.create_default_context()
        if self.use_ssl:
            client = smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=self.timeout)
        else:
            client = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                client.starttls(context=context)

        if self.username and self.password:
            client.login(self.username, self.password)
        return client

    def health_check(self, log: Optional[logging.Logger] = None) -> bool:
        """Attempt to connect and issue a NOOP to validate connectivity."""

        target_logger = log or logger
        try:
            with self._connect() as client:
                client.noop()
            target_logger.info("✉️ Mail connectivity verified for %s:%s", self.host, self.port)
            return True
        except Exception as exc:  # noqa: BLE001 - log all failures
            target_logger.error("❌ Mail health check failed: %s", exc)
            return False
