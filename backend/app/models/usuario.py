"""
Modelo: Usuario
Sincronizado desde Active Directory (LDAP). En DES se usa un stub.
Tiene 5 roles (N:M) y 10 módulos (N:M).

ID de AD: `azure_oid` (objectGUID de AD, único e inmutable).
Username de AD: `username` (sAMAccountName, único).
"""
import enum
from datetime import datetime, date
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    String, DateTime, Date, Boolean, ForeignKey, Integer,
    Enum as SAEnum, Table, Column, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.rol import Rol
    from app.models.area import Area
    from app.models.delegacion import Delegacion
    from app.models.ausencia import Ausencia
    from app.models.firma_digital import FirmaDigital
    from app.models.log_sync_ad import LogSyncAd


class EstadoUsuario(str, enum.Enum):
    """Estados posibles de un usuario en SGD."""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    DESVINCULADO = "desvinculado"
    AUSENTE = "ausente"  # Solo lectura, no se puede actuar


class EstadoDelegacion(str, enum.Enum):
    """Estado de la delegación (alerta de UI)."""
    PENDIENTE = "pendiente"   # Usuario activo sin delegado
    ASIGNADO = "asignado"     # Tiene delegado configurado
    NA = "na"                 # No requiere delegado (visualizadores)


# ─── Tablas de asociación N:M ───
usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Identidad de AD ───
    # sAMAccountName de AD (ej: "aromero", "mbustamante")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # objectGUID de AD (único e inmutable). Null en usuarios creados manualmente.
    azure_oid: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)

    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    iniciales: Mapped[str] = mapped_column(String(5), nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)

    # ─── Organización ───
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── Estado ───
    estado: Mapped[str] = mapped_column(
        SAEnum(EstadoUsuario, name="estado_usuario", values_callable=lambda x: [e.value for e in x]),
        default=EstadoUsuario.ACTIVO,
        nullable=False,
        index=True,
    )

    # Si está ausente (programado en Mi Perfil). Es un flag de lectura, se setea
    # automáticamente al activar/desactivar una `Ausencia` activa.
    ausente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # ─── Delegado (FK a sí mismo) ───
    # Solo si el rol lo requiere (ETO / elaborador-revisor / aprobador)
    delegado_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Estado del delegado (alerta de UI: "DEBE CONFIGURAR DELEGADO")
    estado_delegacion: Mapped[str] = mapped_column(
        SAEnum(EstadoDelegacion, name="estado_delegacion",
               values_callable=lambda x: [e.value for e in x]),
        default=EstadoDelegacion.NA,
        nullable=False,
    )

    # ─── Configuración personal ───
    # Si puede exportar reportes a Excel
    visualiza_reportes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requiere_delegado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Datos originales de AD (para auditoría y re-sync) ───
    # Campo "info" de AD. Texto libre. Se llena en cada sync.
    ad_info: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Campo "postalCode" de AD. Sirve como flag de warning si está vacío.
    ad_postal_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Fecha del último sync que actualizó este usuario desde AD
    ad_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Sesion 23 / Bloque C2: true si el usuario fue importado/creado desde el AD.
    # False si fue creado manualmente o sembrado como stub de DES.
    es_usuario_ad: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # ─── Auditoría ───
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ─── Relaciones ───
    area: Mapped["Area | None"] = relationship("Area", back_populates="usuarios", foreign_keys=[area_id])
    delegado: Mapped["Usuario | None"] = relationship("Usuario", remote_side="Usuario.id", foreign_keys=[delegado_id])

    roles: Mapped[List["Rol"]] = relationship(
        "Rol", secondary=usuario_roles, backref="usuarios"
    )
    # Sesion 26: la relacion modulos se elimino. El control de acceso es por
    # ROL via ACL hardcodeado en el frontend (auth.js:canAccess). El campo
    # user.modulos del backend era codigo muerto.
    delegaciones_como_principal: Mapped[List["Delegacion"]] = relationship(
        "Delegacion", foreign_keys="Delegacion.usuario_principal_id", back_populates="usuario_principal"
    )
    delegaciones_como_suplente: Mapped[List["Delegacion"]] = relationship(
        "Delegacion", foreign_keys="Delegacion.delegado_id", back_populates="delegado"
    )
    ausencias: Mapped[List["Ausencia"]] = relationship(
        "Ausencia", back_populates="usuario", cascade="all, delete-orphan"
    )
    firmas_digitales: Mapped[List["FirmaDigital"]] = relationship(
        "FirmaDigital", back_populates="usuario"
    )

    __table_args__ = (
        UniqueConstraint("username", "estado", name="uq_username_estado"),
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.username} ({self.estado})>"

    @property
    def rol_principal(self) -> "Rol | None":
        """Retorna el primer rol (en COFAR suele ser 1)."""
        return self.roles[0] if self.roles else None
