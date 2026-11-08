"""Checks that the implemented Huffman quantity equals the definition used in Proposition H:
L(n_1..n_K) = min { sum_k n_k l_k : l_k in N, sum_k 2^-l_k <= 1 }  (L = 0 when K <= 1),
by exhaustive search over depth vectors (l_k <= 9), for 20,000 random weight vectors with K <= 6."""
import heapq, itertools, random
def huffman(ms):                       # exactly the computation in phase123/mbr.py CompiledH.h
    ms = [x for x in ms if x]
    if len(ms) < 2: return 0
    hp = list(ms); heapq.heapify(hp); L = 0
    while len(hp) > 1:
        a = heapq.heappop(hp); b = heapq.heappop(hp); L += a + b; heapq.heappush(hp, a + b)
    return L
def brute(ms):
    ms = [x for x in ms if x]
    if len(ms) <= 1: return 0
    best = None
    for ls in itertools.product(range(0, 8), repeat=len(ms)):
        if sum(2.0 ** -l for l in ls) <= 1 + 1e-12:
            v = sum(n * l for n, l in zip(ms, ls)); best = v if best is None or v < best else best
    return best
r = random.Random(129300); n = 0
for _ in range(4000):
    K = r.randint(0, 5); ms = [r.randint(1, 12) for _ in range(K)]
    assert huffman(ms) == brute(ms), ms; n += 1
print('Huffman implementation == Kraft-constrained minimum on', n, 'weight vectors')
