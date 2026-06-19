"""
Modelo: SemaforizacionTarea
Configuracion del semaforo (verde/amarillo/rojo) por TIPO de tarea (sesion 13).

Razones (sesion 13, 2026-06-16):
  - Antes existia `configuracion_global.categoria=SEMAFORO` con claves
    genericas `semaforo_verde_dias` y `semaforo_amarillo_dias`. Eso
    aplicaba la misma regla a TODAS las tareas.
  - El cliente quiere reglas DIFERENTES por tipo de tarea:
      * REVISION         7/7/7  (verde 0-7, amarillo 8-12, rojo 13-15)
      * APROBACION       7/7/7
      * CONTROL_LECTURA  7/7/7
      * EVALUACIONES     5/5/5  (verde 0-5, amarillo 6-11, rojo 12-15)
  - El plazo maximo es 15 dias naturales en todos los casos.
  - "Se pondra en ROJO cuando falte 3 dias para que el plazo de 15 dias
    se cumpla" (osea dias 13-15).
  - Por lo tanto la tabla guarda `dias_verde`, `dias_amarillo`, `dias_rojo`
    como el ULTIMO dia de cada color (inclusive). Asi:
      * REVISION:         dias_verde=7, dias_amarillo=12, dias_rojo=15
      * EVALUACIONES:     dias_verde=5, dias_amarillo=11, dias_rojo=15

El estado (color) de una tarea dada se calcula en runtime con:
    dias_transcurridos = (hoy - fecha_asignacion).days
    if   dias_transcurridos <= cfg.dias_verde:   'VERDE'
    elif dias_transcurridos <= cfg.dias_amarillo: 'AMARILLO'
    else: 'ROJO'
"""
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoTarea(str, enum.Enum):
    """Tipos de tarea del SGD. Catalogo cerrado (6 entradas en R3 Fase 1).

    R3 Fase 1 agrega LIBERACION (US-1.05, ETO libera) y CORRECCION
    (US-3.04, elaborador corrige). Los 4 originales siguen vigentes.
    """
    REVISION = "REVISION"
    APROBACION = "APROBACION"
    CONTROL_LECTURA = "CONTROL_LECTURA"
    EVALUACION = "EVALUACION"
    LIBERACION = "LIBERACION"      # R3 Fase 1: ETO libera (US-1.05, US-4.06)
    CORRECCION = "CORRECCION"      # R3 Fase 1: elaborador corrige (US-3.04, US-3.05)


class SemaforizacionTarea(Base):
    __tablename__ = "semaforizacion_tarea"

    # PK logica = tipo_tarea (catalogo cerrado de 4)
    tipo_tarea: Mapped[TipoTarea] = mapped_column(
        SAEnum(TipoTarea, name="tipo_tarea_semaforo",
               values_callable=lambda x: [e.value for e in x]),
        primary_key=True,
    )

    # Ultimo dia (inclusive) en que la tarea se considera VERDE.
    # Si dias_transcurridos <= dias_verde => VERDE.
    dias_verde: Mapped[int] = mapped_column(Integer, nullable=False)

    # Ultimo dia (inclusive) en que la tarea se considera AMARILLO.
    # Si dias_verde < dias_transcurridos <= dias_amarillo => AMARILLO.
    dias_amarillo: Mapped[int] = mapped_column(Integer, nullable=False)

    # Ultimo dia (inclusive) en que la tarea se considera ROJO.
    # Si dias_transcurridos > dias_amarillo y <= dias_rojo => ROJO.
    # En la practica dias_rojo = plazo_maximo (15 dias).
    dias_rojo: Mapped[int] = mapped_column(Integer, nullable=False)

    # Plazo maximo de la tarea en dias naturales (normalmente 15).
    plazo_maximo_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=15)

    # R3 Fase 1: US-3.01 exige calculo en dias HABILES (no naturales).
    # True = el plazo_maximo_dias y los dias_verde/amarillo/rojo se
    # cuentan excluyendo fines de semana + feriados (tabla `feriados`).
    # False = legado R1/R2 (dias naturales). Default TRUE.
    usa_dias_habiles: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SemaforizacionTarea {self.tipo_tarea.value} v={self.dias_verde} a={self.dias_amarillo} r={self.dias_rojo}>"
