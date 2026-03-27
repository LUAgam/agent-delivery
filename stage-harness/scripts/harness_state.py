#!/usr/bin/env python3
"""State manager for the stage-harness plugin.

This script backs the minimal Iter-0 / Iter-1 workflow:
- initialize a feature workspace
- report current stage and expected artifacts
- validate stage artifacts
- advance or roll back the stage machine
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "templates"
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
HARNESS_ROOT = PROJECT_ROOT / ".harness"
FEATURES_ROOT = HARNESS_ROOT / "features"
ACTIVE_FEATURE_FILE = HARNESS_ROOT / "active-feature.txt"
VALID_FEATURE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

STAGE_SEQUENCE = ["CLARIFY", "SPEC", "PLAN", "EXECUTE", "VERIFY", "DONE"]
ALLOWED_STAGES = set(STAGE_SEQUENCE) | {"FIX"}
STAGE_NEXT = {
    "CLARIFY": "SPEC",
    "SPEC": "PLAN",
    "PLAN": "EXECUTE",
    "EXECUTE": "VERIFY",
    "VERIFY": "DONE",
    "FIX": "VERIFY",
}


@dataclass
class CheckResult:
    label: str
    passed: bool
    resolved_path: str | None
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "passed": self.passed,
            "resolvedPath": self.resolved_path,
            "detail": self.detail,
        }


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "feature"


def validate_feature_name(value: str) -> str:
    feature = value.strip()
    if not feature:
        raise ValueError("feature name cannot be empty")
    if not VALID_FEATURE_RE.fullmatch(feature):
        raise ValueError(
            "feature name must match ^[a-z0-9]+(?:-[a-z0-9]+)*$"
        )
    return feature


def ensure_harness_root_safe() -> None:
    if HARNESS_ROOT.exists() and HARNESS_ROOT.is_symlink():
        raise ValueError(f"refusing to use symlinked harness root: {HARNESS_ROOT}")

    if FEATURES_ROOT.exists() and FEATURES_ROOT.is_symlink():
        raise ValueError(f"refusing to use symlinked features root: {FEATURES_ROOT}")

    resolved_project = PROJECT_ROOT.resolve()
    harness_parent = HARNESS_ROOT.parent.resolve()
    try:
        harness_parent.relative_to(resolved_project)
    except ValueError as exc:
        raise ValueError(f"harness root escapes project root: {HARNESS_ROOT}") from exc


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_write_text(path: Path, content: str) -> None:
    ensure_harness_root_safe()
    resolved_parent = path.parent.resolve()
    harness_root = HARNESS_ROOT
    try:
        resolved_parent.relative_to(harness_root.resolve())
    except ValueError as exc:
        raise ValueError(f"refusing to write outside harness root: {path}") from exc

    if path.exists() and path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {path}")

    if path.parent.exists() and path.parent.is_symlink():
        raise ValueError(f"refusing to write inside symlinked directory: {path.parent}")

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=resolved_parent, prefix=".tmp-stage-harness-", text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def safe_mkdir(path: Path) -> None:
    ensure_harness_root_safe()
    if path.exists() and path.is_symlink():
        raise ValueError(f"refusing to create inside symlinked path: {path}")
    if path.parent.exists() and path.parent.is_symlink():
        raise ValueError(f"refusing to create inside symlinked directory: {path.parent}")

    resolved_parent = path.parent.resolve()
    try:
        resolved_parent.relative_to(HARNESS_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"refusing to create directory outside harness root: {path}") from exc

    path.mkdir(parents=True, exist_ok=True)
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(HARNESS_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"directory escaped harness root: {path}") from exc


def ensure_read_path_safe(path: Path) -> None:
    ensure_harness_root_safe()
    if path.exists() and path.is_symlink():
        raise ValueError(f"refusing to read through symlink: {path}")
    if path.parent.exists() and path.parent.is_symlink():
        raise ValueError(f"refusing to read inside symlinked directory: {path.parent}")
    resolved_parent = path.parent.resolve()
    try:
        resolved_parent.relative_to(HARNESS_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"refusing to read outside harness root: {path}") from exc

    if path.exists():
        resolved_path = path.resolve()
        try:
            resolved_path.relative_to(HARNESS_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"read path escaped harness root: {path}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    safe_write_text(path, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def template_json(name: str) -> dict[str, Any]:
    template_path = TEMPLATE_ROOT / name
    if template_path.exists():
        return load_json(template_path)
    raise FileNotFoundError(f"missing template: {template_path}")


def feature_root(feature: str) -> Path:
    return FEATURES_ROOT / validate_feature_name(feature)


def state_path(feature: str) -> Path:
    return feature_root(feature) / "state.json"


def ensure_global_files() -> None:
    ensure_harness_root_safe()
    HARNESS_ROOT.mkdir(parents=True, exist_ok=True)
    safe_mkdir(FEATURES_ROOT)
    global_config = HARNESS_ROOT / "global-config.json"
    if not global_config.exists():
        payload = template_json("global-config.json")
        write_json(global_config, payload)


def ensure_feature_layout(feature: str) -> dict[str, Path]:
    root = feature_root(feature)
    paths = {
        "root": root,
        "artifacts": root / "artifacts",
        "councils": root / "councils",
        "decision_bundles": root / "decision-bundles",
        "sessions": root / "sessions",
        "trace": root / "trace",
    }
    for path in paths.values():
        safe_mkdir(path)
    safe_mkdir(paths["artifacts"] / "sections")
    return paths


def resolve_feature(requested: str | None, allow_missing: bool = False) -> str | None:
    if requested:
        return validate_feature_name(slugify(requested))
    if ACTIVE_FEATURE_FILE.exists():
        ensure_read_path_safe(ACTIVE_FEATURE_FILE)
        raw_feature = ACTIVE_FEATURE_FILE.read_text(encoding="utf-8").strip()
        if not raw_feature:
            if allow_missing:
                return None
            raise ValueError("active feature pointer is empty; run /harness-start again")
        try:
            return validate_feature_name(raw_feature)
        except ValueError:
            if allow_missing:
                return None
            raise ValueError(
                "active feature pointer is invalid; run /harness-start again"
            ) from None
    if allow_missing:
        return None
    raise ValueError("no active feature; run /harness-start first")


def external_planning_dir(feature: str) -> Path:
    return PROJECT_ROOT / ".shipspec" / "planning" / feature


def load_state(feature: str) -> dict[str, Any]:
    path = state_path(feature)
    if not path.exists():
        raise FileNotFoundError(f"missing state file: {path}")
    ensure_read_path_safe(path)
    state = load_json(path)
    current_stage = str(state.get("currentStage", "")).upper()
    if current_stage not in ALLOWED_STAGES:
        raise ValueError(f"invalid currentStage: {current_stage or '<empty>'}")
    state["currentStage"] = current_stage
    return state


def save_state(feature: str, state: dict[str, Any]) -> None:
    state["updatedAt"] = now_iso()
    write_json(state_path(feature), state)


def candidate_paths(feature: str) -> dict[str, list[Path]]:
    root = feature_root(feature)
    artifacts = root / "artifacts"
    councils = root / "councils"
    bundles = root / "decision-bundles"
    planning = external_planning_dir(feature)
    return {
        "clarification_notes": [artifacts / "clarification-notes.md"],
        "clarify_bundle": [bundles / "clarify.json"],
        "prd": [artifacts / "PRD.md", planning / "PRD.md"],
        "sdd": [artifacts / "SDD.md", planning / "SDD.md"],
        "tasks_json": [artifacts / "TASKS.json", planning / "TASKS.json"],
        "tasks_md": [artifacts / "TASKS.md", planning / "TASKS.md"],
        "bridge_spec": [artifacts / "bridge-spec.md", planning / "bridge-spec.md"],
        "claude_plan": [artifacts / "claude-plan.md", planning / "claude-plan.md"],
        "claude_plan_tdd": [artifacts / "claude-plan-tdd.md", planning / "claude-plan-tdd.md"],
        "sections_index": [artifacts / "sections" / "index.md", planning / "sections" / "index.md"],
        "implementation_summary": [artifacts / "implementation-summary.md"],
        "review_report": [councils / "review-report.md"],
        "test_report": [councils / "test-report.md"],
        "verification_json": [councils / "verification.json"],
        "fix_log": [artifacts / "fix-log.md"],
        "release_notes": [artifacts / "release-notes.md"],
        "delivery_summary": [artifacts / "delivery-summary.md"],
        "learning_candidates": [artifacts / "learning-candidates.md"],
    }


def first_existing_nonempty(paths: list[Path]) -> Path | None:
    for path in paths:
        if not path.exists():
            continue
        if path.is_relative_to(HARNESS_ROOT):
            ensure_read_path_safe(path)
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def json_candidate_valid(paths: list[Path]) -> tuple[Path | None, str]:
    first_error: str | None = None
    for path in paths:
        if not path.exists():
            continue
        if path.is_relative_to(HARNESS_ROOT):
            try:
                ensure_read_path_safe(path)
            except ValueError as exc:
                if first_error is None:
                    first_error = str(exc)
                continue
        if not path.is_file() or path.stat().st_size == 0:
            continue
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            if first_error is None:
                first_error = f"{path} is not valid JSON: {exc.msg}"
            continue
        if isinstance(content, dict) and content:
            return path, "ok"
        if isinstance(content, list) and content:
            return path, "ok"
        if first_error is None:
            first_error = f"{path} is empty JSON"
    return None, first_error or "missing"


def check_text(label: str, paths: list[Path]) -> CheckResult:
    resolved = first_existing_nonempty(paths)
    if resolved:
        return CheckResult(label, True, str(resolved), "ok")
    return CheckResult(label, False, None, "missing or empty")


def check_json(label: str, paths: list[Path]) -> CheckResult:
    resolved, detail = json_candidate_valid(paths)
    if resolved:
        return CheckResult(label, True, str(resolved), detail)
    return CheckResult(label, False, None, detail)


def check_verify_verdict(label: str, paths: list[Path]) -> CheckResult:
    resolved, detail = json_candidate_valid(paths)
    if not resolved:
        return CheckResult(label, False, None, detail)

    payload = load_json(resolved)
    verdict = str(payload.get("verdict", "")).upper()
    if verdict == "PASS":
        return CheckResult(label, True, str(resolved), "verdict PASS")
    if verdict == "FAIL":
        return CheckResult(
            label,
            False,
            str(resolved),
            "verdict FAIL requires FIX before DONE",
        )
    return CheckResult(
        label,
        False,
        str(resolved),
        "verification.json must contain verdict PASS",
    )


def stage_checks(feature: str, stage: str) -> list[CheckResult]:
    paths = candidate_paths(feature)
    if stage == "CLARIFY":
        return [check_text("clarification-notes", paths["clarification_notes"])]
    if stage == "SPEC":
        return [
            check_text("PRD.md", paths["prd"]),
            check_text("SDD.md", paths["sdd"]),
            check_json("TASKS.json", paths["tasks_json"]),
            check_text("TASKS.md", paths["tasks_md"]),
        ]
    if stage == "PLAN":
        return [
            check_text("bridge-spec.md", paths["bridge_spec"]),
            check_text("claude-plan.md", paths["claude_plan"]),
            check_text("claude-plan-tdd.md", paths["claude_plan_tdd"]),
            check_text("sections/index.md", paths["sections_index"]),
        ]
    if stage == "EXECUTE":
        return [check_text("implementation-summary.md", paths["implementation_summary"])]
    if stage == "VERIFY":
        return [
            check_text("review-report.md", paths["review_report"]),
            check_text("test-report.md", paths["test_report"]),
            check_verify_verdict("verification.json", paths["verification_json"]),
        ]
    if stage == "FIX":
        return [
            check_text("fix-log.md", paths["fix_log"]),
            check_json("verification.json", paths["verification_json"]),
        ]
    if stage == "DONE":
        return [
            check_text("release-notes.md", paths["release_notes"]),
            check_text("delivery-summary.md", paths["delivery_summary"]),
            check_text("learning-candidates.md", paths["learning_candidates"]),
        ]
    return []


def validation_summary(feature: str, state: dict[str, Any]) -> dict[str, Any]:
    stage = state["currentStage"]
    checks = stage_checks(feature, stage)
    valid = all(check.passed for check in checks)
    missing = [check.label for check in checks if not check.passed]
    return {
        "feature": feature,
        "stage": stage,
        "valid": valid,
        "checks": [check.as_dict() for check in checks],
        "missing": missing,
    }


def missing_status_payload(message: str) -> dict[str, Any]:
    return {
        "feature": None,
        "currentStage": None,
        "statePath": None,
        "activeFeatureFile": str(ACTIVE_FEATURE_FILE),
        "message": message,
    }


def collect_completed_artifacts(feature: str, stage: str) -> list[str]:
    return [
        check.resolved_path
        for check in stage_checks(feature, stage)
        if check.passed and check.resolved_path is not None
    ]


def render_status(feature: str | None, allow_missing: bool) -> dict[str, Any]:
    if feature is None:
        return missing_status_payload(
            "No active feature. Run /harness-start [feature-name]."
        )

    try:
        state = load_state(feature)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        if allow_missing:
            return missing_status_payload(
                f"Active feature '{feature}' is unavailable: {exc}"
            )
        raise

    validation = validation_summary(feature, state)
    return {
        "feature": feature,
        "currentStage": state["currentStage"],
        "statePath": str(state_path(feature)),
        "historyCount": len(state.get("stageHistory", [])),
        "pendingDecisions": state.get("pendingDecisions", []),
        "validateCurrentStage": validation,
        "paths": {
            "featureRoot": str(feature_root(feature)),
            "artifactsRoot": str(feature_root(feature) / "artifacts"),
            "councilsRoot": str(feature_root(feature) / "councils"),
            "externalPlanningRoot": str(external_planning_dir(feature)),
        },
        "message": (
            f"Active feature '{feature}' is in stage {state['currentStage']}."
            if feature
            else "No active feature."
        ),
        "allowMissing": allow_missing,
    }


def render_status_text(payload: dict[str, Any]) -> str:
    if payload.get("feature") is None:
        return payload.get("message", "No active feature.")

    validation = payload.get("validateCurrentStage", {})
    checks = validation.get("checks", [])
    lines = [
        "<stage-harness-status>",
        f"feature={payload['feature']}",
        f"current_stage={payload['currentStage']}",
        f"state_path={payload['statePath']}",
        f"history_count={payload.get('historyCount', 0)}",
        f"validation_ok={validation.get('valid', False)}",
    ]
    if checks:
        lines.append("required_artifacts:")
        for check in checks:
            marker = "ok" if check.get("passed") else "missing"
            lines.append(f"- [{marker}] {check.get('label')}")
    pending = payload.get("pendingDecisions") or []
    if pending:
        lines.append("pending_decisions:")
        for item in pending:
            lines.append(f"- {item}")
    lines.append("</stage-harness-status>")
    return "\n".join(lines)


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    ensure_global_files()
    feature = slugify(args.feature)
    ensure_feature_layout(feature)
    state_file = state_path(feature)

    created = not state_file.exists()
    if created:
        payload = deepcopy(template_json("state.json"))
        payload["feature"] = feature
        payload["riskLevel"] = args.risk_level
        payload["createdAt"] = now_iso()
        payload["updatedAt"] = payload["createdAt"]
        save_state(feature, payload)

    safe_write_text(ACTIVE_FEATURE_FILE, feature + "\n")
    validation = validation_summary(feature, load_state(feature))
    return {
        "created": created,
        "feature": feature,
        "currentStage": load_state(feature)["currentStage"],
        "statePath": str(state_file),
        "activeFeatureFile": str(ACTIVE_FEATURE_FILE),
        "validation": validation,
    }


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    feature = resolve_feature(args.feature, allow_missing=args.allow_missing)
    return render_status(feature, allow_missing=args.allow_missing)


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    try:
        feature = resolve_feature(args.feature, allow_missing=args.allow_missing)
    except ValueError as exc:
        if args.allow_missing:
            return {
                "feature": None,
                "stage": None,
                "valid": False,
                "checks": [],
                "missing": [],
                "message": f"Gate check failed: {exc}",
                "stateError": True,
            }
        raise
    if feature is None:
        return {
            "feature": None,
            "stage": None,
            "valid": True,
            "checks": [],
            "missing": [],
            "message": "No active feature; gate check skipped.",
        }
    try:
        state = load_state(feature)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        if args.allow_missing:
            return {
                "feature": None,
                "stage": None,
                "valid": False,
                "checks": [],
                "missing": [],
                "message": f"Gate check failed: {exc}",
                "stateError": True,
            }
        raise
    result = validation_summary(feature, state)
    result["message"] = (
        f"Stage {result['stage']} is ready to advance."
        if result["valid"]
        else f"Stage {result['stage']} is blocked by failed checks."
    )
    return result


def command_advance(args: argparse.Namespace) -> dict[str, Any]:
    feature = resolve_feature(args.feature)
    state = load_state(feature)
    current = state["currentStage"]
    if current == "DONE":
        raise ValueError("workflow is already at DONE")

    validation = validation_summary(feature, state)
    if not validation["valid"] and not args.force:
        raise ValueError(
            f"cannot advance {current}; missing artifacts: {', '.join(validation['missing'])}"
        )

    next_stage = STAGE_NEXT.get(current)
    if not next_stage:
        raise ValueError(f"stage {current} cannot advance")

    completed = {
        "stage": current,
        "completedAt": now_iso(),
        "artifacts": collect_completed_artifacts(feature, current),
    }
    state.setdefault("stageHistory", []).append(completed)
    state["currentStage"] = next_stage
    save_state(feature, state)
    safe_write_text(ACTIVE_FEATURE_FILE, feature + "\n")

    return {
        "feature": feature,
        "previousStage": current,
        "currentStage": next_stage,
        "statePath": str(state_path(feature)),
        "recordedHistoryEntry": completed,
    }


def command_rollback(args: argparse.Namespace) -> dict[str, Any]:
    feature = resolve_feature(args.feature)
    state = load_state(feature)
    current = state["currentStage"]
    history = state.get("stageHistory", [])

    if not history:
        raise ValueError("no completed stages available for rollback")

    target = args.to_stage.upper() if args.to_stage else history[-1]["stage"]
    completed_stages = {entry["stage"] for entry in history}
    if target not in STAGE_SEQUENCE and target != "FIX":
        raise ValueError(f"unsupported rollback target: {target}")
    if target != "FIX" and target not in completed_stages:
        raise ValueError(f"cannot roll back to uncompleted stage: {target}")

    current_index = STAGE_SEQUENCE.index(current)
    if target == "FIX":
        if current not in {"VERIFY", "DONE"}:
            raise ValueError("FIX rollback is only allowed from VERIFY or DONE")
    else:
        target_index = STAGE_SEQUENCE.index(target)
        if target_index >= current_index:
            raise ValueError("rollback target must be earlier than the current stage")

    state.setdefault("rollbackHistory", []).append(
        {
            "fromStage": current,
            "toStage": target,
            "reason": args.reason or "manual rollback",
            "timestamp": now_iso(),
        }
    )
    state["currentStage"] = target
    save_state(feature, state)
    safe_write_text(ACTIVE_FEATURE_FILE, feature + "\n")

    return {
        "feature": feature,
        "previousStage": current,
        "currentStage": target,
        "rollbackCount": len(state.get("rollbackHistory", [])),
    }


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage stage-harness state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a feature.")
    init_parser.add_argument("--feature", required=True, help="Feature name.")
    init_parser.add_argument(
        "--risk-level",
        default="medium",
        choices=["low", "medium", "high"],
        help="Initial risk level.",
    )

    status_parser = subparsers.add_parser("status", help="Show current status.")
    status_parser.add_argument("--feature", help="Feature name.")
    status_parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Return an empty status instead of failing when no feature is active.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate current stage artifacts.")
    validate_parser.add_argument("--feature", help="Feature name.")
    validate_parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Return a no-op validation result when no feature is active.",
    )

    advance_parser = subparsers.add_parser("advance", help="Advance to the next stage.")
    advance_parser.add_argument("--feature", help="Feature name.")
    advance_parser.add_argument(
        "--force",
        action="store_true",
        help="Advance even when validation fails.",
    )

    rollback_parser = subparsers.add_parser("rollback", help="Rollback to a prior stage.")
    rollback_parser.add_argument("--feature", help="Feature name.")
    rollback_parser.add_argument("--to-stage", help="Stage to roll back to.")
    rollback_parser.add_argument("--reason", help="Reason for the rollback.")

    render_status_parser = subparsers.add_parser(
        "render-status-text", help="Render SessionStart / reminder context."
    )
    render_status_parser.add_argument("--feature", help="Feature name.")
    render_status_parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Return an empty status instead of failing when no feature is active.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "init":
            payload = command_init(args)
        elif args.command == "status":
            payload = command_status(args)
        elif args.command == "validate":
            payload = command_validate(args)
        elif args.command == "advance":
            payload = command_advance(args)
        elif args.command == "rollback":
            payload = command_rollback(args)
        elif args.command == "render-status-text":
            payload = {
                "ok": True,
                "text": render_status_text(
                    command_status(
                        argparse.Namespace(
                            feature=args.feature,
                            allow_missing=args.allow_missing,
                        )
                    )
                ),
            }
        else:
            raise ValueError(f"unsupported command: {args.command}")
    except Exception as exc:  # noqa: BLE001 - CLI must return friendly JSON errors.
        print_json({"ok": False, "error": str(exc)})
        return 1

    if "ok" not in payload:
        payload["ok"] = True
    print_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
