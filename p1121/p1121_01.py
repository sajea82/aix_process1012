from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_FILES = {
    "absent": DATA_DIR / "02_장기미출수.xlsx",
    "ending": DATA_DIR / "03_끝수별_배치표.xlsx",
    "gung": DATA_DIR / "04_궁도별_배치표.xlsx",
    "cost13": DATA_DIR / "05_13코스트_배치표.xlsx",
    "cost20": DATA_DIR / "06_20코스트_배치표.xlsx",
    "dist45": DATA_DIR / "07_1부터45_분포도.xlsx",
    "minus": DATA_DIR / "08_마이너스표.xlsx",
    "paper_v": DATA_DIR / "09_로또용지_세로분포.xlsx",
    "paper_h": DATA_DIR / "10_로또용지_가로분포.xlsx",
}


def load_p1121_data() -> dict[str, pd.DataFrame]:
    """p1121/data/ 폴더의 최신화 엑셀 자료들을 불러오고 결측치는 0으로 채웁니다."""
    loaded: dict[str, pd.DataFrame] = {}
    for key, path in DATA_FILES.items():
        if path.exists():
            loaded[key] = pd.read_excel(path).fillna(0)
        else:
            loaded[key] = pd.DataFrame().fillna(0)
    return loaded


def score_numbers_from_notes(datasets: dict[str, pd.DataFrame]) -> dict[int, float]:
    """
    최신화된 02~10 자료를 바탕으로 1~45 번호별 점수를 계산하는 자리입니다.
    원하시는 노트별 조건코드를 여기에 반영하세요.
    """
    scores: dict[int, float] = {n: 0.0 for n in range(1, 46)}

    # 예시: 07_1부터45_분포도에서 최근 출현이나 특정 기준을 점수로 반영할 때 활용
    _ = datasets.get("dist45")
    return scores


def passes_custom_conditions(
    combo: tuple[int, ...],
    datasets: dict[str, pd.DataFrame],
) -> bool:
    """
    후보 조합(6개 번호)이 전화차 / 노트 기준 / 쓰레기 조합 조건을 통과하는지 판별합니다.
    원하시는 조건코드를 여기에 입력하세요.
    """
    _ = (combo, datasets)
    return True


def run_p1121_pipeline() -> dict[str, pd.DataFrame]:
    """데이터 로드 및 조건 적용 진입점입니다."""
    datasets = load_p1121_data()
    scores = score_numbers_from_notes(datasets)

    latest_rounds = {}
    for name, df in datasets.items():
        if not df.empty:
            first_col = df.columns[0]
            latest_rounds[name] = df[first_col].iloc[-1]

    print(f"로드된 시트 수: {len(datasets)} / 번호 점수 계산 완료(1~45, 최대점수={max(scores.values()):.2f})")
    print("각 파일 마지막 행 기준값:", latest_rounds)
    return datasets


if __name__ == "__main__":
    run_p1121_pipeline()