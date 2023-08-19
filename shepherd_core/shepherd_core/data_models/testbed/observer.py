from datetime import datetime
from typing import Optional

from pydantic import Field
from pydantic import IPvAnyAddress
from pydantic import StringConstraints
from pydantic import model_validator
from typing_extensions import Annotated

from ...testbed_client import tb_client
from ..base.content import IdInt
from ..base.content import NameStr
from ..base.content import SafeStr
from ..base.shepherd import ShpModel
from .cape import Cape
from .cape import TargetPort
from .target import Target

MACStr = Annotated[
    str,
    StringConstraints(
        max_length=17, pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    ),
]


class Observer(ShpModel, title="Shepherd-Sheep"):
    """meta-data representation of a testbed-component (physical object)"""

    id: IdInt  # noqa: A003
    name: NameStr
    description: SafeStr
    comment: Optional[SafeStr] = None

    ip: IPvAnyAddress
    mac: MACStr

    room: NameStr
    eth_port: NameStr

    latitude: Annotated[float, Field(ge=-90, le=90)] = 51.026573
    longitude: Annotated[float, Field(ge=-180, le=180)] = 13.723291
    # ⤷ cfaed-floor

    cape: Optional[Cape] = None
    target_a: Optional[Target] = None
    target_b: Optional[Target] = None

    created: datetime = Field(default_factory=datetime.now)
    alive_last: Optional[datetime] = None

    def __str__(self):
        return self.name

    @model_validator(mode="before")
    @classmethod
    def query_database(cls, values: dict) -> dict:
        values, _ = tb_client.try_completing_model(cls.__name__, values)
        return values

    @model_validator(mode="after")
    def post_validation(self):
        has_cape = self.cape is not None
        has_target = (self.target_a is not None) or (
            self.target_b is not None
        )
        if not has_cape and has_target:
            raise ValueError(
                f"Observer '{self.name}' is faulty "
                f"-> has targets but no cape"
            )
        return self

    def get_target_port(self, target_id: int) -> TargetPort:
        if self.target_a is not None and target_id == self.target_a.id:
            return TargetPort.A
        if self.target_b is not None and target_id == self.target_b.id:
            return TargetPort.B
        raise ValueError(
            f"Target-ID {target_id} was not found in Observer '{self.name}'"
        )

    def get_target(self, target_id: int) -> Target:
        if self.target_a is not None and target_id == self.target_a.id:
            return self.target_a
        if self.target_b is not None and target_id == self.target_b.id:
            return self.target_b
        raise ValueError(
            f"Target-ID {target_id} was not found in Observer '{self.name}'"
        )
