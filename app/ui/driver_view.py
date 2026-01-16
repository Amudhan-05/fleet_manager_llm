import gradio as gr
from backend.state import global_state
from backend.services.driver_services import analyze_trip_segment, get_segment_count
from pathlib import Path

TRIPS_ROOT = Path("data/trips")
MAX_SEGMENTS = 15

def build_driver_view():
    with gr.Column(elem_classes=["fixed-width-container"]):
        gr.Markdown("# Driver Dashboard", elem_classes=["center-header_driver"])
        gr.Markdown("Get feedback about driving behaviour.")
        gr.Markdown("---")

        trip_dropdown = gr.Dropdown(
            choices=[],
            label="Select Day",
            interactive=True
        )

        segment_dropdown = gr.Dropdown(
            choices=[],
            label="Select Trip",
            interactive=True
        )

        segment_hint = gr.Markdown("_Default: first 30s segment_", elem_classes=["segment-hint"])

        analyze_btn = gr.Button("Analyze Trip")

        gr.Markdown("---")
        
        output_box = gr.Markdown("### Driving Behaviour Feedback\n\nSelect a day and trip, then click 'Analyze Trip' to get feedback.", elem_classes=["feedback-box"], visible=True)

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

    def refresh_segments(trip_id):
        if not trip_id:
            return gr.update(choices=[], value=None)
        display_segments = [f"Trip {i+1}" for i in range(MAX_SEGMENTS)]

        return gr.update(choices=display_segments, value=display_segments[0] if display_segments else None)

    def analyze_with_mapping(trip_id, segment_display):
        driver_id = global_state.current_user_id

        if not trip_id:
            return gr.update(value="### Driving Behaviour Feedback\n\n❌ Please select a trip")

        if not segment_display:
            return gr.update(value="### Driving Behaviour Feedback\n\n❌ Please select a segment")

        try:
            segment_idx = int(segment_display.split()[-1]) - 1
            actual_segments = get_segment_count(driver_id, trip_id)
            actual_count = len(actual_segments)

            if segment_idx >= actual_count:
                return gr.update(value="### Driving Behaviour Feedback\n\n❌ Selected segment not available (only {} segments exist)".format(actual_count))
            result = analyze_trip_segment(driver_id, trip_id, segment_idx)
            return gr.update(value=f"### Driving Behaviour Feedback\n\n{result['coaching']}")
        except Exception as e:
            return gr.update(value=f"### Driving Behaviour Feedback\n\n❌ Analysis failed: {e}")

    trip_dropdown.change(
        fn=refresh_segments,
        inputs=trip_dropdown,
        outputs=segment_dropdown,
        show_progress=False
    )

    analyze_btn.click(
        fn=analyze_with_mapping,
        inputs=[trip_dropdown, segment_dropdown],
        outputs=[output_box],
        show_progress=False
    )

    refresh_state.change(
        fn=list_trips,
        inputs=[],
        outputs=trip_dropdown,
        show_progress=False
    )

    logout_btn = gr.Button("Logout", elem_classes=["logout-btn"])

    return refresh_state, logout_btn