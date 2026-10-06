"""Mini Git REPL 엔트리 포인트. 한 줄을 파싱 → Repository 호출 → 결과 문자열 출력.

실행: python main.py
"""
import shlex

from repo import MiniGitError, Repository

PROMPT = "mini-git> "
INVALID = "Invalid args"


def format_commit(c):
    """LOG 한 항목. hash / author / timestamp / branch / message가 식별 가능해야 한다."""
    lines = [f"commit {c.hash} ({c.author}, {c.timestamp:%Y-%m-%d %H:%M:%S}) [{c.branch}]"]
    if len(c.parents) > 1:
        lines.append("Merge: " + " ".join(c.parents))
    lines.append(c.message)
    return "\n".join(lines)


def bullet_list(header, commits):
    """'- hash: message' 목록."""
    return "\n".join([header] + [f"- {c.hash}: {c.message}" for c in commits])


def _text(args):
    """공백이 들어갈 수 있는 문자열 인자(사용자명/메시지/키워드). 따옴표 없이 쓴 여러 단어도 합친다."""
    text = " ".join(args).strip()
    if not text:
        raise MiniGitError(INVALID)
    return text


def _name(args):
    """공백 없는 단일 인자(브랜치명/hash)."""
    if len(args) != 1:
        raise MiniGitError(INVALID)
    return args[0]


class Shell:
    """REPL 세션 하나의 상태(저장소)를 들고 명령을 실행한다.

    명령 'foo'는 메서드 cmd_foo(args)에 대응한다. 새 명령은 메서드 하나만 추가하면 된다.
    """

    def __init__(self, clock=None):
        self.repo = None
        self.clock = clock

    def execute(self, line):
        """명령 한 줄을 실행해 출력 문자열을 돌려준다. 어떤 입력에도 예외를 밖으로 내보내지 않는다."""
        try:
            tokens = shlex.split(line)
        except ValueError:  # 닫히지 않은 따옴표
            return INVALID
        if not tokens:
            return ""
        handler = getattr(self, f"cmd_{tokens[0].lower()}", None)
        if handler is None:
            return f"Unknown command: {tokens[0]}"
        try:
            return handler(tokens[1:])
        except MiniGitError as e:
            return str(e)

    def _repo(self):
        if self.repo is None:
            raise MiniGitError("Not initialized. Run: init <user_name>")
        return self.repo

    def cmd_init(self, args):
        """저장소 초기화. 이미 있으면 기록을 유지한 채 사용자만 바꾼다(git init 재실행과 같은 취지)."""
        user = _text(args)
        if self.repo is None:
            self.repo = Repository(user, clock=self.clock)
            title = "Initialized repository."
        else:
            self.repo.user = user
            title = "Reinitialized existing repository."
        return f"{title}\nCurrent branch: {self.repo.head}\nCurrent user: {user}"

    def cmd_branch(self, args):
        repo, name = self._repo(), _name(args)
        repo.create_branch(name)
        return f"Created branch: {name}"

    def cmd_switch(self, args):
        repo, name = self._repo(), _name(args)
        repo.switch(name)
        return f"Switched to branch: {name}"

    def cmd_commit(self, args):
        repo = self._repo()
        c = repo.commit(_text(args))
        return f"[{c.branch} {c.hash}] {c.message}"

    def cmd_log(self, args):
        repo = self._repo()
        if not args:
            commits = repo.log()
        elif len(args) == 1 and args[0].lower().startswith("--sort-by="):
            commits = repo.log_sorted(args[0].split("=", 1)[1].lower())
        else:
            raise MiniGitError(INVALID)
        return "\n".join(format_commit(c) for c in commits) or "No commits yet."

    def cmd_path(self, args):
        repo = self._repo()
        if len(args) != 2:
            raise MiniGitError(INVALID)
        path = repo.path(*args)
        return "No path" if path is None else "Path: " + " -> ".join(path)

    def cmd_ancestors(self, args):
        repo, h = self._repo(), _name(args)
        commits = repo.ancestors(h)
        return bullet_list(f"Ancestors of {h}:", commits) if commits else "No ancestors."

    def cmd_search(self, args):
        repo, query = self._repo(), _text(args)
        if query.lower().startswith("--author="):
            commits = repo.search_author(_text([query.split("=", 1)[1]]))
        else:
            commits = repo.search_keyword(query)
        if not commits:
            return "No commits found."
        n = len(commits)
        return bullet_list(f"Found {n} commit{'s' if n > 1 else ''}:", commits)

    def cmd_merge(self, args):
        repo, name = self._repo(), _name(args)
        c = repo.merge(name)
        return f"[{c.branch} {c.hash}] {c.message}"


def main():
    """REPL 루프: exit/quit 또는 EOF(Ctrl-D)로 종료."""
    shell = Shell()
    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        out = shell.execute(line)
        if out:
            print(out)


if __name__ == "__main__":
    main()
