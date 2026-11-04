import urllib.request
import json

def api_call(endpoint, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/{endpoint}",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

base = {
    "sleep_mid_hrs": 5.5, "sleep_quality": 2, "bedtime_code": 3,
    "screen_mid_hrs": 7.0, "phone_bed_code": 4, "exercise_days_mid": 0.0,
    "deadlines_code": 3, "workload_code": 3, "performance_code": 2.0
}

# Scenario 1: Moderate improvement
scenario_1 = dict(base)
scenario_1["workload_code"] = 2       # Reduce workload from Heavy to Manageable
scenario_1["phone_bed_code"] = 1      # Stop phone in bed

res_1 = api_call("whatif", {"baseline": base, "modified": scenario_1})
print("Scenario 1 (Workload 3->2, Phone 4->1):")
print(f"Base Score={res_1['baseline']['score']}, New Score={res_1['modified']['score']}, Diff={res_1['score_difference']}, Direction={res_1['direction']}, CatChanged={res_1['category_changed']}")

# Scenario 2: Severe escalation
scenario_2 = dict(base)
scenario_2["workload_code"] = 4       # Overwhelming
scenario_2["sleep_mid_hrs"] = 4.5     # Less sleep

res_2 = api_call("whatif", {"baseline": base, "modified": scenario_2})
print("\nScenario 2 (Workload 3->4, Sleep 5.5->4.5):")
print(f"Base Score={res_2['baseline']['score']}, New Score={res_2['modified']['score']}, Diff={res_2['score_difference']}, Direction={res_2['direction']}, CatChanged={res_2['category_changed']}")

assert res_1['score_difference'] < 0, "Scenario 1 should decrease score"
assert res_2['score_difference'] > 0, "Scenario 2 should increase score"
print("\nWhat-if scenarios successfully verified!")
