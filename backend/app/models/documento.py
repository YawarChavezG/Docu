"""
Modelo: Documento
Tabla CORE del Sistema de Gestion Documental.

Almacena el documento "maestro" independiente del flujo. Un documento
puede tener N versiones (cada version = un DocumentoFlujo independiente).

Nomenclatura del codigo (ADR-011 ratificado en sesion 21):
    {sigla_area}-{codigo_tipo}-{correlativo_3_digitos} v{version_2_digitos}

Ejemplo: CC-3-005/01
    CC   = sigla del AREA (areas.sigla)
    3    = codigo del TIPO DE DOCUMENTO (tipos_documento.codigo)
    005  = correlativo monotono dentro de (area, tipo)
    01   = version (se guarda aparte, se concatena con /)

Reglas de negocio:
- "Un documento vencido SI O SI debe estar aprobado u obsoleto."
  Esto se enforce con CheckConstraint en BD + validacion Pydantic.
- Borrado logico (activo=True/False), nunca DELETE fisico.
- correlativo es monotono creciente dentro de (area_id, tipo_documento_id)
  via correlativo_service.py con SELECT FOR UPDATE.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    String, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum, func,
    Text, Index, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.gerencia import Gerencia
    from app.models.area import Area
    from app.models.tipo_documento import TipoDocumento
    from app.models.usuario import Usuario
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.archivo_adjunto import ArchivoAdjunto


# ─── Enums del modelo ───

class VigenciaDocumento(str, enum.Enum):
    """Estado de vigencia calculado a partir de aprobacion_at + tipo_documento.periodo_vigencia."""
    VIGENTE = "VIGENTE"
    POR_VENCER = "POR_VENCER"
    VENCIDO = "VENCIDO"
    OBSOLETO = "OBSOLETO"


class EstatusDocumento(str, enum.Enum):
    """Estado del documento dentro del workflow documental."""
    EN_ELABORACION = "EN_ELABORACION"
    LIBERACION_ETO = "LIBERACION_ETO"   # R3 item 0.6: nuevo estado entre EN_ELABORACION y EN_REVISION
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    OBSOLETO = "OBSOLETO"


class Documento(Base):
    """
    Tabla CORE del SGD. Almacena cada version de un documento.
    Un mismo codigo (sin version) puede tener multiples filas, una por version.
    """
    __tablename__ = "documentos"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones organizacionales ───
    gerencia_id: Mapped[int] = mapped_column(
        ForeignKey("gerencias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[int] = mapped_column(
        ForeignKey("areas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # proceso: por ahora sin tabla, queda como int nullable
    proceso_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    tipo_documento_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_documento.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ─── Codigo y version ───
    # Correlativo monotono dentro de (area_id, tipo_documento_id).
    # Lo calcula correlativo_service.py con SELECT FOR UPDATE.
    correlativo: Mapped[int] = mapped_column(Integer, nullable=False)

    # Codigo del documento SIN la version. Formato: CC-3-005
    # (sigla_area + codigo_tipo + correlativo_3_digitos con zero-pad).
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Version de 2 digitos: "00" para creacion, "01"+"NN" para actualizaciones.
    version: Mapped[str] = mapped_column(String(2), nullable=False, default="00")

    # ─── Contenido ───
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)

    # ─── Fechas de ciclo de vida ───
    # aprobacion_at: null hasta que se aprueba. Cuando se aprueba, se calcula
    # expira_at = aprobacion_at + tipo_documento.periodo_vigencia (si indefinido=False).
    aprobacion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )
    expira_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )

    # ─── Estado y vigencia (calculados en backend, no trigger SQL en R2) ───
    vigencia: Mapped[VigenciaDocumento] = mapped_column(
        SAEnum(VigenciaDocumento, name="vigencia_documento",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=VigenciaDocumento.VIGENTE,
        index=True,
    )
    estatus: Mapped[EstatusDocumento] = mapped_column(
        SAEnum(EstatusDocumento, name="estatus_documento",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=EstatusDocumento.EN_ELABORACION,
        index=True,
    )

    # ─── Legacy y comentarios ───
    # codigo_antiguo: codigo del sistema legacy anterior (sigue usandose).
    codigo_antiguo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    # comentarios_eto: max 50 chars enforced por CheckConstraint + Pydantic.
    comentarios_eto: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ─── Auditoria ───
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
    )

    # ─── Relaciones ───
    gerencia: Mapped["Gerencia"] = relationship("Gerencia")
    area: Mapped["Area"] = relationship("Area")
    tipo_documento: Mapped["TipoDocumento"] = relationship("TipoDocumento")
    created_by: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[created_by_id],
    )
    updated_by: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[updated_by_id],
    )

    flujos: Mapped[List["DocumentoFlujo"]] = relationship(
        "DocumentoFlujo", back_populates="documento", cascade="all, delete-orphan",
        foreign_keys="DocumentoFlujo.documento_id",
    )
    archivos: Mapped[List["ArchivoAdjunto"]] = relationship(
        "ArchivoAdjunto", back_populates="documento", cascade="all, delete-orphan",
    )

    # ─── Constraints ───
    # Unico: el correlativo es monotono dentro de (area, tipo, version).
    # Incluye version para permitir ACTUALIZACION (mismo correlativo, version+1).
    __table_args__ = (
        UniqueConstraint(
            "area_id", "tipo_documento_id", "correlativo", "version",
            name="uq_documento_area_tipo_correlativo_version",
        ),
        # Codigo completo (incluye version) tambien es unico.
        # Esto evita que 2 documentos con misma (area, tipo, correlativo, version) coexistan.
        UniqueConstraint(
            "codigo", "version",
            name="uq_documento_codigo_version",
        ),
        # Regla de negocio: un documento VENCIDO SI O SI debe estar APROBADO u OBSOLETO.
        CheckConstraint(
            "(vigencia <> 'VENCIDO') OR (estatus IN ('APROBADO', 'OBSOLETO'))",
            name="ck_documento_vencido_aprobado",
        ),
        # Indices compuestos para queries tipicas.
        Index("ix_documento_vigencia_expira", "vigencia", "expira_at"),
        Index("ix_documento_estatus_activo", "estatus", "activo"),
        Index("ix_documento_area_tipo", "area_id", "tipo_documento_id"),
    )

    def __repr__(self) -> str:
        return f"<Documento {self.codigo}/{self.version} ({self.estatus.value})>"

    @property
    def codigo_completo(self) -> str:
        """Codigo con version concatenada (formato que ve el usuario)."""
        return f"{self.codigo}/{self.version}"
