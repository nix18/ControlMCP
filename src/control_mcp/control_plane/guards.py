"""Sensitive-action guards and confirmation handling."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from control_mcp.domain.models import ConfirmationTicket, new_id

_PENDING_CONFIRMATIONS: dict[str, ConfirmationTicket] = {}
_CONFIRMATION_TOKENS: dict[str, ConfirmationTicket] = {}

_KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "payment": (
        "pay",
        "payment",
        "transfer",
        "wallet",
        "bank",
        "checkout",
        "付款",
        "支付",
        "转账",
        "钱包",
        "银行卡",
    ),
    "password": (
        "password",
        "passcode",
        "pin",
        "otp",
        "verification code",
        "密码",
        "口令",
        "验证码",
        "支付密码",
    ),
    "asset": ("asset", "fund", "withdraw", "deposit", "证券", "资产", "提现", "充值"),
    "destructive": ("delete", "remove", "destroy", "wipe", "drop", "删除", "清空", "销毁"),
}


@dataclass
class RiskAssessment:
    risk_level: str = "low"
    requires_confirmation: bool = False
    reason: str = ""
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _flatten_text(tool_name: str, args: dict[str, Any]) -> str:
    values: list[str] = [tool_name]
    for key, value in args.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            values.append(f"{key}={value}")
        else:
            values.append(f"{key}={json.dumps(value, ensure_ascii=False, default=str)}")
    return " ".join(values).lower()


def assess_tool_risk(tool_name: str, args: dict[str, Any]) -> RiskAssessment:
    """Assess whether a tool call should require explicit confirmation."""
    haystack = _flatten_text(tool_name, args)
    matched: list[str] = []
    reason = ""
    risk_level = "low"

    if tool_name in {"launch_url", "launch_app"}:
        risk_level = "medium"

    if tool_name in {"mouse_and_keyboard", "key_sequence"}:
        risk_level = "medium"

    for label, keywords in _KEYWORD_GROUPS.items():
        for keyword in keywords:
            if keyword in haystack:
                matched.append(keyword)
                if label in {"payment", "password", "asset"}:
                    risk_level = "high"
                    reason = "Detected payment/password/asset-related action."
                elif label == "destructive" and risk_level != "high":
                    risk_level = "medium"
                    reason = "Detected potentially destructive action."

    requires_confirmation = risk_level == "high" or (
        risk_level == "medium" and bool(args.get("risk_context"))
    )
    return RiskAssessment(
        risk_level=risk_level,
        requires_confirmation=requires_confirmation,
        reason=reason,
        matched_keywords=matched,
    )


def create_confirmation(
    *,
    summary: str,
    scope: str,
    reason: str,
    risk_level: str,
    plan_id: str | None = None,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ConfirmationTicket:
    ticket = ConfirmationTicket(
        confirmation_id=new_id("confirm"),
        risk_level=risk_level,
        reason=reason,
        summary=summary,
        scope=scope,
        plan_id=plan_id,
        run_id=run_id,
        metadata=metadata or {},
    )
    _PENDING_CONFIRMATIONS[ticket.confirmation_id] = ticket
    return ticket


def approve_confirmation(
    confirmation_id: str, approve: bool, note: str | None = None
) -> dict[str, Any]:
    ticket = _PENDING_CONFIRMATIONS.get(confirmation_id)
    if ticket is None:
        return {
            "success": False,
            "message": f"Unknown confirmation id: {confirmation_id}",
        }

    if not approve:
        ticket.status = "rejected"
        return {
            "success": True,
            "approved": False,
            "confirmation_id": confirmation_id,
            "message": "Sensitive action was rejected.",
        }

    token = new_id("token")
    ticket.status = "approved"
    ticket.confirmation_token = token
    if note:
        ticket.metadata["note"] = note
    _CONFIRMATION_TOKENS[token] = ticket
    return {
        "success": True,
        "approved": True,
        "confirmation_id": confirmation_id,
        "confirmation_token": token,
        "expires_at": (datetime.now() + timedelta(seconds=ticket.expires_in_seconds)).isoformat(),
        "message": "Sensitive action approved.",
    }


def validate_confirmation_token(token: str | None) -> ConfirmationTicket | None:
    if not token:
        return None
    ticket = _CONFIRMATION_TOKENS.get(token)
    if ticket is None:
        return None
    expires_at = datetime.fromisoformat(ticket.created_at) + timedelta(
        seconds=ticket.expires_in_seconds
    )
    if datetime.now() > expires_at:
        return None
    return ticket


def maybe_require_confirmation(
    tool_name: str,
    args: dict[str, Any],
    *,
    summary: str,
    scope: str,
    plan_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any] | None:
    assessment = assess_tool_risk(tool_name, args)
    if not assessment.requires_confirmation:
        return None

    ticket = create_confirmation(
        summary=summary,
        scope=scope,
        reason=assessment.reason or "Sensitive operation requires explicit confirmation.",
        risk_level=assessment.risk_level,
        plan_id=plan_id,
        run_id=run_id,
        metadata={
            "tool_name": tool_name,
            "args": args,
            "matched_keywords": assessment.matched_keywords,
        },
    )
    return {
        "success": False,
        "status": "confirmation_required",
        "confirmation": ticket.to_dict(),
    }
