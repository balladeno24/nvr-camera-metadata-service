import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class CameraKind(str, enum.Enum):
    ELECTRO_OPTICAL = "electro-optical"
    THERMAL = "thermal"
    INFRARED = "infrared"


class NVR(Base):
    __tablename__ = "nvrs"

    serial_number: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    maximum_input_channels: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    cameras: Mapped[list["Camera"]] = relationship(
        back_populates="nvr",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Camera(Base):
    __tablename__ = "cameras"

    serial_number: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    kind: Mapped[CameraKind] = mapped_column(
    Enum(
        CameraKind,
        native_enum=False,
        values_callable=lambda enum_class: [
            member.value for member in enum_class
        ],
    ),
    nullable=False,
)
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    nvr_uuid: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("nvrs.serial_number", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nvr: Mapped[NVR] = relationship(back_populates="cameras")