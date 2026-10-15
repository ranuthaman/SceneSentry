
def detect_zone_entries(detections, zone, camera_id="Camera 1"):
    """
    Flag potential entries into a rectangular zone.

    zone = (x1, y1, x2, y2)
    Coordinates must match the original video resolution.
    """

    zx1, zy1, zx2, zy2 = zone
    events = []
    previous_inside = False

    for detection in sorted(detections, key=lambda d: d["timestamp"]):
        if detection["object"] != "person":
            continue

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
