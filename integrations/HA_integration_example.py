import asyncio
from ha_client import HomeAssistantClient

# Existing TTS, LLM, STT pipelines remain untouched
# from my_voice_pipeline import stt_pipeline, llm_pipeline, tts_pipeline

ha = HomeAssistantClient(
    base_url="http://homeassistant.local:8123",  # or your local IP
    token="YOUR_LONG_LIVED_ACCESS_TOKEN"
)

async def handle_home_automation(command: str):
    #below are examples of commands to send to home assistant
    if "turn on living room lights" in command:
        await ha.call_service("light", "turn_on", {"entity_id": "light.living_room"})
    elif "status of garage door" in command:
        state = await ha.get_state("binary_sensor.garage_door")
        print(f"Garage Door is: {state['state']}")
    elif "notify me" in command:
        await ha.send_notification(
            title="Alert from AI",
            message="This is a test message.",
            device="mobile_app_pixel_6"
        )

# Optionally call this within your main command dispatch
async def dispatch_command(command: str):
    # Example: external LLM parsed this as a home automation intent
    if "home" in command or "light" in command:
        await handle_home_automation(command)
    else:
        print("Not a HA command. Passing to other integrations.")
