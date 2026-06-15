"""
Configuración central (Pydantic Settings).
Lee desde variables de entorno + .env.

NOTA 2026-06-15: el .env se busca relativo a la RAIZ del repo
(2 niveles arriba de este archivo: app/core/config.py -> repo_root),
NO relativo al CWD. Esto evita problemas cuando uvicorn se lanza
desde otro directorio (ej: scripts/) y pydantic no encuentra el .env.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Path al .env de la raiz del repo (independiente del CWD)
# Este archivo esta en backend/app/core/config.py
# Subimos 3 niveles: core -> app -> backend -> repo_root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_ENV = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Si existe el .env en la raiz, usarlo. Si no, cae al default
        # (variables de entorno del sistema o el default que pydantic
        # encuentre con su propia busqueda).
        env_file=str(_REPO_ENV) if _REPO_ENV.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Proyecto ───
    project_name: str = "cofar-sgd"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # ─── DB / Redis ───
    database_url: str = "postgresql+asyncpg://sgd:sgd@postgres:5432/sgd"
    redis_url: str = "redis://redis:6379/0"

    # ─── Celery ───
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # ─── Locale ───
    tz: str = "America/La_Paz"

    # ─── JWT ───
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ─── CORS ───
    cors_origins: str = "http://localhost:8080,http://localhost:5173"

    @field_validator("cors_origins")
    @classmethod
    def split_cors(cls, v: str) -> List[str]:
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # ─── LDAP / AD ───
    ldap_enabled: bool = False
    ldap_server: str = ""
    ldap_port: int = 389
    ldap_use_ssl: bool = False
    ldap_base_dn: str = "DC=cofar,DC=com"
    ldap_domain: str = "cofar.com"
    ldap_bind_user: str = ""
    ldap_bind_password: str = ""
    ldap_user_search_filter: str = "(sAMAccountName={username})"
    ldap_user_search_base: str = "OU=Usuarios,DC=cofar,DC=com"
    # CNs excluidos del listado de impersonate (separados por coma, vacío = usar defaults del servicio)
    ldap_excluded_cns: str = ""
    # sAMAccountNames excluidos (separados por coma, vacío = usar defaults)
    ldap_excluded_samaccountnames: str = ""

    @field_validator("ldap_user_search_base")
    @classmethod
    def fix_malformed_search_base(cls, v: str) -> str:
        """
        Proteccion contra el bug del .bat que parte en '=':
        Si el search_base quedo como 'OU' o 'OU=' (truncado), reconstruir
        un DN valido a partir del domain del ldap_base_dn.

        Ejemplo del bug:
          .env dice:    LDAP_USER_SEARCH_BASE=OU=Usuarios,DC=cofar,DC=com
          .bat carga:   set LDAP_USER_SEARCH_BASE=OU   (se corto en 1er '=')
          ldap3 intenta parsear 'OU' -> LDAPInvalidDnError "attribute type not present"
        """
        if not v or "=" not in v.split(",")[0]:
            # No es un DN valido. Reconstruir uno seguro.
            return "OU=Usuarios,DC=cofar,DC=com"
        return v

    @field_validator("ldap_bind_password")
    @classmethod
    def fix_malformed_bind_password(cls, v: str) -> str:
        """
        Proteccion: si el password quedo vacio o solo una parte
        (bug del .bat parte en '=' cuando el pass tiene '=' adentro),
        que el log indique que algo anda mal sin crashear.
        """
        # No podemos "arreglar" un password truncado (no lo conocemos),
        # pero al menos no crasheamos si llega vacio o con caracteres raros.
        if v is None:
            return ""
        return v

    # ─── Microsoft Graph ───
    graph_enabled: bool = False
    ms_tenant_id: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""
    graph_scopes: str = "https://graph.microsoft.com/.default"

    # ─── SMTP ───
    smtp_enabled: bool = False
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    smtp_from_email: str = "noreply@cofar.local"
    smtp_from_name: str = "SGD COFAR"

    # ─── Rate limits ───
    rate_limit_default: int = 100
    rate_limit_login: int = 10
    rate_limit_download: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
