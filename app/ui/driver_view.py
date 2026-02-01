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

        trip_dropdown = gr.Dropdown(
            choices=[],
            label="Select Day",
            interactive=True
        )

        segment_dropdown = gr.Dropdown(
            choices=["Waiting for stream..."],
            label="Current Trip",
            interactive=False
        )

        # segment_hint = gr.Markdown("_Default: first 30s segment_", elem_classes=["segment-hint"])

        # analyze_btn = gr.Button("Analyze Trip")

        gr.Markdown("---")
        
        output_box = gr.Markdown("### Driving Behaviour Feedback\n", elem_classes=["feedback-box"], visible=True)
    
    current_trip_state = gr.State(None)
    last_llm_idx_state = gr.State(None)
    segment_stream_state = gr.State([])   # list of severities
    segment_pointer_state = gr.State(0)   # current index

    refresh_state = gr.State(0)

    def list_trips():
        driver_id = global_state.current_user_id
        print(f">>> DRIVER VIEW: refresh trips for driver={driver_id}")

        if not driver_id:
            return gr.update(choices=[])

        driver_dir = TRIPS_ROOT / driver_id
        if not driver_dir.exists():
            return gr.update(choices=[])

        raw_trips = sorted([p.name for p in (TRIPS_ROOT / global_state.current_user_id).iterdir() if p.is_dir()])
        display_choices = [(f"Day {i}", real_trip) for i, real_trip in enumerate(raw_trips, 1)]
        
        return gr.update(choices=display_choices, value=None)

    # def refresh_segments(trip_id):
    #     if not trip_id:
    #         return gr.update(choices=[], value=None)
    #     display_segments = [f"Trip {i+1}" for i in range(MAX_SEGMENTS)]

    #     return gr.update(choices=display_segments, value=display_segments[0] if display_segments else None)

    # def analyze_with_mapping(trip_id, segment_display):
    #     driver_id = global_state.current_user_id

    #     if not trip_id:
    #         return gr.update(value="### Driving Behaviour Feedback\n\n❌ Please select a trip")

    #     if not segment_display:
    #         return gr.update(value="### Driving Behaviour Feedback\n\n❌ Please select a segment")

    #     try:
    #         segment_idx = int(segment_display.split()[-1]) - 1
    #         actual_segments = get_segment_count(driver_id, trip_id)
    #         actual_count = len(actual_segments)

    #         if segment_idx >= actual_count:
    #             return gr.update(value="### Driving Behaviour Feedback\n\n❌ Selected segment not available (only {} segments exist)".format(actual_count))
    #         result = analyze_trip_segment(driver_id, trip_id, segment_idx)
    #         return gr.update(value=f"### Driving Behaviour Feedback\n\n{result['coaching']}")
    #     except Exception as e:
    #         return gr.update(value=f"### Driving Behaviour Feedback\n\n❌ Analysis failed: {e}")

    def init_segment_stream(trip_id):
        driver_id = global_state.current_user_id

        if not trip_id:
            return [], 0, None, None, gr.update(), gr.update()

        segments = load_segment_severities_for_stream(driver_id, trip_id)

        if not segments:
            return [], 0, None, None, gr.update(), gr.update()

        # ---- Segment 1 display ----
        first_seg = segments[0]
        severity = first_seg["severity"]

        label = f"Trip 1 — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)

        # ---- Segment 1 analysis (IMPORTANT FIX) ----
        feedback_update = gr.update()

        if should_auto_query(severity, 0, None):
            row = _registry._load_trip_df(driver_id, trip_id).iloc[0].to_dict()
            summary = build_llm_summary(row)
            coaching = get_coaching_feedback(summary)

            feedback_update = gr.update(
                value=f"### Driving Behaviour Feedback:\n\n{coaching}"
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

    
    def advance_segment_stream(segments, idx, last_llm_idx, trip_id):
        if not segments:
            return idx, last_llm_idx, gr.update(), gr.update()

        seg = segments[idx]
        severity = seg["severity"]

        # update dropdown display
        label = f"Trip {idx + 1} — Severity: {severity}"
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
                value=f"### Driving Behaviour Feedback:\n\n{coaching}"
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


    trip_dropdown.change(
        fn=init_segment_stream,
        inputs=trip_dropdown,
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            last_llm_idx_state,
            current_trip_state,
            segment_dropdown,
            output_box          # 🔑 now written during init
        ],
        show_progress=False
    )
    # analyze_btn.click(
    #     fn=analyze_with_mapping,
    #     inputs=[trip_dropdown, segment_dropdown],
    #     outputs=[output_box],
    #     show_progress=False
    # )

    refresh_state.change(
        fn=list_trips,
        inputs=[],
        outputs=trip_dropdown,
        show_progress=False
    )

    logout_btn = gr.Button("Logout", elem_classes=["logout-btn"])

    STREAM_INTERVAL_SEC = 20.0  # 🔧 adjust freely

    gr.Timer(STREAM_INTERVAL_SEC).tick(
        fn=advance_segment_stream,
        inputs=[
            segment_stream_state,
            segment_pointer_state,
            last_llm_idx_state,
            current_trip_state 
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