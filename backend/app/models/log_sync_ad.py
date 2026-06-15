"""
Modelo: LogSyncAd
Historial de sincronizaciones con Active Directory.
Triggered por: botón manual + job diario 00:05.
"""
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoSync(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATICO = "automatico"


class ResultadoSync(str, enum.Enum):
    EXITO = "exito"
    ERROR = "error"
    PARCIAL = "parcial"  # Algunos usuarios actualizados, otros no


class LogSyncAd(Base):
    __tablename__ = "log_sincronizacion_ad"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Manual (botón) o automático (job)
    tipo: Mapped[str] = mapped_column(
        SAEnum(TipoSync, name="tipo_sync_ad", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # Éxito, error, parcial
    resultado: Mapped[str] = mapped_column(
        SAEnum(ResultadoSync, name="resultado_sync_ad", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # Quién disparó (null si fue automático)
    triggered_by_user_id: Mapped[int | None] = mapped_column(nullable=True)

    # Estadísticas
    usuarios_creados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usuarios_actualizados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usuarios_desvinculados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tareas_reasignadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Detalle del error (si hubo)
    error_mensaje: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Tiempo de ejecución (en ms)
    duracion_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Auditoría
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<LogSyncAd {self.tipo} {self.resultado} {self.started_at}>"
