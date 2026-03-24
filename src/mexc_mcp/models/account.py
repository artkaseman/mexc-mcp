"""Pydantic models for MEXC account API responses.

Covers:
- Balance      — asset free/locked amounts from the account endpoint
- AccountInfo  — full account snapshot including all balances and permissions
- Order        — open/historical order with fill details
- TradeRecord  — executed trade with fee breakdown
"""

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel


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


# ---------------------------------------------------------------------------
# Balance / AccountInfo
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


class Order(BaseModel):
    """A single open or historical order from GET /api/v3/openOrders.

    All price and quantity fields are Decimal. orderId is a string because
    MEXC uses a custom format (e.g. 'C02__474250929059741696').
    """

    model_config = _CAMEL_CONFIG

    symbol: str
    order_id: str
    client_order_id: str | None = None
    price: DecimalStr
    orig_qty: DecimalStr
    executed_qty: DecimalStr
    cummulative_quote_qty: DecimalStr  # MEXC spells it with double-m
    status: str       # NEW | PARTIALLY_FILLED | FILLED | CANCELED | REJECTED | EXPIRED
    time_in_force: str
    type: str         # LIMIT | MARKET | LIMIT_MAKER
    side: str         # BUY | SELL
    stop_price: DecimalStr
    time: int
    update_time: int
    is_working: bool
    orig_quote_order_qty: DecimalStr


# ---------------------------------------------------------------------------
# TradeRecord
# ---------------------------------------------------------------------------


class TradeRecord(BaseModel):
    """A single executed trade from GET /api/v3/myTrades.

    commission is the fee paid; commissionAsset is the asset it was taken in.
    is_buyer / is_maker determine the side and liquidity role.
    """

    model_config = _CAMEL_CONFIG

    symbol: str
    id: str
    order_id: str
    price: DecimalStr
    qty: DecimalStr
    quote_qty: DecimalStr
    commission: DecimalStr
    commission_asset: str
    time: int
    is_buyer: bool
    is_maker: bool
