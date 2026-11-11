def generate_complaint(issue):
    subject = "Request to inspect a possible road pothole"

    body = (
        "To the relevant road-maintenance authority,\n\n"
        "Please inspect a possible pothole at the following "
        "approximate location:\n\n"
        f"Latitude: {issue.lat:.6f}\n"
        f"Longitude: {issue.lon:.6f}\n"
        f"First observed: {issue.first_seen_at.isoformat()}\n"
        f"Recorded observations: {issue.observation_count}\n\n"
        "A user has reviewed and confirmed the detection. "
        "The coordinates represent the phone's approximate GPS "
        "location, not a surveyed pothole position.\n\n"
        "Physical pothole size: unknown.\n"
        "Responsible authority: not verified.\n"
        "Contractor: not verified.\n\n"
        "Please inspect the location and arrange repairs if required.\n\n"
        f"Internal issue reference: {issue.id}\n\n"
        "DEMO NOTICE: This draft is intended for the application's "
        "sandbox workflow. It has not been submitted to a "
        "government portal."
    )

    return subject, body