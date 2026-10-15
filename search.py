
from database import get_events, get_categories


def search_events(
    text="",
    camera_id=None,
    category=None,
    start_time=None,
    end_time=None,
    db_path="scenesentry.db"
):
    """
    Search stored events using text and optional filters.

    Time values are seconds from the beginning of the video.
    """

    events = get_events(
        camera_id=camera_id,
        category=category,
        start_time=start_time,
        end_time=end_time,
        db_path=db_path
    )

    if not text.strip():
        return events

    words = text.lower().split()
    results = []

    for event in events:
        searchable_text = (
            event["category"] + " " +
            event["summary"] + " " +
            event["camera_id"] + " " +
            event["review_status"]
        ).lower()

        # Every search word must appear somewhere in the event.
        if all(word in searchable_text for word in words):
            results.append(event)

    return results


def get_search_categories(db_path="scenesentry.db"):
    """Get categories for dashboard dropdowns."""
    return get_categories(db_path=db_path)
