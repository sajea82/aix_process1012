from pathlib import Path
import shutil
import subprocess
import sys

ROOT_DIR = Path(r"C:\workspace\process\aix_process1012")
P1120_DIR = ROOT_DIR / "p1120"
P1120_UPDATE_DIR = P1120_DIR / "update"
P1121_DIR = ROOT_DIR / "p1121"
P1121_DATA_DIR = P1121_DIR / "data"

PYTHON_EXE = sys.executable

NOTE_UPDATE_SCRIPTS = [
    "p1120_02_최신장기미출수추가.py",
    "p1120_03_최신끝수별추가.py",
    "p1120_04_최신궁도별추가.py",
    "p1120_05_최신13고스트추가.py",
    "p1120_06_최신20고스트추가.py",
    "p1120_07_최신1부터45분포도추가.py",
    "p1120_08_최신마이너스표추가.py",
    "p1120_09_최신로또용지세로추가.py",
    "p1120_10_최신로또용지가로추가.py",
]

NOTE_FILES = [
    "02_장기미출수.xlsx",
    "03_끝수별_배치표.xlsx",
    "04_궁도별_배치표.xlsx",
    "05_13코스트_배치표.xlsx",
    "06_20코스트_배치표.xlsx",
    "07_1부터45_분포도.xlsx",
    "08_마이너스표.xlsx",
    "09_로또용지_세로분포.xlsx",
    "10_로또용지_가로분포.xlsx",
]


def _run_script(script_path: Path, args: list[str] | None = None) -> None:
    if not script_path.exists():
        raise FileNotFoundError(f"스크립트를 찾을 수 없습니다: {script_path}")
    cmd = [PYTHON_EXE, str(script_path)] + (args or [])
    print(f"\n▶ 실행: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(script_path.parent), check=True)


def update_master_ledger(draw_round: int, nums: list[int], bonus: int) -> None:
    """p1120/p1120_02.py를 통해 새 회차 원장을 반영합니다."""
    if len(nums) != 6 or len(set(nums)) != 6:
        raise ValueError("당첨번호 6개(n1~n6)는 중복 없는 6개의 정수여야 합니다.")
    if not (1 <= bonus <= 45) or any(not (1 <= n <= 45) for n in nums):
        raise ValueError("로또 번호와 보너스 번호는 1~45 범위여야 합니다.")

    master_script = P1120_DIR / "p1120_02.py"
    # p1120_02.py가 CLI 인자(--round 등)를 지원할 때를 대비해 전달하되,
    # 대화형/내부 함수만 있는 경우엔 스크립트 실행 후 안내를 띄웁니다.
    cli_args = [
        "--round", str(draw_round),
        "--nums", *[str(n) for n in sorted(nums)],
        "--bonus", str(bonus),
    ]
    try:
        subprocess.run(
            [PYTHON_EXE, str(master_script)] + cli_args,
            cwd=str(P1120_DIR),
            check=True,
        )
    except subprocess.CalledProcessError:
        print("[안내] CLI 인자 직접 반영이 미지원인 구조라면 p1120_02.py 실행 흐름으로 진행합니다.")
        _run_script(master_script)


def update_all_notes() -> None:
    """02 ~ 10 노트 최신화 스크립트를 순차 실행합니다."""
    for script_name in NOTE_UPDATE_SCRIPTS:
        _run_script(P1120_DIR / script_name)


def sync_notes_to_p1121() -> None:
    """p1120/update/의 9개 노트 엑셀을 p1121/data/로 복사합니다."""
    P1121_DATA_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for fname in NOTE_FILES:
        src = P1120_UPDATE_DIR / fname
        dst = P1121_DATA_DIR / fname
        if not src.exists():
            raise FileNotFoundError(f"최신화 노트 파일이 없습니다: {src}")
        shutil.copy2(src, dst)
        copied += 1
    print(f"\n[동기화 완료] {copied}개 노트 엑셀 → {P1121_DATA_DIR}")


def run_prediction() -> None:
    """p1121/p1121_05.py를 실행해 다음 회차 예측 조합을 출력합니다."""
    _run_script(P1121_DIR / "p1121_05.py")


def run_weekly_pipeline(
    draw_round: int | None = None,
    nums: list[int] | None = None,
    bonus: int | None = None,
    skip_master_update: bool = False,
) -> None:
    print("=" * 72)
    print("로또 6/45 주간 원클릭 최신화 및 예측 파이프라인 시작")
    print("=" * 72)

    if not skip_master_update:
        if draw_round is None or nums is None or bonus is None:
            raise ValueError(
                "새 회차 원장 갱신을 위해 draw_round, nums(6개), bonus를 입력해 주세요. "
                "(이미 원장 갱신이 끝난 상태라면 skip_master_update=True로 호출하세요.)"
            )
        update_master_ledger(draw_round, nums, bonus)
    else:
        print("[건너뜀] 원장 갱신 생략 (skip_master_update=True)")

    update_all_notes()
    sync_notes_to_p1121()
    run_prediction()

    print("\n" + "=" * 72)
    print("전체 파이프라인 실행 완료!")
    print("=" * 72)


if __name__ == "__main__":
    # 사용 예시 1: 새 회차(예: 1251회) 원장 입력부터 예측까지 한 번에 실행
    # run_weekly_pipeline(
    #     draw_round=1251,
    #     nums=[1, 2, 3, 4, 5, 6],
    #     bonus=7,
    #     skip_master_update=False,
    # )

    # 사용 예시 2: 이미 원장(1250회까지)이 반영된 상태에서 02~10 갱신 -> 복사 -> 1251회 예측 실행
    run_weekly_pipeline(skip_master_update=True)