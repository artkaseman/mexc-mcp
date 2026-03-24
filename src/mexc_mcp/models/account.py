"""Pydantic models for MEXC account API responses.

Covers:
- Balance      — asset free/locked amounts from the account endpoint
- AccountInfo  — full account snapshot including all balances and permissions
- Order        — full order object (id, symbol, side, type, status, fills)
- TradeHistory — executed trade records with fee details
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Annotated


def _parse_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except Exception as exc:
        raise ValueError(f"invalid decimal value: {v!r}") from exc


DecimalStr = Annotated[Decimal, BeforeValidator(_parse_decimal)]

_CAMEL_CONFIG = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
    extra="ignore",
)


class Balance(BaseModel):
    """Spot wallet balance for a single asset.

    free:   quantity available to trade or withdraw.
    locked: quantity held in open orders or pending withdrawals.
    """

    asset: str
    free: DecimalStr
    locked: DecimalStr


class AccountInfo(BaseModel):
    """Spot account snapshot from GET /api/v3/account.

    balances includes all assets; use the tool layer to filter zero balances.
    """

    model_config = _CAMEL_CONFIG

    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    balances: list[Balance]
    permissions: list[str]
