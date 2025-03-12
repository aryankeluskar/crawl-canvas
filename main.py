import http
import time
import dotenv
import os
import json
import requests
import base64

dotenv.load_dotenv()

def get_courses():
    # canvas.asu.edu/api/v1/users/911835/courses
    url = "https://canvas.asu.edu/api/v1/courses?page=1&per_page=100"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    courses = requests.get(url, headers=headers)
    courses = courses.json()

    out = {}

    for course in courses:
        if "id" in course and "name" in course:
            out.update({
                course["name"]: course["id"]
            })

    with open("courses.json", "w") as f:
        json.dump(out, f)

    return out

def get_modules(course_id):
    url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/modules"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    modules = requests.get(url, headers=headers)

    modules = modules.json()

    with open("modules.json", "w") as f:
        json.dump(modules, f)

    return modules

def get_zoom_access_token():
    """Get an access token from Zoom using client credentials."""
    client_id = os.getenv('ZOOM_CLIENT_ID', 'ENsZO04URgG3J_lxKmbCdg')
    client_secret = os.getenv('ZOOM_CLIENT_SECRET', 'ypqwCkK0PtWTKd6RWPE9rR5T4CpoAmz4')
    account_id = os.getenv('ZOOM_ACCOUNT_ID', 'Tn6CeQOaS2-3bXa1_slyKw')
    
    # Create the authorization string (base64 encoded client_id:client_secret)
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    # Set up the request to get an access token
    token_url = "https://zoom.us/oauth/token"
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Include necessary scopes
    data = {
        "grant_type": "account_credentials",
        "account_id": account_id,
        "scope": "meeting:write meeting:read recording:write"
    }
    
    # Print debug information
    print("Requesting access token from Zoom...")
    
    response = requests.post(token_url, headers=headers, data=data)
    print(f"Token response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error getting access token: {response.text}")
        return None
        
    token_data = response.json()
    print("Successfully obtained access token!")
    
    return token_data.get("access_token")

def start_meeting():
    try:
        import requests
        
        # Get a valid access token first
        access_token = get_zoom_access_token()
        
        if not access_token:
            print("Failed to get access token. Cannot create meeting.")
            return
        
        # User ID (either your email or user ID)
        zoom_user_id = os.getenv('ZOOM_USER_ID', 'me')  # Using 'me' is safer than an email
        
        url = f"https://api.zoom.us/v2/users/{zoom_user_id}/meetings"

        # Create meeting with all the settings we want to apply
        # Note: Some settings might not apply due to account permissions
        body = {
            "topic": "Study Meeting",
            "agenda": "Study Meeting",
            "type": 1,  # 1 = instant meeting
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,  # Allow participants to join before host
                "mute_upon_entry": False,
                "approval_type": 0,
                "password": "123456",
                "auto_recording": "cloud",  # Automatically start cloud recording
                "waiting_room": False  # Disable waiting room
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        print(f"Creating meeting for user: {zoom_user_id}")
        
        response = requests.post(url, headers=headers, json=body)
        print(f"Meeting creation response status: {response.status_code}")
        
        if response.status_code == 201:
            meeting_data = response.json()
            
            print("\n🎉 Meeting created successfully!")
            print(f"Join URL: {meeting_data['join_url']}")
            print(f"Password: {meeting_data.get('password', 'N/A')}")
            
            # Check if settings were applied
            settings = meeting_data.get('settings', {})
            join_before_host_enabled = settings.get('join_before_host', False)
            auto_recording_enabled = settings.get('auto_recording') == 'cloud'
            
            # Provide instructions based on settings status
            print("\n⚠️ IMPORTANT: Check your Zoom meeting settings! ⚠️")
            
            if not join_before_host_enabled:
                print("\n✅ To allow participants to join without the host:")
                print("1. Log into your Zoom account at zoom.us")
                print("2. Go to Settings > Meeting > In Meeting (Basic)")
                print("3. Enable 'Allow participants to join before host'")
            
            if not auto_recording_enabled:
                print("\n✅ To enable automatic cloud recording:")
                print("1. Log into your Zoom account at zoom.us") 
                print("2. Go to Settings > Recording")
                print("3. Enable 'Automatic recording' and select 'Cloud'")
            
            print("\nNote: These settings may require a Business, Education, or Enterprise plan.")
        else:
            print(f"Failed to create meeting: {response.status_code}")
            print(response.text if hasattr(response, 'text') else "No response text")
        
        return os.getenv('ZOOM_LINK')

    except Exception as e:
        print(f"Error: {e}")

    return os.getenv('ZOOM_LINK')

def not_main():
    link = start_meeting()
    print(link)

    courses = get_courses()

    course_name = input("Enter the course name as SUB 101: ")

    for canvas_name, canvas_id in courses.items():
        if course_name in canvas_name:
            course_id = canvas_id
            break

    if course_id is None:
        print("Course not found")
        exit()

    # get modules for the first course
    modules = get_modules(course_id)


if __name__ == "__main__":

    workstation_init = requests.post(
        "https://api.agentstation.ai/v1/workstations",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('AGENT_API')}"
        },
        json={}
    )

    print(workstation_init.json())

    time.sleep(10)
    
    workstation_id = workstation_init.json()["id"]

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
        "invite_url": os.getenv("ZOOM_LINK"),
        "name": "Professor Agent"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/meeting/join", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    time.sleep(3)

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
        "event": "press",
        "text": "F11"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/browser/keyboard", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
    "operator": "midscene",
    "prompt": "1. click on chat in the bottom menu\n2. click on type message here on the chat"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/browser/operator/act", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    time.sleep(5)

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
        "text": "https://excalidraw.com/#room=6f2000970bbfebe7e351,Hqb87BontKyWvsZkQA6RjA"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/keyboard", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    time.sleep(5)

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
    "event": "press",
    "text": "Enter"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/browser/keyboard", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    exit()

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = ''
    headers = {
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/meeting/unmute", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
    "url": "https://excalidraw.com/#room=6f2000970bbfebe7e351,Hqb87BontKyWvsZkQA6RjA"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/meeting/screenshare/start", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    # navigate to https://white-background.vercel.app

    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
        "url": "https://excalidraw.com/#room=6f2000970bbfebe7e351,Hqb87BontKyWvsZkQA6RjA"
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/browser/navigate", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


    conn = http.client.HTTPSConnection("api.agentstation.ai")
    payload = json.dumps({
        "text": "Hello, how are you?",
        "language_code": "en-US"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("AGENT_API")}'
    }
    conn.request("POST", f"/v1/workstations/{workstation_id}/audio/speak", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

    # time.sleep(30)

    # workstation_delete = requests.delete(
    #     f"https://api.agentstation.ai/v1/workstations/{workstation_id}",
    #     headers={
    #         "Authorization": f"Bearer {os.getenv('AGENT_API')}"
    #     }
    # )

    # print(workstation_delete.status_code)