import datetime
from .config import prefs

class QuotaManager:
    def __init__(self):
        self.load_state()

    def load_state(self):
        # Ensure we have the latest state
        self.daily_quotas = prefs.get('daily_quotas', {})
        self.last_reset = prefs.get('last_reset_date', "")
        self.check_reset()

    def check_reset(self):
        today = datetime.date.today().isoformat()
        if self.last_reset != today:
            # It's a new day, reset everything
            print(f"[SmartSummary] New day detected ({today}). Resetting quotas.")
            self.daily_quotas = {} # Reset specific usage counts
            # Note: We don't delete the limits, just the usage.
            # Wait, tracking usage vs limits. 
            # Let's say daily_quotas stores: { "model_id": { "usage": 5, "limit": 10 } }
            # Or better: config stores limits, this stores usage.
            # Let's separate: 
            # prefs['api_configs'] has limits.
            # prefs['usage_stats'] has usage.
            
            prefs['usage_stats'] = {} 
            prefs['last_reset_date'] = today
            self.last_reset = today
            # Trigger save
            pass

    def check_quota(self, model_id, cost=1):
        """
        Returns True if model has enough quota.
        """
        self.check_reset()
        
        # Get limit from config
        api_configs = prefs.get('api_configs', [])
        limit = 0
        for conf in api_configs:
            if conf.get('id') == model_id:
                limit = conf.get('daily_limit', 0)
                break
        
        if limit <= 0:
            return True # 0 means unlimited (or handle as disabled? Let's assume 0 is unlimited for now or handle in UI)
            # Actually, typically 0 might mean no limit, but user said "Quota Exceeded" if limit reached.
            # Let's assume 0 meant unlimited.
        
        usage_stats = prefs.get('usage_stats', {})
        current_usage = usage_stats.get(model_id, 0)
        
        if current_usage + cost > limit:
            return False
            
        return True

    def increment_usage(self, model_id, cost=1):
        self.check_reset()
        usage_stats = prefs.get('usage_stats', {})
        current_usage = usage_stats.get(model_id, 0)
        usage_stats[model_id] = current_usage + cost
        prefs['usage_stats'] = usage_stats
