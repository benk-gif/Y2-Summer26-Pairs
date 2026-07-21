import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()


client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


import requests

def get_user_location_by_ip(ip_address=None):
    """
    Fetches the user's rough geographical location based on their public IP address.
    Uses ip-api.com as a reliable alternative.
    """
    if ip_address:
        url = f"http://ip-api.com/json/{ip_address}"
    else:
        url = "http://ip-api.com/json/"
        
    try:
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "fail":
            print(f"API Error: {data.get('message')}")
            return None
            
        return {
            "ip": data.get("query"),
            "city": data.get("city"),
            "region": data.get("regionName"), # maps to full region name
            "country": data.get("country"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon")
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location data: {e}")
        return None

def find_concerts_by_location(city, radius="100"):
    api_key = os.getenv('TICKETMASTER_API_KEY')
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    
    current_utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    params = {
        "city": city,
        "radius": radius,
        "unit": "miles",
        "countryCode": "US", 
        "classificationName": "music",
        "startDateTime": current_utc_time, 
        "apikey": api_key
    }
    
    
    try:
       
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        events = data.get("_embedded", {}).get("events", [])
        
        if not events:
            return {"message": f"No upcoming concerts found in {city} within a {radius} mile radius."}
            
        formatted_events = []
        for event in events:
            price_ranges = event.get("priceRanges", [{}])
            if isinstance(price_ranges, list) and len(price_ranges) > 0:
                min_price = price_ranges[0].get("min", "N/A")
                max_price = price_ranges[0].get("max", "N/A")
                currency = price_ranges[0].get("currency", "USD")
            else:
                min_price, max_price, currency = "N/A", "N/A", "USD"
            
            venues = event.get("_embedded", {}).get("venues", [{}])
            venue_name = venues[0].get("name", "Unknown Venue") if venues else "Unknown Venue"
            venue_address = venues[0].get("address", {}).get("line1", "No Address") if venues else "No Address"
            
            formatted_events.append({
                "concert_name": event.get("name"),
                "date": event.get("dates", {}).get("start", {}).get("localDate"),
                "time": event.get("dates", {}).get("start", {}).get("localTime"),
                "venue_name": venue_name,
                "venue_address": venue_address,
                "ticket_price": f"{min_price} - {max_price} {currency}",
                "purchase_url": event.get("url")
            })
        return formatted_events
    except Exception as e:
        return {"error": f"Failed to connect to ticket database: {str(e)}"}
    



location_tool = {
    "name": "get_user_location_by_ip",
    "description": "Fetches the user's approximate geographic location (city, region, country, lat/long) based on their current IP address.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ip_address": {
                "type": "string",
                "description": "Optional IP address to look up. If omitted, the tool will look up the caller's current IP."
            }
        }
    }
}

concert_tool = {
    "name": "find_concerts_by_location",
    "description": "Searches for upcoming live music concerts and music festivals within a specific geographic city or region.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name to search within, e.g., 'Haifa'."
            },
            "radius": {
                "type": "string",
                "description": "Radius distance for search range. Defaults to '100'"
            }
        },
        "required": ["city"]
    }
}

all_tools = [location_tool, concert_tool]



def run_chat(history):
    print("\n🎵 June (Concert Agent) is active!")
    print("Type 'ben' to switch to Ben, 'switch' for menu, or 'exit' to quit.\n")

    system_message = """
You are June, a concert information assistant. Your job is to help users find and learn about upcoming concerts and events.

Rules:
- Always provide accurate and up to date information about concerts and events.
- Always ask the user for their location if they haven't provided it yet.
- Never make up concert information. If you don't know, say so.

Response format:
- Respond in a clear, friendly manner.
- End with one natural follow-up question.
"""

    while True:
        user_input = input("\nYou: ").strip()

        # Switch / Exit command checks
        if user_input.lower() in ["ben", "switch to ben"]:
            return "ben"
        elif user_input.lower() in ["switch", "change", "menu"]:
            return "switch"
        elif user_input.lower() in ["exit", "quit"]:
            return "exit"

        history.append({"role": "user", "content": user_input})

        
        while True:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=3000,
                temperature=0.7,
                system=system_message,
                tools=all_tools,
                messages=history,
            )

            if response.stop_reason != "tool_use":
                break

            
            history.append({"role": "assistant", "content": response.content})

            tool_results_content = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_use_id = content_block.id
                    tool_input = content_block.input

                    if tool_name == "get_user_location_by_ip":
                        print("[System: June is checking your location...]")
                        tool_result = get_user_location_by_ip(
                            ip_address=tool_input.get("ip_address")
                        )

                    elif tool_name == "find_concerts_by_location":
                        print("[System: June is checking concert tickets...]")
                        tool_result = find_concerts_by_location(
                            city=tool_input.get("city"),
                            radius=tool_input.get("radius", "100"),
                        )

                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": str(tool_result),
                    })

            
            history.append({
                "role": "user",
                "content": tool_results_content,
            })

        
        reply = ""
        for block in response.content:
            if block.type == "text":
                reply += block.text

        print(f"\nJune: {reply}")
        
        history.append({"role": "assistant", "content": reply})
    system_message = """
    You are June, a concert information assistant.

    Your job is to help users find and learn about upcoming concerts and events.


    Rules:
    - Always provide accurate and up to date information about concerts and events.
    - Always ask the user for their location if they haven't provided it yet.
    - Never make up concert information. If you don't know, say so.

    Response format:
    - respond in a clear manner 
    - Then give your response.
    - End with one follow-up question.
    """
    history = []

    while True:
        user_input = input('>> ')

        if user_input.lower() == 'exit':
            break

        history.append({'role': 'user', 'content': user_input})

        while True:
            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1500,
                temperature=0.7,
                system=system_message,
                tools=all_tools,
                messages=history
            )

            if response.stop_reason != "tool_use":
                break

            history.append({"role": "assistant", "content": response.content})

            
            tool_results_content = []
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_use_id = content_block.id
                    tool_input = content_block.input

                    if tool_name == "get_user_location_by_ip":
                        print("[System: Claude is checking your location...]")
                        tool_result = get_user_location_by_ip(ip_address=tool_input.get("ip_address"))
                        print(f"[Debug Payload Received]: {tool_result}")
                        
                    elif tool_name == "find_concerts_by_location":
                        print("[System: Claude is checking local concert tickets...]")
                        tool_result = find_concerts_by_location(
                            city=tool_input.get("city"),
                            radius=tool_input.get("radius", "100")
                        )
                        print(f"[Debug Payload Received]: {tool_result}")
                    
                    
                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": str(tool_result)
                    })

        
            history.append({
                "role": "user",
                "content": tool_results_content
            })

        
        reply = ""
        for block in response.content:
            if block.type == "text":
                reply += block.text
                
        print(f'Claude: {reply}')
        history.append({'role': 'assistant', 'content': reply})

if __name__ == "__main__":
    run_chat()
