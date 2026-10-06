"""역색인(Inverted Index): 토큰 -> 커밋 hash 목록(posting list).

순회 검색은 커밋 N개의 메시지를 전부 훑어 O(N * 메시지 길이)가 든다.
역색인은 dict 조회 O(1)로 후보 목록을 바로 꺼내고, 비용은 결과 개수 k에 비례한다: O(k).
대신 커밋 생성 시 O(토큰 수)만큼 미리 색인하는 비용을 낸다.
"""


def tokenize(text):
    """공백 split + lower (과제 최소 기준). 순서를 지키며 중복을 없앤다."""
    return list(dict.fromkeys(text.lower().split()))


class InvertedIndex:
    """keyword, author 두 종류의 역색인. add()는 커밋 생성 시점에 한 번 호출된다."""

    def __init__(self):
        self.keywords = {}  # token -> [hash, ...]
        self.authors = {}   # author(lower) -> [hash, ...]

    def add(self, commit_hash, message, author):
        """커밋 하나를 색인한다. posting list는 커밋 생성 순서대로 쌓인다. O(토큰 수)."""
        for token in tokenize(message):
            self.keywords.setdefault(token, []).append(commit_hash)
        self.authors.setdefault(author.lower(), []).append(commit_hash)

    def search_keyword(self, query):
        """질의 토큰을 모두 포함하는 커밋(AND). 첫 토큰의 posting 순서를 따른다."""
        tokens = tokenize(query)
        if not tokens:
            return []
        result = list(self.keywords.get(tokens[0], []))
        for token in tokens[1:]:
            other = set(self.keywords.get(token, []))
            result = [h for h in result if h in other]
        return result

    def search_author(self, name):
        """작성자 이름(대소문자 무시)이 일치하는 커밋."""
        return list(self.authors.get(name.lower(), []))
