import time
import json
import collections
from operator import itemgetter

def find_cycles(graph, rates, source="USDT"):
    # Add a dummy root node
    root = "Root"
    graph[root] = collections.defaultdict(dict)
    for k in graph.keys():
        graph[root][k] = 0.0

    # Initialize distances and predecessors
    dist = {}
    pred = {}

    for k in graph.keys():
        dist[k] = float("inf")
    dist[root] = 0

    # Relax every edge n - 1 times
    for i in range(int(len(graph.keys()) - 1)):
        for v_1, e in graph.items():
            for v_2, w in e.items():
                if dist[v_2] > dist[v_1] + w:
                    dist[v_2] = dist[v_1] + w
                    pred[v_2] = v_1

    # Relax every edge again to find negative weight cycles
    arbitrage = False
    cyclic = {}
    for v_1, e in graph.items():
        for v_2, w in e.items():
            if dist[v_2] > dist[v_1] + w:
                arbitrage = True
                dist[v_2] = dist[v_1] + w

                # Keep track of vertices in negative-weight cycles
                cyclic[v_2] = True

    if not arbitrage:
        return []

    # Calculate arbitrage sequences
    sequences = []
    for v in cyclic.keys():
        visited = collections.defaultdict(bool)
        visited[v] = True
        seq = []
        p = v

        # in a end while loop code is executed once before the condition is evaluated
        seq.append(p)
        visited[p] = True
        p = pred[p]

        while p is not None and not visited[p]:
            seq.append(p)
            visited[p] = True
            p = pred[p]
        seq = list(reversed(seq))
        seq.append(seq[0])

        # Calculate the arbitrage amount
        # See https://stackoverflow.com/questions/50709676/what-does-inject-do
        # Some bug here; Keyerror ??? rewrite to for loop and fix.
        # val = reduce(lambda v,i: v*rates[seq[i]][seq[i+1]], range(len(seq)-1), 1.0)
        # The reason is that this assumes every currency is connected to every other..

        try:
            val = 1.0
            for i in range(len(seq) - 1):
                val = val * rates[seq[i]][seq[i + 1]]
        except KeyError as e:
            continue

        if seq[0] != source:
            continue
        sequences.append({"currencies": seq, "value": val})

    # Output the sequences in descending order of value
    sequences.sort(key=itemgetter("value"), reverse=True)
    for i, v in enumerate(sequences):
        if v["value"] <= 1.0:
            del sequences[i]

    return sequences

with open("data/graph.json") as f:
    graph =json.load(f)

with open("data/rates.json") as f:
    rates = json.load(f)

bf = time.time()
for i in range(10000):
    find_cycles(graph, rates)
af = time.time()

print("Execution of 10000 paths took: {}".format(af - bf))
