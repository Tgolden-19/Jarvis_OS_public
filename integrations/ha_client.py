# ha_client.py
import httpx
import asyncio
import commands.validators as validators

class HomeAssistantClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def call_service(self, domain: str, service: str, data: dict):
        url = f"{self.base_url}/api/services/{domain}/{service}"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()

    async def get_state(self, entity_id: str):
        url = f"{self.base_url}/api/states/{entity_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def send_notification(self, title: str, message: str, device: str):
        return await self.call_service(
            domain="notify",
            service=device,
            data={"title": title, "message": message}
        )
    
    async def send_to_ha_assist(self, user_text):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/assist_pipeline/run",
                headers=self.headers,
                json={
                    "input": user_text,
                    "start_stage": "intent",
                    "end_stage": "response"
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")