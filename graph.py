"""커밋 그래프 탐색 알고리즘.

모든 함수는 같은 입력 하나를 받는다: parents = {hash: [부모 hash, ...]}.
간선 방향은 자식 -> 부모(Git과 같음). 필요한 경우에만 뒤집거나(children_of)
양방향으로 본다(_undirected). LOG/PATH/ANCESTORS가 이 표현을 공유해 재사용된다.
"""
from collections import deque


def children_of(parents):
    """부모 맵을 뒤집은 {hash: [자식 hash, ...]}. O(V+E)."""
    children = {h: [] for h in parents}
    for h, ps in parents.items():
        for p in ps:
            children[p].append(h)
    return children


def topo_order(parents):
    """Kahn 알고리즘. 부모가 항상 자식보다 먼저 나오는 순서를 돌려준다. O(V+E).

    진입차수 = 부모 수. 부모가 모두 출력된 커밋만 큐에 들어간다.
    큐는 FIFO이고 시작 순서는 dict 삽입(=생성) 순서라 결과가 결정적이다.
    사이클이 있으면 그 노드들은 진입차수가 0이 되지 않아 결과가 짧아진다 → ValueError.
    """
    indegree = {h: len(ps) for h, ps in parents.items()}
    children = children_of(parents)
    queue = deque(h for h, d in indegree.items() if d == 0)
    order = []
    while queue:
        h = queue.popleft()
        order.append(h)
        for c in children[h]:
            indegree[c] -= 1
            if indegree[c] == 0:
                queue.append(c)
    if len(order) != len(parents):
        raise ValueError("cycle detected: commit graph must be a DAG")
    return order


def ancestors(parents, start):
    """start에서 부모 방향으로 도달 가능한 모든 커밋. BFS라 가까운 순이고 start는 제외한다.

    visited 집합으로 merge 커밋의 공통 조상을 한 번만 출력한다. O(V+E).
    """
    seen = {start}
    order = []
    queue = deque([start])
    while queue:
        for p in parents[queue.popleft()]:
            if p not in seen:
                seen.add(p)
                order.append(p)
                queue.append(p)
    return order


def _undirected(parents):
    """부모-자식 간선을 양방향으로 본 인접 리스트."""
    children = children_of(parents)
    return {h: parents[h] + children[h] for h in parents}


def _bfs_distances(adj, source):
    """source에서 각 노드까지의 간선 수. 도달 못 하는 노드는 결과에 없다."""
    dist = {source: 0}
    queue = deque([source])
    while queue:
        h = queue.popleft()
        for n in adj[h]:
            if n not in dist:
                dist[n] = dist[h] + 1
                queue.append(n)
    return dist


def shortest_path(parents, src, dst):
    """무방향 최단 경로(간선 수 최소) 가운데 'h1->h2->...' 문자열이 사전순 최소인 경로. 없으면 None.

    1) dst에서 BFS로 모든 노드의 dst까지 거리를 구한다.
    2) src에서 출발해 '거리가 정확히 1 줄어드는 이웃' 중 가장 작은 hash를 매번 고른다.
    최단 경로들은 길이가 같고 hash 길이도 모두 같으므로(repo가 7자리 고정),
    앞에서부터 가장 작은 hash를 고르는 것이 곧 문자열 전체의 사전순 최소다. O(V+E).
    """
    adj = _undirected(parents)
    dist = _bfs_distances(adj, dst)
    if src not in dist:
        return None
    path = [src]
    while path[-1] != dst:
        cur = path[-1]
        path.append(min(n for n in adj[cur] if dist.get(n) == dist[cur] - 1))
    return path
