"""Instruction preprocessing and desktop task plan generation."""

from __future__ import annotations

import re
from typing import Any

from control_mcp.control_plane.guards import assess_tool_risk
from control_mcp.domain.models import DesktopTaskPlan, PlanStep, new_id

_PLANS: dict[str, DesktopTaskPlan] = {}


def _normalize_instruction(instruction: str) -> str:
    normalized = re.sub(r"\s+", " ", instruction).strip()
    return normalized


def _extract_target_window(instruction: str) -> str | None:
    patterns = [
        r"(?:打开|切换到|聚焦|focus|open)\s*([A-Za-z0-9._\-\u4e00-\u9fff ]{2,30})",
        r"(?:在|into)\s+([A-Za-z0-9._\-\u4e00-\u9fff ]{2,30})\s*(?:里|中|window)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, instruction, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _intent_and_confidence(instruction: str) -> tuple[str, float]:
    lower = instruction.lower()
    if any(keyword in lower for keyword in ["截图", "capture", "screenshot", "截屏"]):
        return "capture_information", 0.9
    if any(keyword in lower for keyword in ["滚动", "scroll", "聊天记录", "长截图"]):
        return "capture_scroll_content", 0.88
    if any(
        keyword in lower
        for keyword in ["运行", "build", "run", "启动配置", "jetbrains", "pycharm", "idea"]
    ):
        return "run_application_flow", 0.85
    if any(keyword in lower for keyword in ["输入", "type", "粘贴", "填写"]):
        return "input_text", 0.78
    if any(keyword in lower for keyword in ["支付", "付款", "转账", "密码", "验证码", "wallet"]):
        return "sensitive_transaction", 0.92
    if any(keyword in lower for keyword in ["点击", "click", "按钮"]):
        return "click_ui", 0.7
    return "navigate_and_observe", 0.45


def _needs_observation(intent: str, target_window: str | None) -> bool:
    return (
        intent in {"navigate_and_observe", "click_ui", "capture_information"}
        or target_window is None
    )


def _build_steps(normalized: str, intent: str, target_window: str | None) -> list[PlanStep]:
    steps: list[PlanStep] = []

    if target_window:
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="navigation",
                action="focus_window",
                args={"title": target_window},
                goal="Bring the target window to the foreground.",
                verification=["window focused"],
                fallback=["alt+tab fallback"],
            )
        )

    if intent in {"navigate_and_observe", "capture_information", "click_ui"}:
        capture_action = "capture_window" if target_window else "capture_screen"
        capture_args: dict[str, Any] = {"quality": 75, "max_width": 960}
        if target_window:
            capture_args["title"] = target_window
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="observation",
                action=capture_action,
                args=capture_args,
                goal="Observe the current UI before acting.",
                verification=["visual context acquired"],
                fallback=["capture_screen fallback"],
            )
        )

    if intent == "capture_scroll_content":
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="observation",
                action="capture_screen" if not target_window else "capture_window",
                args={
                    "quality": 75,
                    "max_width": 960,
                    **({"title": target_window} if target_window else {}),
                },
                goal="Acquire the current window before choosing a scroll region.",
                verification=["window or screen snapshot available"],
                fallback=["manual region selection"],
            )
        )

    if intent == "run_application_flow":
        keys = ["shift", "f10"]
        if "重启" in normalized or "restart" in normalized.lower():
            keys = ["ctrl", "f5"]
        steps.extend(
            [
                PlanStep(
                    id=new_id("step"),
                    kind="action",
                    action="key_press",
                    args={"keys": ["win", "up"]},
                    goal="Maximize the target window before running.",
                    verification=["window ready"],
                    fallback=["capture_window check"],
                ),
                PlanStep(
                    id=new_id("step"),
                    kind="action",
                    action="key_press",
                    args={"keys": keys},
                    goal="Run or restart the current IDE configuration.",
                    verification=["run triggered"],
                    fallback=["configuration chooser"],
                ),
                PlanStep(
                    id=new_id("step"),
                    kind="verification",
                    action="wait_until_stable",
                    args={
                        "scope": "window",
                        "title": target_window,
                        "rounds": 2,
                        "interval_seconds": 1.5,
                    },
                    goal="Wait until the visible run output stabilizes.",
                    verification=["stable window content"],
                    fallback=["capture_window and retry"],
                ),
            ]
        )

    if intent == "input_text":
        sensitive = assess_tool_risk(
            "key_type", {"text": normalized, "risk_context": normalized}
        ).requires_confirmation
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="action",
                action="key_type",
                args={"text": normalized},
                goal="Type or paste the requested content.",
                verification=["input changed"],
                fallback=["clipboard paste"],
                risk_level="high" if sensitive else "medium",
                sensitive=sensitive,
            )
        )

    if intent == "sensitive_transaction":
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="guard",
                action="request_confirmation",
                args={"risk_context": normalized},
                goal="Require explicit approval before continuing.",
                verification=["user confirmed"],
                fallback=["abort task"],
                risk_level="high",
                sensitive=True,
            )
        )

    if not steps:
        steps.append(
            PlanStep(
                id=new_id("step"),
                kind="observation",
                action="capture_screen",
                args={"quality": 75, "max_width": 960},
                goal="Start from a visual observation because the instruction is ambiguous.",
                verification=["screen snapshot available"],
                fallback=["list_windows"],
            )
        )

    return steps


def plan_desktop_task(instruction: str, current_context: str | None = None) -> DesktopTaskPlan:
    normalized = _normalize_instruction(instruction)
    intent, confidence = _intent_and_confidence(normalized)
    target_window = _extract_target_window(normalized)
    steps = _build_steps(normalized, intent, target_window)

    risk = assess_tool_risk(
        "plan_desktop_task", {"instruction": normalized, "risk_context": normalized}
    )
    if any(step.sensitive for step in steps):
        risk.requires_confirmation = True
        risk.risk_level = "high"
        risk.reason = risk.reason or "Sensitive steps exist in the generated plan."

    status = "needs_observation" if _needs_observation(intent, target_window) else "ready"
    summary = f"Intent={intent}; target_window={target_window or 'unknown'}; steps={len(steps)}"
    if current_context:
        summary += "; context=provided"

    plan = DesktopTaskPlan(
        plan_id=new_id("plan"),
        instruction=instruction,
        normalized_instruction=normalized,
        intent=intent,
        confidence=confidence,
        summary=summary,
        needs_confirmation=risk.requires_confirmation,
        needs_observation=_needs_observation(intent, target_window),
        status=status,
        target_window=target_window,
        risk_reasons=[risk.reason] if risk.reason else [],
        steps=steps,
    )
    _PLANS[plan.plan_id] = plan
    return plan


def get_plan(plan_id: str) -> DesktopTaskPlan | None:
    return _PLANS.get(plan_id)


def remember_plan(plan: DesktopTaskPlan) -> DesktopTaskPlan:
    _PLANS[plan.plan_id] = plan
    return plan
