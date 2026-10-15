
def detect_zone_entries(detections, zone, camera_id="Camera 1"):
    """
    Prototype zone-entry detection.

    NOTE: This version treats all people as one group.
    It is a basic demo rule, not individual person tracking.
    """
    zx1, zy1, zx2, zy2 = zone
    events = []
    previous_inside = False

    people = sorted(
        (d for d in detections if d["object"] == "person"),
        key=lambda d: d["timestamp"]
    )

    for detection in people:
        center_x = (detection["x1"] + detection["x2"]) / 2
        center_y = (detection["y1"] + detection["y2"]) / 2

        inside = (
            zx1 <= center_x <= zx2
            and zy1 <= center_y <= zy2
        )

        if inside and not previous_inside:
            events.append({
                "timestamp": detection["timestamp"],
                "camera_id": camera_id,
                "category": "restricted_zone_entry",
                "summary": "Person detected entering the configured zone",
                "evidence_path": "",
                "review_status": "needs_review"
            })

        previous_inside = inside

    return events
