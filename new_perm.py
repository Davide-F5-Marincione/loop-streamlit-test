import random

l = list(range(1, 31))
for _ in range(20):
    random.shuffle(l)
    print(l)
