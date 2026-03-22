"""Health check module for monitoring bot status."""
import os
import time
import logging
import json
from pathlib import Path
from core.config import PID_FILE, LOGS_DIR

log = logging.getLogger("core.health")

class HealthChecker:
    """Health monitoring and reporting."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_activity = time.time()
        self.message_count = 0
        self.error_count = 0
    
    def mark_activity(self):
        """Mark recent activity."""
        self.last_activity = time.time()
    
    def increment_messages(self):
        """Increment message counter."""
        self.message_count += 1
        self.mark_activity()
    
    def increment_errors(self):
        """Increment error counter."""
        self.error_count += 1
        self.mark_activity()
    
    def get_status(self) -> dict:
        """Get current health status."""
        now = time.time()
        uptime = now - self.start_time
        last_activity_ago = now - self.last_activity
        
        # Health checks
        is_healthy = True
        issues = []
        
        # Check if too long without activity (might be stuck)
        if last_activity_ago > 600:  # 10 minutes
            is_healthy = False
            issues.append("No activity for too long")
        
        # Check if error rate is too high
        if self.message_count > 0:
            error_rate = self.error_count / self.message_count
            if error_rate > 0.1:  # More than 10% errors
                is_healthy = False
                issues.append(f"High error rate: {error_rate:.2%}")
        
        # Check PID file
        if not os.path.exists(PID_FILE):
            is_healthy = False
            issues.append("PID file missing")
        
        return {
            "healthy": is_healthy,
            "uptime_seconds": int(uptime),
            "last_activity_ago": int(last_activity_ago),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "issues": issues,
            "timestamp": int(now)
        }
    
    def save_status(self):
        """Save status to file for external monitoring."""
        status_file = Path(LOGS_DIR) / "health.json"
        try:
            status = self.get_status()
            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save health status: {e}")

# Global health checker instance
health_checker = HealthChecker()