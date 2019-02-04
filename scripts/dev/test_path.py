import json

with open("app/test/data/graph.json") as f:
    graph = json.load(f)

with open("app/test/data/rates.json") as f:
    rates = json.load(f)

from app.paths import find_cycles

c = find_cycles(graph, rates)
print(c)
