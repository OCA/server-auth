# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from extendable_pydantic import StrictExtendableBaseModel


class CrossConnectGroup(StrictExtendableBaseModel):
    id: int
    name: str
    comment: str | None = None

    @classmethod
    def from_group(cls, group):
        return cls.model_construct(
            id=group.id,
            name=group.full_name,
            comment=group.comment or None,
        )


class SyncResponse(StrictExtendableBaseModel):
    groups: list[CrossConnectGroup]

    @classmethod
    def from_groups(cls, groups):
        return cls.model_construct(
            groups=[CrossConnectGroup.from_group(group) for group in groups]
        )


class AccessRequest(StrictExtendableBaseModel, extra="ignore"):
    id: int
    name: str
    login: str
    email: str
    lang: str
    groups: list[int]
    redirect_url: str = None


class AccessResponse(StrictExtendableBaseModel):
    client_id: int
    token: str

    @classmethod
    def from_params(cls, token, client_id):
        return cls.model_construct(token=token, client_id=client_id)
