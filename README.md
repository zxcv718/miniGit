# Mini Git

Git의 커밋 그래프(DAG), 브랜치, 역색인 검색, 직접 구현한 정렬을 담은 인메모리 CLI.

## 실행

```bash
python main.py        # Python 3.10+, 외부 패키지 없음
python sorting.py     # 정렬 성능 비교 (보너스)
```

## 명령어

| 명령 | 설명 |
|---|---|
| `init <user_name>` | 저장소 초기화(main 브랜치, HEAD=main). 재실행 시 기록은 유지하고 사용자만 변경 |
| `branch <name>` | 현재 HEAD 커밋을 가리키는 브랜치 생성 |
| `switch <name>` | HEAD를 브랜치로 이동 |
| `commit <message>` | HEAD를 부모로 커밋 생성 + 역색인 갱신 |
| `log` | 부모가 자식보다 먼저 나오는 위상 순서 |
| `log --sort-by=date\|author` | 병합 정렬(안정) |
| `path <c1> <c2>` | 무방향 최단 경로(동률이면 사전순 최소), 없으면 `No path` |
| `ancestors <hash>` | 모든 조상 (가까운 순) |
| `search <keyword>` / `search --author=<name>` | 역색인 검색 (대소문자 무시, 여러 단어는 AND) |
| `merge <branch>` | (보너스) 부모 2개인 merge commit |
| `diff <file1> <file2>` | (보너스) 줄 단위 비교: `  ` 공통 / `- ` 삭제 / `+ ` 추가 |
| `exit` / `quit` | 종료 (Ctrl-D도 가능) |

명령어는 대소문자를 가리지 않습니다. 공백이 들어간 인자는 `"..."`로 감쌉니다.

### 에러와 경계 케이스

| 상황 | 출력 |
|---|---|
| `init` 전에 `init`·`diff` 외 명령 | `Not initialized. Run: init <user_name>` |
| 인자 개수가 틀림, 빈 문자열, 닫히지 않은 따옴표 | `Invalid args` |
| 없는 명령 | `Unknown command: <cmd>` |
| `branch`: 이미 있는 이름 | `Branch already exists: <name>` |
| `switch` / `merge`: 없는 브랜치 | `Unknown branch: <name>` |
| `path` / `ancestors`: 없는 hash | `Unknown commit: <hash>` |
| `path`: 연결되지 않은 두 커밋(첫 커밋 전에 만든 브랜치는 별도 루트가 됨) | `No path` |
| `ancestors`: 루트 커밋 | `No ancestors.` |
| `log`: 커밋 없음 / `--sort-by`가 `date`·`author` 외 | `No commits yet.` / `Invalid args` |
| `search`: 결과 없음 / `--author=` 값 없음 | `No commits found.` / `Invalid args` |
| `merge`: 현재 브랜치 자신 | `Cannot merge a branch into itself` |
| `merge`: 어느 한쪽 브랜치에 커밋이 없음(첫 커밋 전) | `Nothing to merge` |
| `merge`: 상대 브랜치 끝이 이미 내 조상 | `Already up to date` |
| `diff`: 파일을 읽을 수 없음 | `Cannot read file: <path>` |

`search`와 `log --sort-by`는 서로 다른 명령이라 함께 쓰지 않습니다. 검색 결과는 항상 커밋 생성 순서입니다.

### 재초기화

`init`을 다시 실행하면 커밋과 브랜치는 그대로 두고 현재 사용자만 바꿉니다. 여러 작성자의 커밋을 만들어 `search --author`와 `log --sort-by=author`를 시연할 때 씁니다.

```
mini-git> init Alice
Initialized repository.
Current branch: main
Current user: Alice
mini-git> commit "Initial commit"
[main 356a192] Initial commit
mini-git> init Bob
Reinitialized existing repository.
Current branch: main
Current user: Bob
mini-git> commit "Fix bug"
[main da4b923] Fix bug
mini-git> log
commit 356a192 (Alice, 2026-10-07 06:08:16) [main]
Initial commit
commit da4b923 (Bob, 2026-10-07 06:08:16) [main]
Fix bug
```

### 실행 예시

```
mini-git> init "Alice"
Initialized repository.
Current branch: main
Current user: Alice
mini-git> commit "Initial commit"
[main 356a192] Initial commit
mini-git> branch feature
Created branch: feature
mini-git> switch feature
Switched to branch: feature
mini-git> commit "Add login feature"
[feature da4b923] Add login feature
mini-git> switch main
Switched to branch: main
mini-git> commit "Add payment feature"
[main 77de68d] Add payment feature
mini-git> path da4b923 77de68d
Path: da4b923 -> 356a192 -> 77de68d
mini-git> search login
Found 1 commit:
- da4b923: Add login feature
```

## 구조

| 파일 | 책임 |
|---|---|
| `main.py` | 파싱(`shlex`) → 실행 → 출력. `cmd_<name>` 메서드로 명령 디스패치 |
| `repo.py` | `Repository`: commits(hash→Commit), branches(name→hash), head(브랜치명), user, index |
| `graph.py` | `topo_order`(Kahn), `ancestors`(BFS), `shortest_path`(BFS 2회) — 입력은 `{hash: [parents]}` 하나로 통일 |
| `sorting.py` | `merge_sort`, `quick_sort`, `benchmark` |
| `index.py` | `InvertedIndex` (keyword→hashes, author→hashes) |
| `diff.py` | LCS 기반 `diff_lines` |

## 설계 포인트

- **DAG 보장**: 부모는 항상 이미 존재하는 커밋이라 새 간선이 사이클을 만들 수 없다. 사이클이 있으면 위상 정렬이 불가능해 LOG가 끝나지 않거나 조상 탐색이 무한 루프에 빠진다. `topo_order`는 이를 `ValueError`로 감지한다. 사용자 명령으로는 사이클을 만들 방법이 없으므로 이 예외는 내부 불변식 검사이고, 사용자용 메시지는 따로 두지 않았다.
- **LOG 부모 우선**: Kahn 알고리즘(진입차수=부모 수, FIFO 큐). O(V+E). 동시에 출력 가능한 커밋이 여럿이면(예: 같은 부모의 두 자식) 큐에 들어간 순서, 즉 생성 순서대로 나온다. 그래서 같은 입력이면 출력이 항상 같다.
- **PATH**: 커밋-부모 간선을 무방향으로 봐야 형제 브랜치끼리도 공통 조상을 거쳐 연결된다. dst에서 BFS로 거리표를 만들고, src에서 거리가 1씩 줄어드는 가장 작은 hash를 고른다. hash가 모두 7자리라 이것이 곧 문자열 사전순 최소다.
- **hash**: `sha1(카운터)[:7]` + 충돌 시 다음 카운터. 같은 명령 순서면 같은 hash가 나와 테스트와 디버깅이 재현 가능하다. 난수 기반이면 실행마다 hash가 달라져 테스트가 hash를 하드코딩할 수 없다. 재시도 루프는 카운터가 매번 바뀌므로 7자리 공간(16⁷ ≈ 2.7억)이 다 차지 않는 한 곧 끝나서 상한을 두지 않았다.
- **역색인**: 커밋 생성 시점(`Repository.commit`) 한 곳에서 갱신한다. 검색은 dict 조회 O(1) + 결과 k개 O(k). 순회 검색은 O(N·메시지 길이)다.

## 정렬 알고리즘

| 알고리즘 | 평균 | 최악 | 안정 | 비고 |
|---|---|---|---|---|
| merge_sort | O(n log n) | O(n log n) | O | `LOG --sort-by`에 사용(동률이면 위상 순서 유지) |
| quick_sort | O(n log n) | O(n²) | X | 랜덤 피벗, 제자리 교환 |

### 성능 비교 (`python sorting.py`, Python 3.14, Apple Silicon)

```
      n  input     merge_sort   quick_sort
    100  random      0.00010s     0.00006s
    100  sorted      0.00007s     0.00005s
   1000  random      0.00125s     0.00084s
   1000  sorted      0.00083s     0.00088s
  10000  random      0.01625s     0.01234s
  10000  sorted      0.01007s     0.01044s
```

- n이 10배가 되면 두 알고리즘 모두 약 13배 늘어난다. n log n의 증가율(10 × log 10000 / log 1000 ≈ 13.3)과 맞는다.
- 랜덤 입력에서는 quick_sort가 더 빠르다. 리스트를 새로 만들지 않고 제자리에서 교환하기 때문이다.
- 이미 정렬된 입력은 고정 피벗 퀵 정렬의 최악 사례(O(n²))다. 랜덤 피벗 덕분에 여기서도 n log n이 유지된다.

## 확장 질문 메모

- **커밋 10배**: `_parents_map()`이 호출마다 O(V)로 재구성되는 것이 첫 병목이다. 조상이 1개뿐인 커밋을 조회해도 커밋 수에 비례해 느려진다. → `Repository`에 `parents`·`children` dict 필드를 두고 `commit()`에서 새 커밋을 넣을 때 함께 갱신하면, 그래프 명령이 매번 다시 만들 필요가 없다. LOG 위상 정렬은 O(V+E)라 선형으로 늘어나고, `diff`는 O(n·m)이다.
- **큰 그래프에서 PATH**: BFS 두 번(거리표 + 경로 선택)이라 O(V+E) 시간에 거리표 O(V) 메모리를 쓴다. 두 커밋이 가까워도 거리표는 연결된 커밋 전체로 퍼진다. → 양쪽에서 동시에 BFS를 넓히다 만나면 멈추는 양방향 BFS로 탐색 범위를 줄인다.
- **PATH를 부모 방향만 허용**: 조상-자손 관계에서만 경로가 생기고 형제 브랜치 간은 `No path`가 된다. `_undirected` 대신 `parents`를 인접 리스트로 쓰고, 양쪽 방향(a→b, b→a)을 각각 시도한다.
- **author 정렬 + 부모 우선 유지**: Kahn의 FIFO 큐를 author 키 우선순위 큐로 바꾼다(진입차수 0인 후보 중 author가 가장 작은 것부터 꺼냄).
- **분산 환경의 hash**: 카운터는 저장소마다 1부터 시작하므로, 두 저장소가 독립적으로 만든 커밋은 hash가 겹친다. 저장소를 합치는 기능이 생기면 실제 Git처럼 커밋 내용(부모 hash·작성자·시각·메시지)을 sha1한 내용 기반 hash로 바꾸고, 지금의 "이미 있으면 다음" 검사는 그대로 유지한다.
