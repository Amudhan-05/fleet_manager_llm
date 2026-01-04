import gradio as gr

from ui.login_view import build_login_view
from ui.driver_view import build_driver_view
from ui.coach_view import build_coach_view

from backend.state import global_state
from backend.state.global_state import GLOBAL_STATE
from backend.llm.load_llm import load_llm_once

# ----------------------------
# Global initialization
# ----------------------------
load_llm_once()


def route_after_login(user_id, role):
    print(f">>> ROUTER: user_id={user_id}, role={role}")

    global_state.current_user_id = user_id
    global_state.current_role = role

    print(">>> GLOBAL STATE CHECK")
    print("   user_id:", global_state.current_user_id)
    print("   role:", global_state.current_role)

    if role == "driver":
        # register presence
        GLOBAL_STATE.driver_login(
            driver_id=user_id,
            name=user_id
        )

        return (
            gr.update(visible=False),   # login section
            gr.update(visible=True),    # driver section
            gr.update(visible=False),   # coach section
            gr.update(value=1),         # driver refresh
            gr.update(),                # coach refresh
        )

    if role == "coach":
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(),
            gr.update(value=1),
        )

    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(),
        gr.update(),
    )

def logout():
    print(">>> LOGOUT")

    global_state.current_user_id = None
    global_state.current_role = None

    return (
        None,                    # user_id_state
        None,                    # role_state
        gr.update(visible=True), # login
        gr.update(visible=False),# driver
        gr.update(visible=False) # coach
    )

custom_css = """
html {
    color-scheme: light;
}
:root {
    --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --card-bg: #ffffff;
    --card-border-radius: 14px;
    --text-primary: #1f2937;
    --text-muted: #64748b;
    --accent: #667eea;
    --accent-hover: #5a67d8;
}
body {
    background: var(--bg-gradient);
    color: #1f2937;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
}
.gradio-container {
    max-width: 1200px !important;
    margin: auto;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
}
h1, h2, h3 {
    text-align: center;
    color: var(--text-primary);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.dmk-card {
    background: var(--card-bg);
    padding: 32px;
    border-radius: var(--card-border-radius);
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    margin-top: 20px;
}

/* Label pills */
.dmk-label {
    display: inline-block;
    background: #2563eb;
    color: white;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 999px;
    margin-bottom: 6px;
}

.dmk-card,
.dashboard {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

button,
.button,
.dmk-login-btn {
    margin-top: 18px;
    background: var(--accent) !important;
    color: white !important;
    font-weight: 600;
    border-radius: 10px !important;
    height: 44px;
}

button:hover {
    background: var(--accent-hover) !important;
}

.dmk-viewport {
    min-height: 100vh;
    align-items: center;
}


.dmk-center-vertical {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.dashboard {
    animation: fadeIn 0.5s ease-in-out;
}


.dashboard h2{
    margin-bottom: 12px;
}
.dashboard h3 {
    margin-top: 12px;
    margin-bottom: 6px;
}
/* Output box */
.output {
    background-color: #f8fafc !important;
    color: #1f2937 !important;
    margin-top: 12px;
    padding: 16px;
    border-radius: 8px;
    min-height: 120px;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
}

/* Dropdown spacing */
.gradio-dropdown,
.gradio-textbox {
    margin-bottom: 14px !important;
}

.gradio-dropdown > div,
.gradio-textbox input {
    min-height: 44px;
}

.gradio-dropdown {
    margin-top: 4px !important;
}

.segment-hint {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 8px;
}

* {
    forced-color-adjust: none;
}

input,
textarea,
select {
    background-color: #ffffff !important;
    color: #1f2937 !important;
    border-color: #d1d5db !important;
}
input:focus,
select:focus,
textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25);
}
.logout-btn {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    color: white !important;
    border-radius: 10px;
    margin-top: 20px;
}

.logout-btn:hover {
    box-shadow: 0 6px 18px rgba(239, 68, 68, 0.4);
}


footer {
    display: none !important;
}
"""

def create_app():
    # ------------------------------------------------------------------
    # DMK LAYOUT + CSS (VERBATIM)
    # ------------------------------------------------------------------
    with gr.Blocks(
        css= custom_css
    ) as app:

        # ==========================
        # Header
        # ==========================
        with gr.Row():
            gr.Markdown("# Fleet Management LLM Dashboard")

        # ==========================
        # Main Content
        # ==========================
        with gr.Row(elem_classes=["dmk-viewport"]):
            with gr.Column(scale=1):
                pass

            with gr.Column(scale=6, elem_classes=["container", "dmk-center-vertical"]):

                # --------------------
                # LOGIN SECTION
                # --------------------
                with gr.Column(visible=True) as login_col:
                    user_id_state, role_state = build_login_view()

                # --------------------
                # DRIVER SECTION
                # --------------------
                with gr.Column(visible=False) as driver_col:
                    driver_refresh_state, driver_logout_btn = build_driver_view()

                
                # --------------------
                # COACH SECTION
                # --------------------
                with gr.Column(visible=False) as coach_col:
                    coach_refresh_state, coach_logout_btn = build_coach_view()
                


            with gr.Column(scale=1):
                pass

        # ==========================
        # ROUTING
        # ==========================
        role_state.change(
            fn=route_after_login,
            inputs=[user_id_state, role_state],
            outputs=[
                login_col,
                driver_col,
                coach_col,
                driver_refresh_state,
                coach_refresh_state,
            ]
        )

        driver_logout_btn.click(
            fn=logout,
            inputs=[],
            outputs=[user_id_state, role_state, login_col, driver_col, coach_col]
        )

        coach_logout_btn.click(
            fn=logout,
            inputs=[],
            outputs=[user_id_state, role_state, login_col, driver_col, coach_col]
        )


    return app
