"""저장소 상태와 명령 로직. 출력 포맷은 main.py가 맡고, 여기서는 Commit 객체를 돌려준다.

책임 분리:
- commits : hash -> Commit          커밋 저장소. dict라서 hash 조회가 O(1)
- branches: 브랜치명 -> hash | None  브랜치는 커밋을 가리키는 이름표일 뿐(첫 커밋 전엔 None)
- head    : 현재 브랜치명            HEAD는 브랜치를 가리키는 symbolic ref
- user    : 현재 작성자
- index   : InvertedIndex            검색 전용 보조 구조
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime

import graph
from index import InvertedIndex
from sorting import merge_sort

SORT_KEYS = {
    "date": lambda c: c.timestamp,
    "author": lambda c: c.author.lower(),
}


class MiniGitError(Exception):
    """사용자에게 그대로 보여줄 에러 (예: 'Unknown branch: x')."""


@dataclass
class Commit:
    """커밋 그래프의 노드. parents가 간선(자식 -> 부모)이다."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: list
    branch: str  # 생성 당시 브랜치 (LOG 표시용)


class Repository:
    """인메모리 Mini Git 저장소."""

    def __init__(self, user, clock=None):
        self.user = user
        self.clock = clock or datetime.now  # 테스트에선 고정 시계 주입
        self.commits = {}
        self.branches: dict[str, str | None] = {"main": None}
        self.head = "main"
        self.index = InvertedIndex()
        self._counter = 0

    # ── 쓰기 ─────────────────────────────────────────────

    def create_branch(self, name):
        """현재 HEAD 커밋을 가리키는 새 브랜치를 만든다."""
        if name in self.branches:
            raise MiniGitError(f"Branch already exists: {name}")
        self.branches[name] = self.branches[self.head]

    def switch(self, name):
        """HEAD를 다른 브랜치로 옮긴다."""
        self._require_branch(name)
        self.head = name

    def merge(self, name):
        """현재 브랜치 끝과 name 브랜치 끝을 부모로 하는 merge 커밋을 만든다(내용 병합은 흉내만).

        상대 끝이 이미 내 조상이거나 나와 같으면 합칠 것이 없다 → 'Already up to date'.
        조상 판정은 ANCESTORS와 같은 graph.ancestors를 재사용한다.
        """
        self._require_branch(name)
        if name == self.head:
            raise MiniGitError("Cannot merge a branch into itself")
        ours, theirs = self.branches[self.head], self.branches[name]
        if ours is None or theirs is None:
            raise MiniGitError("Nothing to merge")
        if theirs == ours or theirs in graph.ancestors(self._parents_map(), ours):
            raise MiniGitError("Already up to date")
        return self.commit(f"Merge branch '{name}' into {self.head}", extra_parent=theirs)

    def commit(self, message, extra_parent=None):
        """HEAD 커밋(+ merge면 상대 브랜치 끝)을 부모로 하는 새 커밋을 만들고, 브랜치를 전진시키고, 역색인을 갱신한다.

        부모는 항상 '이미 존재하는' 커밋이므로 새 간선이 사이클을 만들 수 없다 → DAG 보장.
        역색인 갱신은 커밋이 생기는 이 한 곳에서만 일어난다(merge 커밋 포함).
        """
        parents = [p for p in (self.branches[self.head], extra_parent) if p]
        c = Commit(self._new_hash(), message, self.user, self.clock(), parents, self.head)
        self.commits[c.hash] = c
        self.branches[self.head] = c.hash
        self.index.add(c.hash, message, self.user)
        return c

    # ── 읽기 ─────────────────────────────────────────────

    def get(self, commit_hash):
        """hash로 커밋을 O(1) 조회한다. 없으면 'Unknown commit: <hash>'."""
        if commit_hash not in self.commits:
            raise MiniGitError(f"Unknown commit: {commit_hash}")
        return self.commits[commit_hash]

    def log(self):
        """모든 커밋을 부모가 자식보다 먼저 오도록(위상 정렬) 나열한다."""
        return [self.commits[h] for h in graph.topo_order(self._parents_map())]

    def log_sorted(self, by):
        """date/author 기준 병합 정렬. 안정 정렬이고 입력이 위상 순서라 동률이면 부모가 먼저 남는다."""
        if by not in SORT_KEYS:
            raise MiniGitError("Invalid args")
        return merge_sort(self.log(), key=SORT_KEYS[by])

    def path(self, a, b):
        """두 커밋 사이 무방향 최단 경로(hash 목록). 연결되지 않았으면 None."""
        self.get(a)
        self.get(b)
        return graph.shortest_path(self._parents_map(), a, b)

    def ancestors(self, commit_hash):
        """도달 가능한 모든 조상 커밋 (가까운 순)."""
        self.get(commit_hash)
        return [self.commits[h] for h in graph.ancestors(self._parents_map(), commit_hash)]

    def search_keyword(self, query):
        """역색인으로 키워드 검색."""
        return [self.commits[h] for h in self.index.search_keyword(query)]

    def search_author(self, name):
        """역색인으로 작성자 검색."""
        return [self.commits[h] for h in self.index.search_author(name)]

    # ── 내부 ─────────────────────────────────────────────

    def _new_hash(self):
        """카운터 기반 sha1 앞 7자리. 세션마다 같은 순서면 같은 hash가 나온다(재현성).

        카운터 값은 매번 다르지만 7자리로 자르면 충돌할 수 있으므로, 이미 있으면 다음 카운터로 넘긴다.
        """
        while True:
            self._counter += 1
            h = hashlib.sha1(str(self._counter).encode()).hexdigest()[:7]
            if h not in self.commits:
                return h

    def _parents_map(self):
        """graph 모듈 입력 형식 {hash: [parents]}."""
        # ponytail: 호출마다 O(V)로 다시 만든다. 커밋이 아주 많아지면 commit()에서 증분 유지로 바꿀 것
        return {h: c.parents for h, c in self.commits.items()}

    def _require_branch(self, name):
        if name not in self.branches:
            raise MiniGitError(f"Unknown branch: {name}")
