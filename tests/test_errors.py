"""Tests for the SERF-aligned error envelope."""

from __future__ import annotations

from enum import StrEnum

from mcp_safety_core.errors import ErrorCode, failure_response


class InstErr(StrEnum):
    DISK_FULL = "DISK_FULL"
    NETWORK_FAILURE = "NETWORK_FAILURE"


def test_envelope_shape_default() -> None:
    r = failure_response(ErrorCode.BAD_REQUEST, "bad input")
    assert r["ok"] is False
    assert r["error_code"] == "BAD_REQUEST"
    assert r["error_detail"] == "bad input"
    assert r["retryable"] is False
    assert r["suggested_action"] is not None
    assert isinstance(r["suggested_action"], str)


def test_domain_code_str_enum() -> None:
    r = failure_response(InstErr.DISK_FULL, "out of space", retryable=False)
    assert r["error_code"] == "DISK_FULL"
    assert r["retryable"] is False
    # No common default remediation for a domain code -> stays None
    assert r["suggested_action"] is None


def test_retryable_and_suggested_action() -> None:
    r = failure_response(
        InstErr.NETWORK_FAILURE,
        "conn refused",
        retryable=True,
        suggested_action="Retry with backoff",
    )
    assert r["retryable"] is True
    assert r["suggested_action"] == "Retry with backoff"


def test_common_code_default_remediation_present() -> None:
    assert failure_response(ErrorCode.TIMEOUT)["suggested_action"] is not None
    assert failure_response(ErrorCode.READ_ONLY)["suggested_action"] is not None


def test_extras_merged() -> None:
    r = failure_response(ErrorCode.FAILED, detail="x", status_code=500)
    assert r["status_code"] == 500


def test_string_code_that_is_a_common_member_resolves() -> None:
    r = failure_response("TIMEOUT", "slow")
    assert r["error_code"] == "TIMEOUT"
    assert r["retryable"] is False


def test_arbitrary_string_code_not_in_common_enum() -> None:
    r = failure_response("WEIRD", "boom")
    assert r["error_code"] == "WEIRD"
    assert r["retryable"] is False


def test_every_common_code_resolves() -> None:
    for code in ErrorCode:
        r = failure_response(code, "detail")
        assert r["ok"] is False
        assert r["error_code"] == code.value
        assert set(r) >= {"ok", "error_code", "error_detail", "retryable", "suggested_action"}
