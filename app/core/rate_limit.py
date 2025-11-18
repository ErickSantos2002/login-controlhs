# app/core/rate_limit.py

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting simples baseado em memória.

    Rastreia requisições por IP e bloqueia IPs que excedem o limite.
    Para produção em múltiplos servidores, considere usar Redis.
    """

    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        Args:
            app: Aplicação FastAPI
            calls: Número de requisições permitidas
            period: Período em segundos
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        # Dict[IP, List[timestamp]]
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_task = None

    async def dispatch(self, request: Request, call_next):
        # Obter IP do cliente
        client_ip = self._get_client_ip(request)

        # Verificar rate limit
        if not self._is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de requisições excedido. Máximo: {self.calls} requisições por {self.period}s",
                headers={"Retry-After": str(self.period)}
            )

        # Processar requisição
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Obtém o IP real do cliente (considerando proxies)"""
        # Tentar headers de proxy primeiro
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback para IP direto
        return request.client.host if request.client else "unknown"

    def _is_allowed(self, client_ip: str) -> bool:
        """Verifica se o IP está dentro do limite de requisições"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)

        # Limpar requisições antigas
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]

        # Verificar limite
        if len(self.requests[client_ip]) >= self.calls:
            return False

        # Registrar nova requisição
        self.requests[client_ip].append(now)
        return True

    async def cleanup_old_entries(self):
        """Limpa entradas antigas periodicamente (evita memory leak)"""
        while True:
            await asyncio.sleep(300)  # A cada 5 minutos
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.period * 2)

            # Remover IPs sem atividade recente
            ips_to_remove = []
            for ip, timestamps in self.requests.items():
                if not timestamps or timestamps[-1] < cutoff:
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self.requests[ip]


# Decorator para rate limit específico em endpoints
def rate_limit(calls: int = 10, period: int = 60):
    """
    Decorator para aplicar rate limit específico em endpoints.

    Uso:
        @router.post("/login")
        @rate_limit(calls=5, period=60)
        async def login(...):
            ...
    """
    def decorator(func):
        # Armazenar metadata do rate limit
        func._rate_limit = {"calls": calls, "period": period}
        return func
    return decorator
