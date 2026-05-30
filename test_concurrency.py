import requests
import threading
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/events/1"
NUM_REQUESTS = 50

def reset_event():
    # Use a management command or a helper endpoint to reset the database between tests
    # For simplicity, we can trust that the test script runs against a clean state
    # or implement a reset endpoint if needed.
    # However, the requirement says Docker startup seeds the data.
    # We can use the vulnerable endpoint first, then pessimistic, then optimistic.
    # But each test needs a fresh 0 booked_seats to accurately show the result.
    # I'll create a simple reset view in Django.
    requests.post(f"{BASE_URL}/reset/") # I need to implement this

def send_request(url, results):
    try:
        response = requests.post(url, timeout=10)
        status_code = response.status_code
        if status_code == 201:
            results["success"] += 1
        elif status_code == 409:
            results["conflict"] += 1
        elif status_code == 400:
            results["no_seats"] += 1
        else:
            results["other_fail"] += 1
    except requests.RequestException:
        results["other_fail"] += 1

def run_test(endpoint_path):
    url = f"{BASE_URL}/{endpoint_path}/"
    results = {"success": 0, "conflict": 0, "no_seats": 0, "other_fail": 0}
    
    # Reset state via management command-equivalent or a reset endpoint
    # I will add a reset endpoint to help this script.
    requests.post(f"{BASE_URL}/reset/")
    
    threads = []
    print(f"Starting test for {endpoint_path}...")
    for _ in range(NUM_REQUESTS):
        thread = threading.Thread(target=send_request, args=(url, results))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        
    # Get final booked seats from DB
    status_resp = requests.get(f"{BASE_URL}/status/")
    total_booked = status_resp.json().get('booked_seats', 0)
    
    print(f"Finished {endpoint_path}. Success: {results['success']}, Failed: {results['conflict'] + results['no_seats'] + results['other_fail']}. Total in DB: {total_booked}")
    return results, total_booked

def main():
    # Wait for service to be up
    print("Waiting for server to be ready...")
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/status/")
            break
        except:
            time.sleep(1)
    
    # Test on_commit specifically (Requirement 8)
    print("Testing on_commit rollback (Requirement 8)...")
    requests.post(f"{BASE_URL}/reset/")
    resp = requests.post(f"{BASE_URL}/book_pessimistic_fail/")
    print(f"Failing request status: {resp.status_code}")
    
    # Run concurrency tests
    v_results, v_booked = run_test("book_vulnerable")
    p_results, p_booked = run_test("book_pessimistic")
    o_results, o_booked = run_test("book_optimistic")

    final_results = {
        "vulnerable": {
            "successful_bookings": v_results["success"],
            "failed_bookings": v_results["no_seats"] + v_results["conflict"] + v_results["other_fail"],
            "total_seats_in_db": v_booked
        },
        "pessimistic": {
            "successful_bookings": p_results["success"],
            "failed_bookings": p_results["no_seats"] + p_results["conflict"] + p_results["other_fail"],
            "total_seats_in_db": p_booked
        },
        "optimistic": {
            "successful_bookings": o_results["success"],
            "conflict_failures": o_results["conflict"],
            "other_failures": o_results["no_seats"] + o_results["other_fail"],
            "total_seats_in_db": o_booked
        }
    }

    with open("results.json", "w") as f:
        json.dump(final_results, f, indent=2)
    
    print("Test concurrency completed. results.json generated.")

if __name__ == "__main__":
    main()
