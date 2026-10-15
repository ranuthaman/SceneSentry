
import os
import tempfile

import cv2
import pandas as pd
import streamlit as st

from video_processor import process_video
from event_logic import detect_zone_entries
import database
import search


# ---------------- CONFIG ----------------

DB_PATH = "scenesentry.db"

st.set_page_config(
    page_title="SceneSentry",
    page_icon="🎥",
    layout="wide"
)

database.init_db(DB_PATH)


# ---------------- HEADER ----------------

st.title("🎥 SceneSentry")
st.caption(
    "CCTV Video Intelligence | Candidate incident detection "
    "| Searchable event timeline"
)

st.info(
    "Alerts are automated observations, not confirmed incidents. "
    "Please review the footage before taking action."
)


# ---------------- SIDEBAR ----------------

st.sidebar.header("⚙️ Processing Settings")

confidence = st.sidebar.slider(
    "YOLO confidence",
    min_value=0.10,
    max_value=0.90,
    value=0.35,
    step=0.05
)

frame_stride = st.sidebar.selectbox(
    "Frame sampling",
    options=[1, 2, 3, 5],
    index=1,
    help="Higher values process fewer frames and may miss events."
)

camera_id = st.sidebar.text_input(
    "Camera name",
    value="Camera 1"
)


# ---------------- VIDEO UPLOAD ----------------

st.header("1. Upload CCTV Footage")

uploaded_video = st.file_uploader(
    "Choose a video file",
    type=["mp4", "avi", "mov", "mkv"]
)

if uploaded_video is not None:
    st.video(uploaded_video)

    st.caption(
        f"File: {uploaded_video.name} | "
        f"Size: {uploaded_video.size / (1024 * 1024):.1f} MB"
    )

    st.header("2. Configure Detection Zone")

    # Read dimensions from a temporary copy of the uploaded video.
    temp_path = None

    try:
        suffix = os.path.splitext(uploaded_video.name)[1] or ".mp4"

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as temp_file:
            temp_file.write(uploaded_video.getvalue())
            temp_path = temp_file.name

        cap = cv2.VideoCapture(temp_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if width <= 0 or height <= 0:
            st.error("Could not read video dimensions.")
            st.stop()

        st.write(f"Video resolution: **{width} × {height}**")

        # Default zone: central-to-lower part of the image.
        st.caption(
            "Adjust the rectangle coordinates in pixels. "
            "The default zone is only an example, not a real restricted area."
        )

        col1, col2 = st.columns(2)

        with col1:
            zone_x1 = st.number_input(
                "Zone left (x1)", 0, width - 1,
                int(width * 0.39)
            )
            zone_y1 = st.number_input(
                "Zone top (y1)", 0, height - 1,
                int(height * 0.37)
            )

        with col2:
            zone_x2 = st.number_input(
                "Zone right (x2)", 1, width,
                max(1, int(width * 0.65))
            )
            zone_y2 = st.number_input(
                "Zone bottom (y2)", 1, height,
                max(1, int(height * 0.97))
            )

        st.caption(
            "Coordinates use the top-left corner as (0, 0). "
            "The current prototype checks whether a detected person's "
            "bounding-box center lies inside this rectangle."
        )

        run_button = st.button(
            "🚀 Process Video",
            type="primary",
            use_container_width=True
        )

        if run_button:
            if zone_x1 >= zone_x2 or zone_y1 >= zone_y2:
                st.error("Invalid zone: right must exceed left, and bottom must exceed top.")
            else:
                try:
                    progress = st.progress(0, text="Starting video processing...")

                    progress.progress(10, text="Running YOLO detection...")

                    detections = process_video(
                        temp_path,
                        confidence=confidence,
                        frame_stride=frame_stride
                    )

                    progress.progress(65, text="Finding candidate zone observations...")

                    events = detect_zone_entries(
                        detections,
                        (
                            int(zone_x1),
                            int(zone_y1),
                            int(zone_x2),
                            int(zone_y2)
                        ),
                        camera_id=camera_id
                    )

                    progress.progress(80, text="Saving events to database...")

                    for event in events:
                        event["category"] = "person_in_configured_zone"
                        event["summary"] = (
                            "Person detected in the configured zone"
                        )
                        event["review_status"] = "needs_review"
                        event["evidence_path"] = uploaded_video.name

                        database.insert_event(
                            event,
                            db_path=DB_PATH
                        )

                    progress.progress(100, text="Processing complete!")

                    st.session_state["last_detection_count"] = len(detections)
                    st.session_state["last_event_count"] = len(events)

                    st.success("Video processing completed!")

                except Exception as error:
                    st.error(f"Processing failed: {error}")

                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)

    except Exception as error:
        st.error(f"Could not inspect the video: {error}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# ---------------- METRICS ----------------

st.header("3. Overview")

all_events = database.get_events(db_path=DB_PATH)

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "YOLO detections (last run)",
    st.session_state.get("last_detection_count", 0)
)

metric2.metric(
    "Candidate alerts (last run)",
    st.session_state.get("last_event_count", 0)
)

metric3.metric(
    "Events stored",
    len(all_events)
)


# ---------------- SEARCH ----------------

st.header("4. Search Event Timeline")

query_col, camera_col, category_col = st.columns(3)

with query_col:
    search_text = st.text_input(
        "Search events",
        placeholder="e.g. person, configured zone"
    )

with camera_col:
    cameras = sorted({
        event["camera_id"] for event in all_events
    })
    selected_camera = st.selectbox(
        "Camera",
        ["All cameras"] + cameras
    )

with category_col:
    categories = search.get_search_categories(db_path=DB_PATH)
    selected_category = st.selectbox(
        "Event category",
        ["All categories"] + categories
    )

try:
    filtered_events = search.search_events(
        text=search_text,
        camera_id=(
            selected_camera
            if selected_camera != "All cameras"
            else None
        ),
        category=(
            selected_category
            if selected_category != "All categories"
            else None
        ),
        db_path=DB_PATH
    )

    st.write(f"**{len(filtered_events)} matching event(s)**")

    if filtered_events:
        table_data = []

        for event in filtered_events:
            table_data.append({
                "Time (seconds)": round(event["timestamp"], 2),
                "Camera": event["camera_id"],
                "Category": event["category"],
                "Summary": event["summary"],
                "Review status": event["review_status"],
                "Evidence file": event["evidence_path"]
            })

        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True
        )

        csv_data = pd.DataFrame(table_data).to_csv(index=False)

        st.download_button(
            "⬇️ Export matching events as CSV",
            data=csv_data,
            file_name="scenesentry_events.csv",
            mime="text/csv"
        )

    else:
        st.info("No matching events. Try another search or process a video.")

except Exception as error:
    st.error(f"Could not load the event timeline: {error}")


# ---------------- FOOTER ----------------

st.divider()
st.caption(
    "SceneSentry prototype | Automated observations require human review. "
    "The current version does not track individual identities or confirm "
    "that an incident occurred."
)
