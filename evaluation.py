import json
import numpy as np

with open('responses.json') as f:
    responses = json.load(f)

responses = responses["responses"]

tot_nons = 0
tot_loops = 0
sum_nons = 0
sum_loops = 0
all_non_values = []
all_loop_values = []
for response in responses[:]:
    keys = list(response.keys())
    for key in keys:
        if key.endswith(".wav"):
            value = response[key]
            if "non" in key:
                all_non_values.append(value)
            else:
                all_loop_values.append(value)

all_non_values = np.array(all_non_values)
all_loop_values = np.array(all_loop_values)

print("Non-Loop")
print(f"Mean {np.mean(all_non_values):.2f}, Std: {np.std(all_non_values):.2f}, Median: {np.median(all_non_values):.2f}")
print()
print("Loop")
print(f"Mean {np.mean(all_loop_values):.2f}, Std: {np.std(all_loop_values):.2f}, Median: {np.median(all_loop_values):.2f}")
