import gradio as gr
from backend.services.coach_services import (
    get_driver_status,
    list_drivers,
    list_trips,
    list_segments,
    analyze_segment,
    get_segment_severities
)
from backend.processing.severity import assign_severity
from backend.registry.trip_registry import TripRegistry
from pathlib import Path

TRIPS_ROOT = Path("data/trips")
_registry = TripRegistry(TRIPS_ROOT)

MAX_SEGMENTS = 15
def build_coach_view():
    with gr.Column(elem_classes=["fixed-width-container"]):
        gr.Markdown("## Fleet Manager Dashboard", elem_classes=["center-header_coach"])
        gr.Markdown("---")
        
        driver_dd = gr.Dropdown(
            label="Select Driver",
            choices=[],
            interactive=True
        )

        trip_dd = gr.Dropdown(
            label="Select Day",
            choices=[],
            interactive=True
        )

        segment_dd = gr.Dropdown(
            label="Select Trip",
            choices=[],
            interactive=True
        )
        gr.Markdown("### Driver Details")

        driver_status_box = gr.Markdown("Select a driver to view details.", elem_classes=["output-box"], visible=True)

        segment_severity_box = gr.HTML( "<h3>Severity</h3><em>Select Trip to view severity</em>", visible=True )

        analyze_btn = gr.Button("Analyze Trip")

        output_box = gr.Markdown("### Driving Behaviour Feedback\nSelect trip, then click 'Analyze Trip' to get feedback", elem_classes=["feedback-box"], visible=True)

    refresh_state = gr.State(0)

    def refresh_status(driver_id):
        if not driver_id:
            return gr.update(value="Select a driver to view details.")

        info = get_driver_status(driver_id)
        if not info:
            return gr.update(value="Driver not found.")

        status_icon = "🟢 Online" if info["online"] else "🔴 Offline"
        return gr.update(
            value=f"**Driver ID:** {info['driver_id']} , **Status:** {status_icon}"
        )

    def refresh_drivers():
        drivers = list_drivers()
        return gr.update(choices=drivers, value=None)

    def refresh_trips(driver_id):
        if not driver_id:
            return gr.update(choices=[], value=None)

        raw_trips = list_trips(driver_id)
        display_choices = [(f"Day {i}", trip_name) for i, trip_name in enumerate(raw_trips, 1)]
        return gr.update(choices=display_choices, value=None)

    def refresh_segments(driver_id, trip_id):
        if not driver_id or not trip_id:
            return gr.update(choices=[], value=None)
        
        choices = [(f"Trip {i+1}", i) for i in range(MAX_SEGMENTS)]

        return gr.update(
            choices=choices,
            value=0  # default to Segment 1
        )

    def run_analysis(driver_id, trip_id, segment_display):
        if not driver_id or not trip_id or not segment_display:
            return gr.update(value="❌ Please select driver, day, and trip.")

        try:
            segment_idx = segment_display  # already an int
            result = analyze_segment(driver_id, trip_id, segment_idx)
            return gr.update(value=f"### Driver's Behaviour Feedback\n\n{result['coaching']}")
        except Exception as e:
            return gr.update(value=f"❌ Error: {e}")
    

    def show_selected_segment_severity(driver_id, trip_id, segment_idx):
        if not driver_id or not trip_id or segment_idx is None:
            return gr.update(value="<h3>Trip Severity</h3>")
        try:
            df = _registry._load_trip_df(driver_id, trip_id)
            if segment_idx >= len(df):
                return gr.update(value="<h3>Trip Severity</h3><p>Trip does not exist.</p>")
            row = df.iloc[segment_idx].to_dict()
            severity = assign_severity(row)
            icon = "🟢" if severity == "LOW" else "🟡" if severity == "MEDIUM" else "🔴"
            severity_display = severity.capitalize()
            return gr.update(value=f"<h3>Trip Severity</h3><p><b>Trip {segment_idx+1}</b>: {icon}{severity_display}</p>")
        except Exception as e:
            return gr.update(value=f"<h3>Trip Severity</h3><p>❌ Error: {e}</p>")



    driver_dd.change(
        fn=refresh_status,
        inputs=driver_dd,
        outputs=driver_status_box,
        show_progress=False
    )

    driver_dd.change(
        fn=refresh_trips,
        inputs=driver_dd,
        outputs=trip_dd,
        show_progress=False
    )

    refresh_state.change(
        fn=refresh_drivers,
        inputs=[],
        outputs=driver_dd,
        show_progress=False
    )

    trip_dd.change(
        fn=refresh_segments,
        inputs=[driver_dd, trip_dd],
        outputs=segment_dd,
        show_progress=False
    )

    segment_dd.change(
        fn=show_selected_segment_severity,
        inputs=[driver_dd, trip_dd, segment_dd],
        outputs=segment_severity_box,
        show_progress=False
    )

    analyze_btn.click(
        fn=run_analysis,
        inputs=[driver_dd, trip_dd, segment_dd],
        outputs=output_box,
        show_progress= False
    )

    logout_btn = gr.Button("Logout", elem_classes=["logout-btn"])

    return refresh_state, logout_btn