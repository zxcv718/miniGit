"""줄 단위 diff: LCS(최장 공통 부분수열) 동적 계획법."""


def diff_lines(a, b):
    """두 줄 목록을 비교해 [(tag, line)]을 돌려준다. ' ' 공통, '-' 삭제, '+' 추가.

    lcs[i][j] = a[i:]와 b[j:]의 LCS 길이. 뒤에서부터 채우면 앞에서부터 바로 복원할 수 있다.
    시간/공간 O(n*m).
    """
    # ponytail: O(n*m) 테이블이라 수만 줄 파일엔 무겁다, 필요하면 Myers O((n+m)D)로
    n, m = len(a), len(b)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                lcs[i][j] = lcs[i + 1][j + 1] + 1
            else:
                lcs[i][j] = max(lcs[i + 1][j], lcs[i][j + 1])
    out, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            out.append((" ", a[i]))
            i += 1
            j += 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            out.append(("-", a[i]))
            i += 1
        else:
            out.append(("+", b[j]))
            j += 1
    out.extend(("-", line) for line in a[i:])
    out.extend(("+", line) for line in b[j:])
    return out
