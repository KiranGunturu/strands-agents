import logging
import os

import streamlit as st
from strands import Agent
from strands.models import BedrockModel
from strands.vended_tools import http_request, web_fetch
from strands_tools import use_aws

logging.basicConfig(level=logging.INFO)

DEFAULT_REGION = "us-west-2"
DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-4-6"

SAMPLE_QUESTIONS = [
    "List all S3 buckets in my AWS account and show their regions.",
    "Which EC2 instances are running in my account? Group them by region.",
    "Show me the current weather in Seattle and explain whether it could affect operations.",
    "What AWS resources should I review before deleting an unused VPC?",
    "Give me a concise checklist for investigating high Lambda errors.",
]

SIDEBAR_ACTIONS = {
    "Inventory overview": "Give me a read-only overview of my AWS account: regions in use, running EC2 instances, S3 buckets, and RDS databases.",
    "Investigate an incident": "Help me investigate a production incident. Start by checking recent CloudWatch alarms and unhealthy resources, then summarize evidence and likely causes.",
    "Review cost risks": "Review my AWS account for common cost risks using read-only checks. Focus on idle resources, unattached volumes, old snapshots, and unusually large services.",
    "Security posture": "Give me a read-only AWS security review covering public S3 buckets, overly permissive security groups, IAM access keys, and CloudTrail status.",
}

CLOUDOPS_SYSTEM_PROMPT = """
You are CloudOps Assistant, a careful AWS operations copilot.

Your responsibilities:
- Help users inspect and understand AWS infrastructure, costs, availability, and operational issues.
- Use the use_aws tool for AWS account questions and the http_request or web_fetch tools for public HTTP information.
- For weather requests, use Open-Meteo at api.open-meteo.com because it does not require an API key. Never use OpenWeatherMap.
- Prefer read-only inspection and explain what you found in plain language.
- Before any destructive or state-changing action, clearly describe the action, scope, and risk, and ask for confirmation.
- Never invent AWS resource IDs, metrics, regions, costs, or weather data. State when information cannot be verified.
- Mention the AWS region and relevant time window when they affect the answer.
- For incidents, organize the response as: summary, evidence, likely causes, recommended next steps, and commands or console paths when useful.
- Keep answers concise, practical, and easy to scan. Use Markdown tables or bullets when they improve clarity.
"""


def get_runtime_config() -> tuple[str, str]:
    """Return configured Bedrock values, falling back when variables are blank."""
    region = os.getenv("AWS_REGION", "").strip() or os.getenv("AWS_DEFAULT_REGION", "").strip() or DEFAULT_REGION
    model_id = os.getenv("BEDROCK_MODEL_ID", "").strip() or DEFAULT_MODEL_ID
    return region, model_id


def build_agent() -> Agent:
    """Create the CloudOps agent from the current AWS/Bedrock environment."""
    region, model_id = get_runtime_config()

    model = BedrockModel(model_id=model_id, region_name=region)
    return Agent(
        name="CloudOps Assistant",
        model=model,
        system_prompt=CLOUDOPS_SYSTEM_PROMPT,
        tools=[use_aws, http_request, web_fetch],
    )


@st.cache_resource(show_spinner=False)
def get_agent() -> Agent:
    return build_agent()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### CloudOps Assistant")
        st.caption("Your operational command center for AWS.")
        st.divider()

        st.markdown("**Common workflows**")
        st.caption("Choose a starting point, then refine the request in chat.")
        for label, prompt in SIDEBAR_ACTIONS.items():
            if st.button(label, key=f"sidebar_{label}", use_container_width=True):
                st.session_state.pending_prompt = prompt
                st.rerun()

        st.divider()
        st.markdown("**Environment**")
        region, model_id = get_runtime_config()
        st.markdown(
            f"""
            <div class="env-card">
                <div class="env-label">BEDROCK REGION</div>
                <div class="env-value">{region or "Not configured"}</div>
                <div class="env-label">MODEL</div>
                <div class="env-value env-model">{model_id or "Default model"}</div>
                <div class="env-note">Credentials: AWS SDK default chain</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button("Clear conversation", key="clear_conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="CloudOps Assistant",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root { --ink: #17212b; --muted: #5d6b78; --accent: #0f766e; --line: #d7e1e5; }
        .stApp { background: linear-gradient(135deg, #f7fbfa 0%, #eef4f6 52%, #f8f4ec 100%); }
        [data-testid="stSidebar"] { background: #17212b; }
        [data-testid="stSidebar"] * { color: #edf5f4 !important; }
        [data-testid="stSidebar"] button[kind="secondary"],
        [data-testid="stSidebar"] button[kind="secondary"] p,
        [data-testid="stSidebar"] button[kind="secondary"] span { color: #17212b !important; }
        [data-testid="stSidebar"] button[kind="secondary"] { background: #d5e7e4 !important; border: 1px solid #8fc1b9 !important; }
        [data-testid="stSidebar"] button[kind="secondary"]:hover { background: #ffffff !important; border-color: #ffffff !important; }
        [data-testid="stSidebar"] button[kind="secondary"]:focus { box-shadow: 0 0 0 2px #72c7bb !important; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #b9cbd0 !important; }
        [data-testid="stSidebar"] .env-card { background: #243642; border: 1px solid #46616b; border-radius: 8px; padding: .8rem; }
        [data-testid="stSidebar"] .env-label { color: #9fc6c4 !important; font-size: .68rem; font-weight: 700; letter-spacing: .08em; margin-top: .35rem; }
        [data-testid="stSidebar"] .env-value { color: #ffffff !important; font-family: monospace; font-size: .9rem; font-weight: 700; overflow-wrap: anywhere; }
        [data-testid="stSidebar"] .env-model { font-size: .78rem; }
        [data-testid="stSidebar"] .env-note { color: #c4d4d7 !important; font-size: .72rem; margin-top: .65rem; }
        .hero { padding: 2.5rem 0 1rem; }
        .hero h1 { color: var(--ink); font-size: 2.8rem; letter-spacing: 0; margin-bottom: .35rem; }
        .hero p { color: var(--muted); font-size: 1.05rem; max-width: 720px; }
        .status { color: var(--accent); font-size: .82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
        div[data-testid="stChatMessage"] { border: 1px solid var(--line); border-radius: 8px; background: rgba(255,255,255,.72); }
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_sidebar()

    st.markdown('<div class="hero"><div class="status">Operations workspace</div><h1>CloudOps Assistant</h1><p>Ask about AWS resources, incidents, and operational checks. The assistant gathers account evidence before making recommendations.</p></div>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.subheader("Start with a question")
        columns = st.columns(2)
        for index, question in enumerate(SAMPLE_QUESTIONS):
            with columns[index % 2]:
                if st.button(question, key=f"sample_{index}", use_container_width=True):
                    st.session_state.pending_prompt = question
                    st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about your AWS environment...")
    prompt = prompt or st.session_state.pop("pending_prompt", None)

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Reviewing your environment..."):
                try:
                    response = get_agent()(prompt)
                    answer = str(response)
                except Exception as error:
                    logging.exception("CloudOps request failed")
                    answer = (
                        "I could not complete that request. Check your AWS credentials, "
                        "Bedrock model access, region, and IAM permissions.\n\n"
                        f"`{type(error).__name__}: {error}`"
                    )
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
