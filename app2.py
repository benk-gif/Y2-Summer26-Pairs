
import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_coordinates(place):
   
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        
        "X-Goog-FieldMask": "places.formattedAddress,places.location"
    }
    payload = {"textQuery": place}

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if not data or "places" not in data or len(data["places"]) == 0:
            return None
            
        place_data = data["places"][0]
        return {
            "address": place_data["formattedAddress"],
            "lat": place_data["location"]["latitude"],
            "lng": place_data["location"]["longitude"]
        }
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def get_route(start, destination):
  
    start_coords = get_coordinates(start)
    dest_coords = get_coordinates(destination)

    if not start_coords or not dest_coords:
        return None

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        # Ask for duration, distance, and localized step-by-step text descriptions
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.localizedValues,routes.legs.steps.navigationInstruction"
    }
    
    payload = {
        "origin": {
            "location": {
                "latLng": {"latitude": start_coords["lat"], "longitude": start_coords["lng"]}
            }
        },
        "destination": {
            "location": {
                "latLng": {"latitude": dest_coords["lat"], "longitude": dest_coords["lng"]}
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "languageCode": "en-US"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if not data or "routes" not in data or len(data["routes"]) == 0:
            return None

        route = data["routes"][0]
        leg = route["legs"][0]

        
        steps = []
        for step in leg.get("steps", []):
            nav = step.get("navigationInstruction")
            if nav and "instructions" in nav:
                steps.append(nav["instructions"])

        return {
            "distance": leg["localizedValues"]["distance"]["text"],
            "time": leg["localizedValues"]["duration"]["text"],
            "start": start_coords["address"],
            "end": dest_coords["address"],
            "steps": steps
        }
    except Exception as e:
        print(f"Routing error: {e}")
        return None

def run_chat(history):
    print("\n🚗 Ben (Routes Agent) is active!")
    print("Type 'june' to switch to June, 'switch' for menu, or 'exit' to quit.\n")

    system_message = """
You are Ben, a highly capable, articulate GPS navigation expert and route coordinator. Your job is to translate raw, structured route data into natural, confidence-inspiring driving instructions.

Follow these strict operational constraints:
1. FACTUAL ANCHORING: Base your response *entirely* on the provided [SYSTEM NOTICE] data. Do not invent highway names, estimated times, distances, or landmarks. If data is missing or incomplete, state what you have without making up the rest.
2. STRUCTURE: Start with a brief, warm 1-2 sentence overview summarizing the journey (e.g., total distance and approximate drive time under current traffic conditions).
3. DIRECTIONS: Present the step-by-step navigation instructions as a clean, numbered list. Strip out any residual raw HTML fragments if you see them. Keep each instruction concise and punchy.
4. TONE: Professional, reassuring, and highly clear—like an elite concierge mapping out a trip for a traveler. Avoid dry, robotic code readouts; make it feel like a polished human assistant speaking.
"""

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["june", "switch to june"]:
            return "june"
        elif user_input.lower() in ["switch", "change", "menu"]:
            return "switch"
        elif user_input.lower() in ["exit", "quit"]:
            return "exit"

        history.append({"role": "user", "content": user_input})

        if " to " in user_input.lower():
            parts = user_input.lower().split(" to ")
            start = parts[0].replace("route me from ", "")
            destination = parts[1]

            print("\nFinding route using Google Routes API...")
            route = get_route(start, destination)

            if route:
                directions_text = "\n".join(route["steps"])
                route_text = f"""
[SYSTEM NOTICE: The following real-time data has been fetched for the user's request]
Starting point: {route['start']}
Destination: {route['end']}
Distance: {route['distance']}
Estimated time: {route['time']}

Directions data:
{directions_text}
"""
            else:
                route_text = "[SYSTEM NOTICE: Google Routes API was unable to find a valid driving route between these locations.]"

            history.append({"role": "user", "content": route_text})

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            system=system_message,
            messages=history,
        )

        reply = response.content[0].text
        print(f"\nBen: {reply}")

        history.append({"role": "assistant", "content": reply})
    

    system_message = """
You are Ben, a highly capable, articulate GPS navigation expert and route coordinator. Your job is to translate raw, structured route data into natural, confidence-inspiring driving instructions.

Follow these strict operational constraints:
1. FACTUAL ANCHORING: Base your response *entirely* on the provided [SYSTEM NOTICE] data. Do not invent highway names, estimated times, distances, or landmarks. If data is missing or incomplete, state what you have without making up the rest.
What's your current location or where will you be traveling from?2. STRUCTURE: Start with a brief, warm 1-2 sentence overview summarizing the journey (e.g., total distance and approximate drive time under current traffic conditions).
3. DIRECTIONS: Present the step-by-step navigation instructions as a clean, numbered list. Strip out any residual raw HTML fragments if you see them. Keep each instruction concise and punchy.
4. TONE: Professional, reassuring, and highly clear—like an elite concierge mapping out a trip for a traveler. Avoid dry, robotic code readouts; make it feel like a polished human assistant speaking.
"""

    history = []

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            break

        history.append({
            "role": "user",
            "content": user_input
        })

        if " to " in user_input.lower():
            parts = user_input.lower().split(" to ")
            start = parts[0].replace("route me from ", "")
            destination = parts[1]

            print("\nFinding route using modern API endpoints...")
            route = get_route(start, destination)

            if route:
                directions_text = "\n".join(route['steps'])
                route_text = f"""
[SYSTEM NOTICE: The following real-time data has been fetched for the user's request]
Starting point: {route['start']}
Destination: {route['end']}
Distance: {route['distance']}
Estimated time: {route['time']}

Directions data:
{directions_text}
"""
            else:
                route_text = "[SYSTEM NOTICE: Google Routes API was unable to find a valid driving route between these locations.]"

            history.append({
                "role": "user",
                "content": route_text
            })

        else:
            history.append({
                "role": "user",
                "content": "[SYSTEM NOTICE: User syntax was malformed. Inform them to use: 'Route me from [X] to [Y]']"
            })

        response = client.messages.create(
            model="claude-4-5-20251001",
            max_tokens=1500,
            system=system_message,
            messages=history
        )

        reply = response.content[0].text

        print("\nClaude:")
        print(reply)

        history.append({
            "role": "assistant",
            "content": reply
        })


if __name__ == "__main__":
    run_chat()
