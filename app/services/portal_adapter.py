def submit_to_sandbox(complaint_id: str) -> dict:
    """
    Local demo only.

No network call is made.
    No government portal is contacted.
    The acknowledgment is deterministic for retry safety.
    """
    return {
        "destination": "sandbox",
        "ack_ref": f"SANDBOX-{complaint_id}",
        "message": (
            "Accepted by the local demonstration workflow. "
            "This is not a government complaint number."
        ),
    }
