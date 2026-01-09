import gradio as gr
from backend.state import global_state
from backend.services.driver_services import analyze_trip
from backend.services.driver_services import (
    analyze_trip_segment,
    get_segment_count,
)
from pathlib import Path


TRIPS_ROOT = Path("data/trips")
MAX_SEGMENTS = 15

def build_driver_view():
    with gr.Column(elem_classes=["dmk-card", "dashboard"]):

        gr.Markdown("## Driver Dashboard")

        # --------------------
        # Trip selection
        # --------------------
        trip_dropdown = gr.Dropdown(
            choices=[],
            label="Select Trip",
            interactive=True
        )

        segment_dropdown = gr.Dropdown(
            choices=[],
            label="Select Segment",
            interactive=True
        )

        segment_hint = gr.Markdown(
            "_Default: first 30s segment_",
            elem_classes=["segment-hint"]
        )

        analyze_btn = gr.Button(
            "Analyze Segment",
            elem_classes=["button"]
        )

        gr.Markdown("---")

        # --------------------
        # Output
        # --------------------
        gr.Markdown("### Driving Behaviour Feedback")
        output_box = gr.Markdown(
            "No analysis yet.",
            elem_classes=["output"],
            visible = False
        )

        # debug_box = gr.Markdown(visible=False)

        # Hidden refresh trigger
        refresh_state = gr.State(0)

        # -----------------------------
        # Helpers (UNCHANGED)
        # -----------------------------

        def list_trips():
            driver_id = global_state.current_user_id
            print(f">>> DRIVER VIEW: refresh trips for driver={driver_id}")

            if driver_id is None:
                print(">>> DRIVER VIEW: no driver ID")
                return gr.update(choices=[])

            driver_dir = TRIPS_ROOT / driver_id
            if not driver_dir.exists():
                print(">>> DRIVER VIEW: driver dir does not exist:", driver_dir)
                return gr.update(choices=[])

            trips = sorted(
                p.name for p in driver_dir.iterdir() if p.is_dir()
            )

            return gr.update(choices=trips)

        def analyze_selected_trip(trip_id, segment_idx):
            driver_id = global_state.current_user_id
            print(f">>> DRIVER VIEW: driver={driver_id}, trip={trip_id}, segment={segment_idx}")

            if not trip_id:
                return "❌ Please select a trip"

            try:
                result = analyze_trip_segment(driver_id, trip_id, segment_idx)
                return gr.update(value=result["coaching"], visible=True)
            except Exception as e:
                return f"❌ Analysis failed: {e}"


        def refresh_segments(trip_id):
            if not trip_id:
                return gr.update(choices=[], value=None)

            driver_id = global_state.current_user_id

            segments = get_segment_count(driver_id, trip_id)

            print(">>> TOTAL SEGMENTS:", len(segments))

            if not segments:
                return gr.update(choices=[], value=None)

            limited = segments[:MAX_SEGMENTS]

            return gr.update(
                choices=limited,
                value=limited[0]
            )


        # -----------------------------
        # Wiring (UNCHANGED)
        # -----------------------------

        trip_dropdown.change(
            fn=refresh_segments,
            inputs=trip_dropdown,
            outputs=segment_dropdown
        )

        analyze_btn.click(
            fn=analyze_selected_trip,
            inputs=[trip_dropdown, segment_dropdown],
            outputs=output_box
        )

        refresh_state.change(
            fn=list_trips,
            inputs=[],
            outputs=trip_dropdown
        )

        logout_btn = gr.Button(
            "Logout",
            elem_classes=["logout-btn"]
        )

        return refresh_state, logout_btn
