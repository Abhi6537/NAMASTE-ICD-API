from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import statistics

class StatsTracker:
    def __init__(self):
        self.total_requests = 0
        self.response_times: List[float] = []
        self.endpoint_counts: Dict[str, int] = defaultdict(int)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.start_time = datetime.utcnow()
        
    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """Record a request with its metrics"""
        self.total_requests += 1
        self.response_times.append(response_time)
        self.endpoint_counts[endpoint] += 1
        self.status_codes[status_code] += 1
        
        # Keep only last 1000 response times to prevent memory issues
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        if not self.response_times:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
        else:
            avg_response_time = statistics.mean(self.response_times)
            min_response_time = min(self.response_times)
            max_response_time = max(self.response_times)
        
        # Calculate success rate
        successful_requests = sum(
            count for status, count in self.status_codes.items() 
            if 200 <= status < 400
        )
        success_rate = (successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_requests": self.total_requests,
            "average_response_time": round(avg_response_time, 2),
            "min_response_time": round(min_response_time, 2),
            "max_response_time": round(max_response_time, 2),
            "success_rate": round(success_rate, 2),
            "uptime_seconds": round(uptime_seconds, 2),
            "recent_response_times": [round(rt, 2) for rt in self.response_times[-100:]],
            "endpoint_counts": dict(self.endpoint_counts),
            "status_code_distribution": dict(self.status_codes),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.__init__()

# Global stats tracker instance
stats_tracker = StatsTracker()