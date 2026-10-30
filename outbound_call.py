"""Place an outbound phone call through VideoSDK's SIP API.

The dialed number is bridged into a room; the agent in main.py joins that room
and talks to the person who picks up.

Usage:
    python outbound_call.py +14155550123
    python outbound_call.py +14155550123 gw_123456789
    python outbound_call.py +14155550123 gw_123456789 room_123456789
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SIP_CALL_URL = "https://api.videosdk.live/v2/sip/call"


def make_call(to_number: str, gateway_id: str = None, room_id: str = None) -> dict:
    """Dial `to_number` (E.164) using the given outbound SIP gateway."""
    token = os.getenv("VIDEOSDK_AUTH_TOKEN")
    gateway_id = gateway_id or os.getenv("OUTBOUND_GATEWAY_ID")

    if not token:
        raise SystemExit("VIDEOSDK_AUTH_TOKEN is missing. Add it to your .env file.")
    if not gateway_id:
        raise SystemExit(
            "gatewayId is required. Set OUTBOUND_GATEWAY_ID in .env "
            "or pass it as the second argument."
        )

    payload = {"gatewayId": gateway_id, "sipCallTo": to_number}
    if room_id:
        payload["destinationRoomId"] = room_id

    response = requests.post(
        SIP_CALL_URL,
        headers={"Authorization": token, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python outbound_call.py <phone_number_in_E164> [gateway_id] [room_id]"
        )

    result = make_call(
        to_number=sys.argv[1],
        gateway_id=sys.argv[2] if len(sys.argv) > 2 else None,
        room_id=sys.argv[3] if len(sys.argv) > 3 else None,
    )
    print(result)
