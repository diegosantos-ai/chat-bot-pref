from datetime import datetime
from zoneinfo import ZoneInfo

class TimeHelper:
    tz = ZoneInfo("America/Sao_Paulo")
    
    @staticmethod
    def now():
        return datetime.now(TimeHelper.tz)
    
    @staticmethod
    def is_after(date_str):
        # "2025-11-30" → compara com hoje
        target = datetime.fromisoformat(date_str).replace(tzinfo=TimeHelper.tz)
        return TimeHelper.now() > target
    
    @staticmethod
    def format_relative(date_str):
        # Garante comparação apenas por data (ignora hora/fuso para contagem de dias)
        target_date = datetime.fromisoformat(date_str).date()
        today = TimeHelper.now().date()
        days = (target_date - today).days
        
        if days < 0:
            return f"há {abs(days)} dias"
        elif days == 0:
            return "hoje"
        return f"em {days} dias"
