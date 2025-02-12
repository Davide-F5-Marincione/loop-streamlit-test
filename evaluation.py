import json
import numpy as np

with open('responses.json') as f:
    responses = json.load(f)

responses = responses["responses"]

tot_nons = 0
tot_loops = 0
sum_nons = 0
sum_loops = 0
for response in responses:
    keys = list(response.keys())
    for key in keys:
        if key.endswith(".wav"):
            value = response[key]["value"]
            print(f"{key}: {value}")
            if "non" in key:
                sum_nons += value
                tot_nons += 1
            else:
                sum_loops += value
                tot_loops += 1

print(f"Average non-looping: {sum_nons / tot_nons}")
print(f"Average looping: {sum_loops / tot_loops}")