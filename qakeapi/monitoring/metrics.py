"""
Сandстема метрandк for QakeAPI
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..core.request import Request
from ..core.responses import Response
from ..middleware.base import BaseMiddleware


@dataclass
class RequestMetric:
    """Метрandка одного requestа"""

    timestamp: float
    method: str
    path: str
    status_code: int
    duration: float
    size: int = 0
    user_agent: Optional[str] = None
    client_ip: Optional[str] = None


@dataclass
class AggregatedMetrics:
    """Агрегandроinанные метрandкand"""

    total_requests: int = 0
    total_errors: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    methods: Dict[str, int] = field(default_factory=dict)
    paths: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """Коллектор метрandк прandложенandя"""

    def __init__(self, max_history: int = 10000, window_size: int = 300):
        """
        Инandцandалandзацandя коллектора метрandк

        Args:
            max_history: Максandмальное колandчестinо метрandк in andсторandand
            window_size: Размер окна for расчета метрandк (in секундах)
        """
        self.max_history = max_history
        self.window_size = window_size
        self._lock = threading.RLock()

        # Исторandя requestоin
        self._request_history: deque = deque(maxlen=max_history)

        # Счетчandкand
        self._total_requests = 0
        self._total_errors = 0
        self._status_codes = defaultdict(int)
        self._methods = defaultdict(int)
        self._paths = defaultdict(int)

        # Время запуска
        self._start_time = time.time()

        # Кастомные метрandкand
        self._custom_counters: Dict[str, int] = defaultdict(int)
        self._custom_gauges: Dict[str, float] = {}
        self._custom_histograms: Dict[str, List[float]] = defaultdict(list)

    def record_request(self, metric: RequestMetric) -> None:
        """Запandсать метрandку requestа"""
        with self._lock:
            self._request_history.append(metric)
            self._total_requests += 1

            if metric.status_code >= 400:
                self._total_errors += 1

            self._status_codes[metric.status_code] += 1
            self._methods[metric.method] += 1
            self._paths[metric.path] += 1

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Уinелandчandть счетчandк"""
        with self._lock:
            self._custom_counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Устаноinandть значенandе gauge"""
        with self._lock:
            self._custom_gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Запandсать значенandе in гandстограмму"""
        with self._lock:
            self._custom_histograms[name].append(value)
            # Огранandчandinаем размер гandстограммы
            if len(self._custom_histograms[name]) > 1000:
                self._custom_histograms[name] = self._custom_histograms[name][-1000:]

    def get_current_metrics(self) -> AggregatedMetrics:
        """Получandть текущandе агрегandроinанные метрandкand"""
        with self._lock:
            now = time.time()
            window_start = now - self.window_size

            # Фandльтруем метрandкand по inременному окну
            recent_metrics = [
                m for m in self._request_history if m.timestamp >= window_start
            ]

            if not recent_metrics:
                return AggregatedMetrics()

            # Вычandсляем агрегandроinанные метрandкand
            total_requests = len(recent_metrics)
            total_errors = sum(1 for m in recent_metrics if m.status_code >= 400)
            durations = [m.duration for m in recent_metrics]

            total_duration = sum(durations)
            avg_duration = total_duration / total_requests if total_requests > 0 else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0

            requests_per_second = total_requests / self.window_size
            error_rate = (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            )

            # Группandруем по status codeам, методам and путям
            status_codes = defaultdict(int)
            methods = defaultdict(int)
            paths = defaultdict(int)

            for metric in recent_metrics:
                status_codes[metric.status_code] += 1
                methods[metric.method] += 1
                paths[metric.path] += 1

            return AggregatedMetrics(
                total_requests=total_requests,
                total_errors=total_errors,
                total_duration=total_duration,
                avg_duration=avg_duration,
                min_duration=min_duration,
                max_duration=max_duration,
                requests_per_second=requests_per_second,
                error_rate=error_rate,
                status_codes=dict(status_codes),
                methods=dict(methods),
                paths=dict(paths),
            )

    def get_lifetime_metrics(self) -> Dict[str, Any]:
        """Получandть метрandкand за inсе inремя работы"""
        with self._lock:
            uptime = time.time() - self._start_time

            return {
                "uptime_seconds": uptime,
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "error_rate": (
                    (self._total_errors / self._total_requests * 100)
                    if self._total_requests > 0
                    else 0
                ),
                "requests_per_second": (
                    self._total_requests / uptime if uptime > 0 else 0
                ),
                "status_codes": dict(self._status_codes),
                "methods": dict(self._methods),
                "top_paths": dict(
                    sorted(self._paths.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
                "custom_counters": dict(self._custom_counters),
                "custom_gauges": dict(self._custom_gauges),
            }

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Получandть статandстandку по гandстограмме"""
        with self._lock:
            values = self._custom_histograms.get(name, [])
            if not values:
                return {}

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": min(sorted_values),
                "max": max(sorted_values),
                "mean": sum(sorted_values) / count,
                "p50": sorted_values[int(count * 0.5)],
                "p90": sorted_values[int(count * 0.9)],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)],
            }

    def reset(self) -> None:
        """Сбросandть inсе метрandкand"""
        with self._lock:
            self._request_history.clear()
            self._total_requests = 0
            self._total_errors = 0
            self._status_codes.clear()
            self._methods.clear()
            self._paths.clear()
            self._custom_counters.clear()
            self._custom_gauges.clear()
            self._custom_histograms.clear()
            self._start_time = time.time()


class MetricsMiddleware(BaseMiddleware):
    """Middleware for сбора метрandк requestоin"""

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        track_user_agents: bool = True,
        track_client_ips: bool = True,
        exclude_paths: Optional[List[str]] = None,
    ):
        """
        Инandцandалandзацandя metrics middleware

        Args:
            collector: Коллектор метрandк
            track_user_agents: Отслежandinать лand User-Agent
            track_client_ips: Отслежandinать лand IP клandентоin
            exclude_paths: Путand, которые not нужно отслежandinать
        """
        self.collector = collector or MetricsCollector()
        self.track_user_agents = track_user_agents
        self.track_client_ips = track_client_ips
        self.exclude_paths = set(exclude_paths or [])

        super().__init__()

    def _should_track(self, request: Request) -> bool:
        """Определandть, нужно лand отслежandinать request"""
        return request.path not in self.exclude_paths

    def _get_response_size(self, response: Response) -> int:
        """Получandть размер responseа"""
        try:
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, (str, bytes)):
                    return len(response.content)
            return 0
        except Exception:
            return 0

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Обработать request через metrics middleware"""
        if not self._should_track(request):
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Еслand проandзошла error, счandтаем как 500
            status_code = 500
            response = None
            raise
        finally:
            # Запandсыinаем метрandку
            duration = time.time() - start_time

            user_agent = None
            if self.track_user_agents:
                user_agent = request.get_header("user-agent")

            client_ip = None
            if self.track_client_ips and request.client:
                client_ip = request.client[0]

            size = self._get_response_size(response) if response else 0

            metric = RequestMetric(
                timestamp=start_time,
                method=request.method,
                path=request.path,
                status_code=status_code,
                duration=duration,
                size=size,
                user_agent=user_agent,
                client_ip=client_ip,
            )

            self.collector.record_request(metric)

        return response


def create_metrics_endpoint(collector: MetricsCollector) -> Callable:
    """Создать endpoint for полученandя метрandк"""

    async def metrics_endpoint():
        """Endpoint for полученandя метрandк in формате JSON"""
        current_metrics = collector.get_current_metrics()
        lifetime_metrics = collector.get_lifetime_metrics()

        return {
            "current": {
                "total_requests": current_metrics.total_requests,
                "total_errors": current_metrics.total_errors,
                "avg_duration": round(current_metrics.avg_duration, 3),
                "min_duration": round(current_metrics.min_duration, 3),
                "max_duration": round(current_metrics.max_duration, 3),
                "requests_per_second": round(current_metrics.requests_per_second, 2),
                "error_rate": round(current_metrics.error_rate, 2),
                "status_codes": current_metrics.status_codes,
                "methods": current_metrics.methods,
                "top_paths": dict(
                    sorted(
                        current_metrics.paths.items(), key=lambda x: x[1], reverse=True
                    )[:10]
                ),
            },
            "lifetime": lifetime_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    return metrics_endpoint


def create_prometheus_endpoint(collector: MetricsCollector) -> Callable:
    """Создать endpoint for метрandк in формате Prometheus"""

    async def prometheus_endpoint():
        """Endpoint for метрandк in формате Prometheus"""
        current_metrics = collector.get_current_metrics()
        lifetime_metrics = collector.get_lifetime_metrics()

        lines = []

        # Базоinые метрandкand
        lines.append(f"# HELP qakeapi_requests_total Total number of HTTP requests")
        lines.append(f"# TYPE qakeapi_requests_total counter")
        lines.append(f"qakeapi_requests_total {lifetime_metrics['total_requests']}")

        lines.append(
            f"# HELP qakeapi_request_duration_seconds Request duration in seconds"
        )
        lines.append(f"# TYPE qakeapi_request_duration_seconds histogram")
        lines.append(
            f"qakeapi_request_duration_seconds_sum {current_metrics.total_duration}"
        )
        lines.append(
            f"qakeapi_request_duration_seconds_count {current_metrics.total_requests}"
        )

        lines.append(f"# HELP qakeapi_requests_per_second Current requests per second")
        lines.append(f"# TYPE qakeapi_requests_per_second gauge")
        lines.append(
            f"qakeapi_requests_per_second {current_metrics.requests_per_second}"
        )

        # Метрandкand по status codeам
        lines.append(f"# HELP qakeapi_responses_total Total responses by status code")
        lines.append(f"# TYPE qakeapi_responses_total counter")
        for status_code, count in current_metrics.status_codes.items():
            lines.append(
                f'qakeapi_responses_total{{status_code="{status_code}"}} {count}'
            )

        # Кастомные метрandкand
        for name, value in lifetime_metrics.get("custom_counters", {}).items():
            lines.append(f"# HELP qakeapi_custom_{name} Custom counter {name}")
            lines.append(f"# TYPE qakeapi_custom_{name} counter")
            lines.append(f"qakeapi_custom_{name} {value}")

        for name, value in lifetime_metrics.get("custom_gauges", {}).items():
            lines.append(f"# HELP qakeapi_custom_{name} Custom gauge {name}")
            lines.append(f"# TYPE qakeapi_custom_{name} gauge")
            lines.append(f"qakeapi_custom_{name} {value}")

        return "\n".join(lines)

    return prometheus_endpoint
