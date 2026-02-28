import gradio as gr
from backend.state import global_state
from backend.services.driver_services import load_segment_severities_for_stream
from backend.processing.severity import build_llm_summary
from backend.llm.llm_engine import get_coaching_feedback
from pathlib import Path
from backend.registry.trip_registry import TripRegistry
import threading
llm_lock = threading.Lock()
ALERT_SEVERITIES = {"high", "critical"}  # adjust to match your labels
TRIPS_ROOT = Path("data/trips")
_registry = TripRegistry(TRIPS_ROOT)
MAX_SEGMENTS = 15

def start_llm_for_segment(idx, summaries, llm_result_holder, severity):
    def _run():
        # summary = summaries[idx]
        # coaching = get_coaching_feedback(summary, severity, False)
        # llm_result_holder["result"] = coaching
        if not llm_lock.acquire(blocking=False):
            print("LLM is currently busy. Thread exiting.")
            return
        
        try:
            summary = summaries[idx]
            coaching = get_coaching_feedback(summary, severity, False)
            llm_result_holder["result"] = coaching
        finally:
            # ALWAYS release the lock so future threads can run
            llm_lock.release()

    t = threading.Thread(target=_run, daemon=True)
    t.start()

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
    next_llm_idx_state = gr.State(None)
    next_llm_result_state = gr.State(None)
    segment_summaries_state = gr.State(None)
    segment_stream_state = gr.State([])   # list of severities
    segment_pointer_state = gr.State(0)   # current index
    streaming_state = gr.State(False)
    trip_df_state = gr.State(None)
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
        df = _registry._load_trip_df(driver_id, trip_id)
        segments = load_segment_severities_for_stream(driver_id, trip_id)
        summaries = {
            i: build_llm_summary(df.iloc[i].to_dict())
            for i in range(len(segments))
        }
        if not segments:
            return [], 0, None, None, gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."), gr.update(value="<h3>Driving Behaviour Feedback</h3><p>❌ No Trips</p>"), False

        first_seg = segments[0]
        severity = first_seg["severity"]

        label = f"Segment 1 — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)

        permission_and_test_script = """
        <img src="x" style="display:none" onerror="
        (function() {
            const existing = document.getElementById('severity-alert-banner');
            if (existing) existing.remove();

            const banner = document.createElement('div');
            banner.id = 'severity-alert-banner';
            banner.innerHTML = '🟢 Alert notifications active';
            banner.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(40, 40, 40, 0.85);
                color: #aaaaaa;
                font-size: 12px;
                font-weight: normal;
                padding: 8px 14px;
                border-radius: 6px;
                z-index: 99999;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            `;

            document.body.appendChild(banner);
            setTimeout(() => {
                banner.style.transition = 'opacity 1s ease';
                banner.style.opacity = '0';
                setTimeout(() => banner.remove(), 1000);
            }, 2000);
        })()
        ">
        """
        feedback_update = gr.update(
                value=(
                "<h3>Driving Behaviour Feedback</h3>"
                "<p>Trip started. Monitoring segments...</p>"
                + permission_and_test_script
            )
        )

        # 🔑 SEED LLM PIPELINE FOR FIRST SEGMENT
        holder = {"result": None}
        start_llm_for_segment(0, summaries, holder, severity)
                

        return (
            segments,            # segment_stream_state
            0,                   # segment_pointer_state
            trip_id,             # current_trip_state
            dropdown_update,     # segment_dropdown
            feedback_update,     # output_box
            True,                 # streaming_state (start streaming)
            df,
            summaries,
            0,
            holder
        )

    def stop_streaming():
        return (
            [],                  # segment_stream_state
            0,                   # segment_pointer_state
            None,                # current_trip_state
            gr.update(choices=["Waiting for stream..."], value="Waiting for stream..."),  # segment_dropdown
            gr.update(value="<h3>Driving Behaviour Feedback</h3>"),  # output_box
            False,                # streaming_state (stop streaming)
            None
        )


    def advance_segment_stream(segments, idx, trip_id, streaming, df, summaries, next_llm_idx, next_llm_result):
        if not streaming or not segments:
            return idx, gr.update(), gr.update(), next_llm_idx, next_llm_result

        seg = segments[idx]
        severity = seg["severity"]

        label = f"Segment {idx + 1} — Severity: {severity}"
        dropdown_update = gr.update(choices=[label], value=label)

        feedback_update = gr.update()  # default: no change
        # ✅ DISPLAY precomputed LLM result for CURRENT segment
        

        notification_script = ""
        if severity.lower() in ALERT_SEVERITIES:
            print(f"NOTIFICATION: {severity}")
            notification_script = f"""
            <img src="x" style="display:none" onerror="
                (function() {{
                    // --- Sound (programmatic beep, no file needed) ---
                    try {{
                        const ctx = new (window.AudioContext || window.webkitAudioContext)();
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(880, ctx.currentTime);
                        gain.gain.setValueAtTime(0.5, ctx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1);
                        osc.start(ctx.currentTime);
                        osc.stop(ctx.currentTime + 1);
                    }} catch(e) {{ console.warn('Audio failed:', e); }}

                    // --- Banner ---
                    const existing = document.getElementById('severity-alert-banner');
                    if (existing) existing.remove();

                    const banner = document.createElement('div');
                    banner.id = 'severity-alert-banner';
                    banner.innerHTML = '⚠️ HIGH SEVERITY DETECTED — Segment {idx + 1}: {severity}';
                    banner.style.cssText = `
                        position: fixed;
                        top: 20px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: #ff4444;
                        color: white;
                        font-size: 18px;
                        font-weight: bold;
                        padding: 16px 32px;
                        border-radius: 10px;
                        z-index: 99999;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                        animation: fadeout 4s forwards;
                    `;

                    // Auto-dismiss after 4 seconds
                    document.body.appendChild(banner);
                    setTimeout(() => banner.remove(), 4000);
                }})();
            ">
            """


        if (
            next_llm_idx == idx
            and isinstance(next_llm_result, dict)
            and next_llm_result.get("result") is not None
        ):
            feedback_update = gr.update(
                value=(
                    "<h3>Driving Behaviour Feedback</h3>"
                    f"<p>{next_llm_result['result']}</p>"
                    + notification_script
                )
            )
        # 🔮 start LLM for NEXT segment
        lookahead_idx = idx + 1
        if lookahead_idx < len(segments):
            if next_llm_idx != lookahead_idx:
                holder = {"result": None}
                lookahead_severity = segments[lookahead_idx]["severity"] 
                start_llm_for_segment(lookahead_idx, summaries, holder, lookahead_severity)

                next_llm_idx = lookahead_idx
                next_llm_result = holder   # store HOLDER, not result


        next_idx = min(idx + 1, len(segments) - 1)

        return (
            next_idx,
            dropdown_update,
            feedback_update,
            next_llm_idx,
            next_llm_result
        )
    
    def reset_driver_view():
        return (
            [],                                  # segment_stream_state
            0,                                   # segment_pointer_state
            None,                                # current_trip_state
            gr.update(
                choices=["Waiting for stream..."],
                value="Waiting for stream..."
            ),                                   # segment_dropdown
            gr.update(
                value="<h3>Driving Behaviour Feedback</h3>"
            ),                                   # output_box
            False,                               # streaming_state
            None,                                # trip_df_state
            None,                                # segment_summaries_state
            None,                                # next_llm_idx_state
            None                                 # next_llm_result_state
        )

    start_btn.click(
        fn=start_streaming,
        inputs=[],
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            current_trip_state,
            segment_dropdown,
            output_box,
            streaming_state,
            trip_df_state,
            segment_summaries_state,
            next_llm_idx_state,
            next_llm_result_state
        ],
        show_progress=False
    )
    stop_btn.click(
        fn=stop_streaming,
        inputs=[],
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            current_trip_state,
            segment_dropdown,
            output_box,
            streaming_state,
            trip_df_state
        ],
        show_progress=False
    )
    refresh_state.change(
        fn=reset_driver_view,
        inputs=[],
        outputs=[
            segment_stream_state,
            segment_pointer_state,
            current_trip_state,
            segment_dropdown,
            output_box,
            streaming_state,
            trip_df_state,
            segment_summaries_state,
            next_llm_idx_state,
            next_llm_result_state
        ],
        show_progress=False
    )


    logout_btn = gr.Button("Logout", elem_classes=["logout-btn"])

    STREAM_INTERVAL_SEC = 15.0  # 🔧 adjust freely

    gr.Timer(STREAM_INTERVAL_SEC).tick(
        fn=advance_segment_stream,
        inputs=[
            segment_stream_state,
            segment_pointer_state,
            current_trip_state,
            streaming_state,
            trip_df_state,
            segment_summaries_state,
            next_llm_idx_state,
            next_llm_result_state 
        ],
        outputs=[
            segment_pointer_state,
            segment_dropdown,
            output_box,
            next_llm_idx_state,
            next_llm_result_state
        ],
        show_progress=False
    )

    return refresh_state, logout_btn