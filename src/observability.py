"""
Observability and Logging for FOR ME System

Implements observability instrumentation:
- Request tracing
- Tool call events
- Tool result tracking
- Token usage tracking
- Latency metrics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from google.adk.runners import Runner
from google.adk.apps.app import App


class FORMEObservability:
    """
    Observability wrapper for FOR ME system.
    
    Captures:
    - user_message
    - tool_call events
    - tool_result events
    - token usage
    - model → tool → model sequences
    - latencies
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize observability system.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.request_logs = {}
    
    def enable_logging(self, app: App, runner: Runner) -> None:
        """
        Enable logging for app and runner.
        
        Args:
            app: ADK App instance
            runner: ADK Runner instance
        """
        # Logging is handled through custom log methods
        # ADK logging plugins are optional and may not be available in all versions
        pass
    
    def log_request(
        self,
        request_id: str,
        user_id: str,
        user_message: str,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Log a new request.
        
        Args:
            request_id: Unique request identifier
            user_id: User identifier
            user_message: User's message
            session_id: Optional session ID
        """
        self.request_logs[request_id] = {
            "request_id": request_id,
            "user_id": user_id,
            "session_id": session_id,
            "user_message": user_message,
            "timestamp": datetime.now().isoformat(),
            "events": [],
            "tool_calls": [],
            "tool_results": [],
            "token_usage": {},
            "latencies": {},
        }
    
    def log_tool_call(
        self,
        request_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a tool call event.
        
        Args:
            request_id: Request identifier
            tool_name: Name of the tool
            tool_args: Tool arguments
            timestamp: Optional timestamp
        """
        if request_id not in self.request_logs:
            self.log_request(request_id, user_id="unknown", user_message="")
        
        event = {
            "type": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        
        # Defensive copy to prevent shared mutation
        event = json.loads(json.dumps(event, ensure_ascii=True, default=str))
        
        self.request_logs[request_id]["tool_calls"].append(event)
        self.request_logs[request_id]["events"].append(event)
    
    def log_tool_result(
        self,
        request_id: str,
        tool_name: str,
        tool_result: Any,
        latency_ms: Optional[float] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a tool result event.
        
        Args:
            request_id: Request identifier
            tool_name: Name of the tool
            tool_result: Tool result
            latency_ms: Latency in milliseconds
            timestamp: Optional timestamp
        """
        if request_id not in self.request_logs:
            self.log_request(request_id, user_id="unknown", user_message="")
        
        # Prevent crash if tool_result is not JSON-serializable
        tool_result_str = json.dumps(tool_result, ensure_ascii=True, default=str)[:500]
        
        event = {
            "type": "tool_result",
            "tool_name": tool_name,
            "tool_result": tool_result_str,
            "latency_ms": latency_ms,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        
        # Defensive copy to prevent shared mutation
        event = json.loads(json.dumps(event, ensure_ascii=True, default=str))
        
        self.request_logs[request_id]["tool_results"].append(event)
        self.request_logs[request_id]["events"].append(event)
        
        if latency_ms:
            if "tool_latencies" not in self.request_logs[request_id]["latencies"]:
                self.request_logs[request_id]["latencies"]["tool_latencies"] = {}
            # Support multiple calls with same tool name
            self.request_logs[request_id]["latencies"]["tool_latencies"].setdefault(tool_name, []).append(latency_ms)
    
    def log_token_usage(
        self,
        request_id: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Log token usage.
        
        Args:
            request_id: Request identifier
            model_name: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens
        """
        if request_id not in self.request_logs:
            self.log_request(request_id, user_id="unknown", user_message="")
        
        # Type-safe fallback for model_name
        if not model_name:
            model_name = "unknown_model"
        
        self.request_logs[request_id]["token_usage"][model_name] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
    
    def save_log(self, request_id: str) -> None:
        """
        Save log to file.
        
        Args:
            request_id: Request identifier
        """
        if request_id not in self.request_logs:
            return
        
        log_file = self.log_dir / f"{request_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            # Add final "request completed" marker
            self.request_logs[request_id]["completed_at"] = datetime.now().isoformat()
            json.dump(self.request_logs[request_id], f, indent=2, ensure_ascii=True, default=str)
    
    def print_trace(self, request_id: str) -> None:
        """
        Print event timeline for a request.
    
    Args:
            request_id: Request identifier
        """
        if request_id not in self.request_logs:
            print(f"Request {request_id} not found")
            return
        
        log = self.request_logs[request_id]
        
        print(f"\n{'='*70}")
        print(f"Request Trace: {request_id}")
        print(f"{'='*70}")
        print(f"User: {log['user_id']}")
        print(f"Session: {log.get('session_id', 'N/A')}")
        print(f"Message: {log['user_message'][:100]}...")
        print(f"Timestamp: {log['timestamp']}")
        print(f"\n{'='*70}")
        print("Event Timeline:")
        print(f"{'='*70}")
        
        for i, event in enumerate(log["events"], 1):
            event_type = event["type"]
            timestamp = event.get("timestamp", "N/A")
            
            if event_type == "tool_call":
                tool_name = event["tool_name"]
                print(f"{i}. [{timestamp}] TOOL CALL: {tool_name}")
                print(f"   Args: {json.dumps(event['tool_args'], indent=6, ensure_ascii=True, default=str)[:200]}")
            
            elif event_type == "tool_result":
                tool_name = event["tool_name"]
                latency = event.get("latency_ms")
                print(f"{i}. [{timestamp}] TOOL RESULT: {tool_name}")
                if latency:
                    print(f"   Latency: {latency:.2f}ms")
                print(f"   Result: {event['tool_result'][:200]}...")
        
        print(f"\n{'='*70}")
        print("Token Usage:")
        print(f"{'='*70}")
        for model, usage in log.get("token_usage", {}).items():
            print(f"{model}:")
            print(f"  Input: {usage['input_tokens']}")
            print(f"  Output: {usage['output_tokens']}")
            print(f"  Total: {usage['total_tokens']}")
        
        print(f"{'='*70}\n")
    
    def get_all_logs(self) -> Dict[str, Any]:
        """
        Get all request logs.
        
        Returns:
            Dictionary of all request logs
        """
        return self.request_logs


# Global observability instance
_observability = None


def get_observability() -> FORMEObservability:
    """
    Get global observability instance.
    
    Returns:
        FORMEObservability instance
    """
    global _observability
    if _observability is None:
        _observability = FORMEObservability()
    return _observability
