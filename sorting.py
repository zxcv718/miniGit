"""정렬 알고리즘 직접 구현 (과제 제약: 표준 정렬 API 사용 금지)."""
import random
import time


def merge_sort(items, key=lambda x: x):
    """병합 정렬. 안정 정렬, 평균/최악 O(n log n), 추가 메모리 O(n).

    동률이면 왼쪽(먼저 들어온) 원소를 먼저 내보내므로 입력 순서가 유지된다(안정성).
    입력을 바꾸지 않고 새 리스트를 돌려준다.
    """
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(right[j]) < key(left[i]):  # 엄격히 작을 때만 오른쪽 → 안정성
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            i += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(items, key=lambda x: x):
    """퀵 정렬(Lomuto 분할, 랜덤 피벗). 불안정 정렬, 평균 O(n log n), 최악 O(n^2).

    최악은 피벗이 매번 최솟/최댓값일 때다. 랜덤 피벗으로 그 확률을 낮춘다.
    제자리 교환 때문에 동률 원소의 상대 순서가 바뀔 수 있다.
    """
    arr = list(items)
    _quick(arr, 0, len(arr) - 1, key)
    return arr


def _quick(arr, lo, hi, key):
    """작은 쪽만 재귀하고 큰 쪽은 반복문으로 처리 → 재귀 깊이 O(log n)."""
    while lo < hi:
        p = _partition(arr, lo, hi, key)
        if p - lo < hi - p:
            _quick(arr, lo, p - 1, key)
            lo = p + 1
        else:
            _quick(arr, p + 1, hi, key)
            hi = p - 1


def _partition(arr, lo, hi, key):
    """피벗보다 작은 원소를 왼쪽으로 모으고 피벗의 최종 위치를 돌려준다."""
    # ponytail: 2-way 분할이라 중복 키가 아주 많으면 O(n^2)에 가까워짐, 필요하면 3-way 분할로
    r = random.randint(lo, hi)
    arr[r], arr[hi] = arr[hi], arr[r]
    pivot = key(arr[hi])
    i = lo
    for j in range(lo, hi):
        if key(arr[j]) < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi] = arr[hi], arr[i]
    return i


def _timed(sort, data):
    start = time.perf_counter()
    sort(data)
    return time.perf_counter() - start


def benchmark(sizes=(100, 1_000, 10_000), repeat=3):
    """입력 크기·종류별 실행 시간(초, repeat회 중 최솟값)을 잰다.

    'sorted' 입력은 고정 피벗 퀵 정렬의 최악 사례인데, 랜덤 피벗이라 O(n log n)이 유지되는지 확인하려고 넣었다.
    """
    rows = []
    for n in sizes:
        inputs = {
            "random": [random.randint(0, n * 10) for _ in range(n)],
            "sorted": list(range(n)),
        }
        for kind, data in inputs.items():
            t_merge = min(_timed(merge_sort, data) for _ in range(repeat))
            t_quick = min(_timed(quick_sort, data) for _ in range(repeat))
            rows.append((n, kind, t_merge, t_quick))
    return rows


if __name__ == "__main__":
    print(f"{'n':>7}  {'input':<7} {'merge_sort':>12} {'quick_sort':>12}")
    for n, kind, t_merge, t_quick in benchmark():
        print(f"{n:>7}  {kind:<7} {t_merge:>11.5f}s {t_quick:>11.5f}s")
