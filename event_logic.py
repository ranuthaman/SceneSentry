
def detect_zone_entries(
    detections,
    zone,
    camera_id="Camera 1",
    cooldown_seconds=3.0
):
    """
    Detect candidate observations of people inside a configured zone.

    zone format: (x1, y1, x2, y2)

    This is a simple prototype. It does not track individual people,
    so it cannot reliably confirm that a specific person entered.
    """

    zx1, zy1, zx2, zy2 = zone

    if zx1 >= zx2 or zy1 >= zy2:
        raise ValueError("Invalid zone coordinates")

    events = []
    last_event_time = float("-inf")

    # Process person detections in timestamp order.
    people = sorted(
        (
            d for d in detections
            if d.get("object") == "person"
        ),
        key=lambda d: d["timestamp"]
    )

    for detection in people:
        center_x = (detection["x1"] + detection["x2"]) / 2
        center_y = (detection["y1"] + detection["y2"]) / 2

        inside = (
            zx1 <= center_x <= zx2
            and zy1 <= center_y <= zy2
        )

        timestamp = detection["timestamp"]

        # Limit repeated alerts while someone remains in the zone.
        if inside and timestamp - last_event_time >= cooldown_seconds:
            events.append({
                "timestamp": timestamp,
                "camera_id": camera_id,
                "category": "person_in_configured_zone",
                "summary": "Person detected in the configured zone",
                "evidence_path": "",
                "review_status": "needs_review"
            })

            last_event_time = timestamp

    return events
