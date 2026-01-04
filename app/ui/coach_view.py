import gradio as gr
from backend.services.coach_services import (
    get_driver_status,
    list_drivers,
    list_trips,
    list_segments,
    analyze_segment,
)

MAX_SEGMENTS = 15
def build_coach_view():
    with gr.Column(elem_classes=["dmk-card", "dashboard"]):

        gr.Markdown("## Fleet Manager Dashboard")

        gr.Markdown(
            "Monitor active drivers and their current status."
        )

        gr.Markdown("---")

        # --------------------
        # Driver status output
        # --------------------
        gr.Markdown("### Driver Details")

        driver_status_box = gr.Markdown(
            "Select a driver to view status.",
            elem_classes=["output"]
        )

        driver_dd = gr.Dropdown(
            label="Select Driver",
            choices=[],
            interactive=True
        )

        trip_dd = gr.Dropdown(
            label="Select Trip",
            choices=[],
            interactive=True
        )

        segment_dd = gr.Dropdown(
            label="Select Segment",
            choices=[],
            interactive=True
        )

        analyze_btn = gr.Button("Analyze Segment")
        output_box = gr.Markdown(
            "No analysis yet.",
            elem_classes=["output"]
        )

        # Hidden refresh trigger (unchanged)
        refresh_state = gr.State(0)

        # -----------------------------
        # Helpers (UNCHANGED)
        # -----------------------------
        def refresh_status(driver_id):
            if not driver_id:
                return "Select a driver to view status."

            info = get_driver_status(driver_id)
            if not info:
                return "Driver not found."

            return (
                f"**Driver ID:** `{info['driver_id']}`\n\n"
                f"**Status:** 🟢 Active\n\n"
                f"**Trips available:** {info['trip_count']}"
            )
        
        def refresh_drivers():
            drivers = list_drivers()
            return gr.update(choices=drivers, value=None)

        def refresh_trips(driver_id):
            if not driver_id:
                return gr.update(choices=[], value=None)

            trips = list_trips(driver_id)
            return gr.update(choices=trips, value=None)

        def refresh_segments(driver_id, trip_id):
            if not driver_id or not trip_id:
                return gr.update(choices=[], value=None)

            segments = list_segments(driver_id, trip_id)
            limited = segments[:MAX_SEGMENTS]

            return gr.update(
                choices=limited,
                value=limited[0] if limited else None
            )

        def run_analysis(driver_id, trip_id, segment_idx):
            if not driver_id or not trip_id or segment_idx is None:
                return "❌ Please select driver, trip, and segment."

            result = analyze_segment(driver_id, trip_id, segment_idx)
            return result["coaching"]

        # -----------------------------
        # Wiring (UNCHANGED)
        # -----------------------------
        driver_dd.change(
            fn=refresh_status,
            inputs=driver_dd,
            outputs=driver_status_box
        )

        driver_dd.change(
            fn=refresh_trips,
            inputs=driver_dd,
            outputs=trip_dd
        )

        refresh_state.change(
            fn=refresh_drivers,
            inputs=[],
            outputs=driver_dd
        )

        trip_dd.change(
            fn=refresh_segments,
            inputs=[driver_dd, trip_dd],
            outputs=segment_dd
        )

        analyze_btn.click(
            fn=run_analysis,
            inputs=[driver_dd, trip_dd, segment_dd],
            outputs=output_box
        )

        logout_btn = gr.Button(
            "Logout",
            elem_classes=["logout-btn"]
        )

        return refresh_state,logout_btn
