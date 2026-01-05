import gradio as gr
from backend.auth.auth_service import authenticate


def build_login_view():
    # Outer container = DMK card
    with gr.Column(
        scale=1,
        min_width=420
    ):
        # Card background
        with gr.Column(
            elem_classes=["dmk-card"]
        ):

            gr.Markdown("## Login")

            # --------------------
            # Username
            # --------------------
            # gr.HTML("<span class='dmk-label'>Username</span>",unsafe_allow_html=True)
            username_box = gr.Textbox(
                label="Username",
                placeholder="Enter username"
                
            )

            # --------------------
            # Password
            # --------------------
            # gr.HTML("<span class='dmk-label'>Username</span>")
            password_box = gr.Textbox(
                type="password",
                placeholder="Enter password",
                label="Password"
            )

            # --------------------
            # Login button
            # --------------------
            login_btn = gr.Button(
                "Login",
                elem_classes=["dmk-login-btn"]
            )

            error_box = gr.Markdown("", visible=False)

            # Hidden states (unchanged)
            user_id_state = gr.State(None)
            role_state = gr.State(None)

            # ------------------------
            # Callback (UNCHANGED)
            # ------------------------
            def do_login(username, password):
                print(f">>> UI: login attempt for user={username}")

                user = authenticate(username, password)

                if user is None:
                    print(">>> UI: login failed")
                    return (
                        None,
                        None,
                        gr.update(
                            value="❌ Invalid username or password",
                            visible=True
                        )
                    )

                success, role = user
                if not success:
                    print(">>> UI: login failed (success=False)")
                    return (
                        None,
                        None,
                        gr.update(
                            value="❌ Authentication failed",
                            visible=True
                        )
                    )
                
                user_id = username
                print(f">>> UI: login success user_id={user_id} role={role}")

                return (
                    user_id,
                    role,
                    gr.update(visible=False)
                )

            login_btn.click(
                fn=do_login,
                inputs=[username_box, password_box],
                outputs=[user_id_state, role_state, error_box]
            )

            return user_id_state, role_state
