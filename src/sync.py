import os
import json
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

def load_config():
    """Load configuration from environment variables or config.json"""
    if all(key in os.environ for key in ['WEBUNTIS_SERVER', 'WEBUNTIS_SCHOOL', 'WEBUNTIS_USERNAME', 'WEBUNTIS_PASSWORD']):
        return {
            'server': os.environ['WEBUNTIS_SERVER'],
            'school': os.environ['WEBUNTIS_SCHOOL'],
            'username': os.environ['WEBUNTIS_USERNAME'],
            'password': os.environ['WEBUNTIS_PASSWORD'],
            'class_id': os.environ.get('WEBUNTIS_CLASS_ID')  # Optional
        }
    
    with open('config.json', 'r') as f:
        return json.load(f)

def webuntis_login(config):
    """Authenticate against WebUntis and return session + sessionId"""
    session = requests.Session()
    
    # Login endpoint
    login_url = f"https://{config['server']}/WebUntis/jsonrpc.do?school={config['school']}"
    
    login_data = {
        "id": "WebUntisSync",
        "method": "authenticate",
        "params": {
            "user": config['username'],
            "password": config['password'],
            "client": "WebUntisSync"
        },
        "jsonrpc": "2.0"
    }
    
    response = session.post(login_url, json=login_data)
    response.raise_for_status()
    
    result = response.json()
    if 'error' in result:
        raise Exception(f"Login failed: {result['error']}")
    
    return session, result['result']['sessionId']

def get_element_id(session, config, session_id):
    """Get element ID (class or student). Use configured class_id if provided."""
    # If class_id is provided, use it directly
    if config.get('class_id'):
        class_id = int(config['class_id'])
        print(f"📚 Using configured class ID: {class_id}")
        return class_id, 1  # Type 1 = class
    
    url = f"https://{config['server']}/WebUntis/jsonrpc.do?school={config['school']}"
    headers = {"Cookie": f"JSESSIONID={session_id}"}
    
    # Try fetching classes first
    data = {
        "id": "WebUntisSync",
        "method": "getClasses",
        "params": {},
        "jsonrpc": "2.0"
    }
    
    response = session.post(url, json=data, headers=headers)
    result = response.json()
    
    # If there are classes, take the first (or search by name)
    if 'result' in result and len(result['result']) > 0:
        classes = result['result']
        
        # Log available classes
        print("📋 Available classes:")
        for cl in classes[:5]:  # Show first 5
            print(f"   - {cl.get('name')} (ID: {cl['id']})")
        
        # Search for Class1 or similar
        for cl in classes:
            if '1IT3' in cl.get('name', '').upper() or '1IT3A' in cl.get('name', '').upper():
                print(f"📚 Found class: {cl['name']} (ID: {cl['id']})")
                return cl['id'], 1  # Type 1 = class
        
        # If specific class not found, take first
        print(f"📚 Using class: {classes[0]['name']} (ID: {classes[0]['id']})")
        return classes[0]['id'], 1
    
    # Otherwise try student
    data = {
        "id": "WebUntisSync", 
        "method": "getStudents",
        "params": {},
        "jsonrpc": "2.0"
    }
    
    response = session.post(url, json=data, headers=headers)
    result = response.json()
    
    if 'result' in result and len(result['result']) > 0:
        student = result['result'][0]
        print(f"👤 Found student: {student.get('name', 'Unknown')} (ID: {student['id']})")
        print(f"👤 Found student: {student.get('name', 'Unknown')} (ID: {student['id']})")
        return student['id'], 5  # Type 5 = student
    
    raise Exception("Could not retrieve class or student ID")

def get_timetable(session, config, session_id, element_id, element_type, start_date, end_date):
    """Fetch timetable"""
    url = f"https://{config['server']}/WebUntis/jsonrpc.do?school={config['school']}"
    
    data = {
        "id": "WebUntisSync",
        "method": "getTimetable",
        "params": {
            "options": {
                "element": {
                    "id": element_id,
                    "type": element_type  # 1 = class, 5 = student
                    "type": element_type  # 1 = class, 5 = student
                },
                "startDate": start_date.strftime("%Y%m%d"),
                "endDate": end_date.strftime("%Y%m%d"),
                "showBooking": True,
                "showInfo": True,
                "showSubstText": True,
                "showLsText": True,
                "showStudentgroup": True,
                "classFields": ["id", "name", "longname"],
                "roomFields": ["id", "name", "longname"],
                "subjectFields": ["id", "name", "longname"],
                "teacherFields": ["id", "name", "longname"]
            }
        },
        "jsonrpc": "2.0"
    }
    
    headers = {"Cookie": f"JSESSIONID={session_id}"}
    response = session.post(url, json=data, headers=headers)
    result = response.json()
    
    if 'error' in result:
        raise Exception(f"Timetable fetch failed: {result['error']}")
    
    return result['result']

def parse_webuntis_time(date_int, time_int):
    """Convert WebUntis date/time format to a datetime object"""
    date_str = str(date_int)
    time_str = str(time_int).zfill(4)
    
    dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
    return dt

def sync_calendar():
    """Sync WebUntis timetable to an ICS file (docs/calendar.ics)"""
    config = load_config()
    
    print("🔐 Logging in to WebUntis...")
    session, session_id = webuntis_login(config)
    
    print("🔍 Finding timetable element...")
    element_id, element_type = get_element_id(session, config, session_id)
    
    today = datetime.now().date()
    # Start date: 3 months ago (to see the past 3 months)
    start_date = today - timedelta(days=90)
    # End date: 6 months ahead (to see the future 6 months)
    end_date = today + timedelta(days=180)
    
    print(f"📅 Fetching timetable from {start_date} to {end_date}...")
    timetable = get_timetable(session, config, session_id, element_id, element_type, start_date, end_date)
    
    # Create ICS calendar
    cal = Calendar()
    cal.add('prodid', '-//WebUntis Sync//webuntis-sync//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'WebUntis Timetable')
    cal.add('x-wr-timezone', 'Europe/Brussels')
    
    timezone = pytz.timezone('Europe/Brussels')
    
    event_count = 0
    for lesson in timetable:
        if lesson.get('code') == 'cancelled':
            continue
        
        event = Event()
        
        # Parse times
        start_dt = parse_webuntis_time(lesson['date'], lesson['startTime'])
        end_dt = parse_webuntis_time(lesson['date'], lesson['endTime'])
        
        # Fetch data
        subjects = [su.get('longname') or su.get('name', '') for su in lesson.get('su', [])]
        teachers = [te.get('longname') or te.get('name', '') for te in lesson.get('te', [])]
        rooms = [ro.get('longname') or ro.get('name', '') for ro in lesson.get('ro', [])]
        classes = [cl.get('longname') or cl.get('name', '') for cl in lesson.get('kl', [])]
        
        # Title
        summary = ', '.join(subjects) if subjects else ''
        if not summary:
            summary = lesson.get('su', [{}])[0].get('name', 'Lesson') if lesson.get('su') else 'Lesson'
        if lesson.get('substText'):
            summary = f"{summary} ({lesson['substText']})"
        
        event.add('summary', summary)
        event.add('dtstart', timezone.localize(start_dt))
        event.add('dtend', timezone.localize(end_dt))
        
        description_parts = []
        
        # 1. Teacher(s)
        if teachers:
            description_parts.append(' / '.join(teachers))
            
        # 2. Classes
        if classes:
            description_parts.append(' / '.join(classes))
            
        # 3. Location (rooms) removed here because it is already in the location field
        
        # 4. Extra info
        if lesson.get('info'):
            description_parts.append(str(lesson['info']))
        if lesson.get('substText'):
            description_parts.append(str(lesson['substText']))
        
        if description_parts:
            event.add('description', '\n'.join(description_parts))
        
        # Location field separate
        if rooms:
            event.add('location', ', '.join(rooms))
        
        # Unique ID
        event.add('uid', f"{lesson['id']}-{lesson['date']}-{lesson['startTime']}@webuntis-sync")
        
        cal.add_component(event)
        event_count += 1
    
    # Write ICS to docs
    os.makedirs('docs', exist_ok=True)
    with open('docs/calendar.ics', 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"✅ Calendar synced: {event_count} events added")

if __name__ == '__main__':
    try:
        sync_calendar()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise