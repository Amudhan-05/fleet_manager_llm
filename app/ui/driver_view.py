import gradio as gr
from backend.state import global_state
from backend.services.driver_services import (
    analyze_trip_segment, 
    get_segment_count, 
    get_segment_severities, 
    load_segment_severities_for_stream
)
from backend.processing.severity import build_llm_summary
from backend.llm.llm_engine import get_coaching_feedback
from pathlib import Path
from backend.registry.trip_registry import TripRegistry

TRIPS_ROOT = Path("data/trips")
_registry = TripRegistry(TRIPS_ROOT)
MAX_SEGMENTS = 15

def build_driver_view():
    with gr.Column(elem_classes=["fixed-width-container"]):
        gr.Markdown("# Driver Dashboard", elem_classes=["center-header_driver"])
        gr.Markdown("Live feedback about driving behaviour.")
        gr.Markdown("---")
        start_btn = gr.Button("Start Trip", variant="primary")
        stop_btn = gr.Button("Stop Trip", variant="secondary")

        segment_dropdown = gr.Dropdown(
            choices=["Waiting for stream..."],
            label="Current Trip",
            interactive=False
        )
        gr.Markdown("---")
        
        output_box = gr.HTML("<h3>Driving Behaviour Feedback</h3>", elem_classes=["feedback-box"], visible=True)

    current_trip_state = gr.State(None)
    last_llm_idx_state = gr.State(None)
    segment_stream_state = gr.State([])   # list of severities
    segment_pointer_state = gr.State(0)   # current index
    streaming_state = gr.State(False)

    refresh_state = gr.State(0)
    def start_streaming():
        driver_id = global_state.current_user_id
        print(f">>> DRIVER VIEW: starting stream for driver={driver_id}")

        if not driver_id:
            return [], 0, None, None, gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."), gr.update(value="<h3>Driving Behaviour Feedback</h3><p>❌ No driver ID</p>"), False

        driver_dir = TRIPS_ROOT / driver_id
        if not driver_dir.exists():
            return [], 0, None, None, gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."), gr.update(value="<h3>Driving Behaviour Feedback</h3><p>❌ No trips directory</p>"), False

        raw_trips = sorted([p.name for p in driver_dir.iterdir() if p.is_dir()])
        if not raw_trips:
            return [], 0, None, None, gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."), gr.update(value="<h3>Driving Behaviour Feedback</h3><p>❌ No trips available</p>"), False

        trip_id = raw_trips[0]  # Implicitly use the first trip as "day 1"

        segments = load_segment_severities_for_stream(driver_id, trip_id)

        if not segments:
            return [], 0, None, None, gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."), gr.update(value="<h3>Driving Behaviour Feedback</h3><p>❌ No segments</p>"), False

        first_seg = segments[0]
        severity = first_seg["severity"]

        label = f"Segment 1 — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)
        feedback_update = gr.update()

        if should_auto_query(severity, 0, None):
            row = _registry._load_trip_df(driver_id, trip_id).iloc[0].to_dict()
            summary = build_llm_summary(row)
            coaching = get_coaching_feedback(summary)

            feedback_update = gr.update(
                value=f"<h3>Driving Behaviour Feedback</h3><p>{coaching}</p>"
            )

            last_llm_idx = 0
        else:
            last_llm_idx = None

        return (
            segments,            # segment_stream_state
            0,                   # segment_pointer_state
            last_llm_idx,        # last_llm_idx_state
            trip_id,             # current_trip_state
            dropdown_update,     # segment_dropdown
            feedback_update,     # output_box
            True                 # streaming_state (start streaming)
        )

    def stop_streaming():
        return (
            [],                  # segment_stream_state
            0,                   # segment_pointer_state
            None,                # last_llm_idx_state
            None,                # current_trip_state
            gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."),  # segment_dropdown
            gr.update(value="<h3>Driving Behaviour Feedback</h3>"),  # output_box
            False                # streaming_state (stop streaming)
        )

    def init_segment_stream(trip_id):
        driver_id = global_state.current_user_id

        if not trip_id:
            return [], 0, None, None, gr.update(), gr.update()

        segments = load_segment_severities_for_stream(driver_id, trip_id)

        if not segments:
            return [], 0, None, None, gr.update(), gr.update()
        first_seg = segments[0]
        severity = first_seg["severity"]

        label = f"Segment 1 — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)
        feedback_update = gr.update()

        if should_auto_query(severity, 0, None):
            row = _registry._load_trip_df(driver_id, trip_id).iloc[0].to_dict()
            summary = build_llm_summary(row)
            coaching = get_coaching_feedback(summary)

            feedback_update = gr.update(
                value=f"<h3>Driving Behaviour Feedback</h3><p>{coaching}</p>"
            )

            last_llm_idx = 0
        else:
            last_llm_idx = None

        return (
            segments,            # segment_stream_state
            0,                   # segment_pointer_state
            last_llm_idx,        # last_llm_idx_state
            trip_id,             # current_trip_state
            dropdown_update,     # segment_dropdown
            feedback_update      # 🔑 output_box
        )

    def advance_segment_stream(segments, idx, last_llm_idx, trip_id, streaming):
        if not streaming:
            return idx, last_llm_idx, gr.update(), gr.update()

        if not segments:
            return idx, last_llm_idx, gr.update(), gr.update()

        seg = segments[idx]
        severity = seg["severity"]

        label = f"Segment {idx + 1} — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)

        feedback_update = gr.update()  # default: no change

        # auto-query logic
        if should_auto_query(severity, idx, last_llm_idx):
            if trip_id is not None:
                driver_id = global_state.current_user_id
                row = _registry._load_trip_df(driver_id, trip_id).iloc[idx].to_dict()
                summary = build_llm_summary(row)
                coaching = get_coaching_feedback(summary)

            feedback_update = gr.update(
                value=f"<h3>Driving Behaviour Feedback</h3><p>{coaching}</p>"
            )
            last_llm_idx = idx
        
        next_idx = idx + 1
        if next_idx >= len(segments):
            next_idx = idx  # clamp at last segment

        return next_idx, last_llm_idx, dropdown_update, feedback_update

    
    def should_auto_query(severity, segment_idx, last_queried_idx):
        if severity == "LOW":
            return last_queried_idx != segment_idx
        if severity == "MEDIUM":
            return last_queried_idx != segment_idx
        if severity == "HIGH":
            return last_queried_idx != segment_idx
        return False
    start_btn.click(
        fn=start_streaming,
        inputs=[],
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            last_llm_idx_state,
            current_trip_state,
            segment_dropdown,
            output_box,
            streaming_state
        ],
        show_progress=False
    )
    stop_btn.click(
        fn=stop_streaming,
        inputs=[],
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            last_llm_idx_state,
            current_trip_state,
            segment_dropdown,
            output_box,
            streaming_state
        ],
        show_progress=False
    )
    refresh_state.change(
        fn=lambda: None,  # No-op since list_trips is removed
        inputs=[],
        outputs=[],
        show_progress=False
    )

    logout_btn = gr.Button("Logout", elem_classes=["logout-btn"])

    STREAM_INTERVAL_SEC = 10.0  # 🔧 adjust freely

    gr.Timer(STREAM_INTERVAL_SEC).tick(
        fn=advance_segment_stream,
        inputs=[
            segment_stream_state,
            segment_pointer_state,
            last_llm_idx_state,
            current_trip_state,
            streaming_state 
        ],
        outputs=[
            segment_pointer_state,
            last_llm_idx_state,
            segment_dropdown,
            output_box
        ],
        show_progress=False
    )


    return refresh_state, logout_btn