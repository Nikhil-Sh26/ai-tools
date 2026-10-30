"""VideoSDK AI telephony agent.

This worker handles BOTH call directions:

- Inbound  : a caller dials your VideoSDK/Twilio number, the routing rule
             dispatches this agent into the room, the agent answers.
- Outbound : outbound_call.py dials a number through the SIP API, the callee is
             bridged into a room and this same agent joins it.

Run with:  python main.py
"""

import logging
import os
import traceback

from dotenv import load_dotenv
from videosdk.agents import (
    Agent,
    AgentSession,
    JobContext,
    Options,
    Pipeline,
    RoomOptions,
    WorkerJob,
)
from videosdk.plugins.google import GeminiLiveConfig, GeminiRealtime

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class PhoneAgent(Agent):
    """Answers inbound calls and speaks on outbound calls."""

    def __init__(self):
        super().__init__(
            instructions=(
                "You are a helpful AI assistant that talks to people on the phone. "
                "Keep your answers short, natural and friendly. "
                "If you did not understand something, politely ask the caller to repeat it. "
                "If the caller wants to end the call, say goodbye and stop talking."
            ),
        )

    async def on_enter(self) -> None:
        greeting = os.getenv(
            "INITIAL_GREETING",
            "Hello! You're speaking with an AI assistant. How can I help you today?",
        )
        await self.session.say(greeting)

    async def on_exit(self) -> None:
        await self.session.say("Goodbye, and thanks for calling!")


async def start_session(context: JobContext):
    model = GeminiRealtime(
        model=os.getenv("REALTIME_MODEL", "gemini-3.1-flash-live-preview"),
        # GOOGLE_API_KEY is picked up automatically from the environment.
        config=GeminiLiveConfig(
            voice=os.getenv("VOICE", "Leda"),
            response_modalities=["AUDIO"],
        ),
    )
    pipeline = Pipeline(llm=model)
    session = AgentSession(agent=PhoneAgent(), pipeline=pipeline)

    # wait_for_participant=True keeps the agent idle until a phone leg joins the room.
    await session.start(wait_for_participant=True, run_until_shutdown=True)


def make_context() -> JobContext:
    return JobContext(room_options=RoomOptions(name="VideoSDK Telephony Agent"))


if __name__ == "__main__":
    try:
        options = Options(
            # CRITICAL: must match the Agent ID configured in the routing rule.
            agent_id=os.getenv("AGENT_ID", "MyTelephonyAgent"),
            # REQUIRED: registers the worker so telephony calls can be dispatched to it.
            register=True,
            max_processes=int(os.getenv("MAX_PROCESSES", "10")),
            host="localhost",
            port=int(os.getenv("AGENT_PORT", "8081")),
        )
        job = WorkerJob(entrypoint=start_session, jobctx=make_context, options=options)
        job.start()
    except Exception:
        traceback.print_exc()
