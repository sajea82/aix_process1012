from collections import Counter
from pathlib import Path
import re
import pandas as pd

# ---------------------------------------------------------
# 1. 가중치 설정 (백테스트 시 이 딕셔너리만 조정해 튜닝)
# ---------------------------------------------------------
NOTE_WEIGHTS = {
    "absent_sweet_spot": 2.4,     # 장기미출수 5~14회차 (튜닝 반영)
    "absent_super_cold": 1.8,     # 장기미출수 15~22회차 (튜닝 반영)
    "absent_extreme_cold": -1.0,  # 장기미출수 25회차 이상 감점
    "ending_cold": 1.6,           # 최근 저출현 끝수 가점 (튜닝 반영)
    "ending_hot": -0.7,           # 최근 과열 끝수 감점 (튜닝 반영)
    "gung_dormant": 1.5,          # 최근 휴면 궁도 가점
    "gung_crowded": -0.7,         # 직전 과밀 궁도 감점 (튜닝 반영)
    "cost_core": 1.0,             # 13/20 코스트 중앙 핵심 구간
    "dist45_reversion": 1.5,      # 최근 10회 저출현 회귀 (튜닝 반영)
    "dist45_overheated": -1.5,    # 최근 10회 과다 출현 감점 (튜닝 반영)
    "double_num_bonus": 0.5,      # 쌍수(11,22,33,44) 공백 보정 (튜닝 반영)
    "minus_overlap_2plus": 2.5,   # 마이너스표 2중 이상 교차 적중 (튜닝 반영)
    "minus_overlap_1": 1.0,       # 마이너스표 단일 매칭
    "paper_line_dormant": 0.6,    # 로또용지 가로/세로 공백 라인 보정 (튜닝 반영)
}

NOTE_FILE_MAP = {
    "absent": "02_장기미출수.xlsx",
    "ending": "03_끝수별_배치표.xlsx",
    "gung": "04_궁도별_배치표.xlsx",
    "cost13": "05_13코스트_배치표.xlsx",
    "cost20": "06_20코스트_배치표.xlsx",
    "dist45": "07_1부터45_분포도.xlsx",
    "minus": "08_마이너스표.xlsx",
    "col": "09_로또용지_세로분포.xlsx",
    "row": "10_로또용지_가로분포.xlsx",
}


def load_notes_from_dir(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """p1121/data/ 폴더의 9개 노트 엑셀을 결측값 0 처리하여 로드합니다."""
    base_dir = Path(__file__).resolve().parent
    target_dir = data_dir or (base_dir / "data")
    if not target_dir.exists():
        fallback_dir = base_dir.parent / "p1120" / "update"
        if fallback_dir.exists():
            target_dir = fallback_dir

    notes: dict[str, pd.DataFrame] = {}
    for key, filename in NOTE_FILE_MAP.items():
        fpath = target_dir / filename
        if fpath.exists():
            df = pd.read_excel(fpath).fillna(0)
            notes[key] = df
        else:
            print(f"[경고] 파일 없음 ({key}): {fpath}")
            notes[key] = pd.DataFrame()
    return notes


def _get_df(notes: dict[str, pd.DataFrame], *keys: str) -> pd.DataFrame | None:
    """여러 후보 키 중 실제로 로드된 비어 있지 않은 DataFrame을 반환합니다."""
    for k in keys:
        df = notes.get(k)
        if df is not None and not df.empty:
            return df
    return None


def _extract_nums(cell_val) -> list[int]:
    """셀 값에서 '12(보)', '12*', '12' 등의 형태를 1~45 정수 리스트로 안전 추출"""
    if cell_val is None or cell_val == 0 or str(cell_val).strip() in ("", "0", "nan", "None"):
        return []
    found = re.findall(r"\d+", str(cell_val))
    return [int(x) for x in found if 1 <= int(x) <= 45]


def _get_gung(n: int) -> int:
    """1~45 번호의 9궁(낙서 구궁수) 매핑"""
    gung_map = {
        1: [1, 10, 19, 28, 37],
        2: [2, 11, 20, 29, 38],
        3: [3, 12, 21, 30, 39],
        4: [4, 13, 22, 31, 40],
        5: [5, 14, 23, 32, 41],
        6: [6, 15, 24, 33, 42],
        7: [7, 16, 25, 34, 43],
        8: [8, 17, 26, 35, 44],
        9: [9, 18, 27, 36, 45],
    }
    for g, nums in gung_map.items():
        if n in nums:
            return g
    return (n - 1) % 9 + 1


def score_numbers_from_notes(
    notes: dict[str, pd.DataFrame],
    target_round: int = 1250,
    weights: dict[str, float] | None = None,
) -> dict[int, float]:
    """
    p1121/data/에서 로드된 9개 노트 DataFrame을 종합하여
    1~45 각 번호의 출현 기대 점수를 반환합니다.
    """
    w = {**NOTE_WEIGHTS, **(weights or {})}
    scores: dict[int, float] = {n: 0.0 for n in range(1, 46)}

    # -----------------------------------------------------
    # [1] 02_장기미출수 (absent: 1251행 또는 마지막 행 기준 미출 기간)
    # -----------------------------------------------------
    df_absent = _get_df(notes, "absent")
    if df_absent is not None:
        last_row = df_absent.iloc[-1]
        numeric_cols = [c for c in df_absent.columns if str(c).isdigit() and 1 <= int(c) <= 45]
        if len(numeric_cols) == 45:
            for col in numeric_cols:
                num = int(col)
                miss_cnt = int(float(last_row[col]))
                if 5 <= miss_cnt <= 14:
                    scores[num] += w["absent_sweet_spot"]
                elif 15 <= miss_cnt <= 22:
                    scores[num] += w["absent_super_cold"]
                elif miss_cnt >= 25:
                    scores[num] += w["absent_extreme_cold"]
        else:
            for col_idx, val in enumerate(last_row.values[1:], start=1):
                for num in _extract_nums(val):
                    if 5 <= col_idx <= 14:
                        scores[num] += w["absent_sweet_spot"]
                    elif 15 <= col_idx <= 22:
                        scores[num] += w["absent_super_cold"]
                    elif col_idx >= 25:
                        scores[num] += w["absent_extreme_cold"]

    # -----------------------------------------------------
    # [2] 07_1부터45_분포도 (최근 10회 출현 빈도 & 쌍수 보정)
    # -----------------------------------------------------
    df_dist = _get_df(notes, "dist45", "dist")
    recent_counts = Counter()
    if df_dist is not None:
        recent_df = df_dist.tail(10)
        for _, r in recent_df.iterrows():
            for val in r.values[1:]:
                for num in _extract_nums(val):
                    recent_counts[num] += 1

        for n in range(1, 46):
            cnt = recent_counts[n]
            if cnt <= 1:
                scores[n] += w["dist45_reversion"]
            elif cnt >= 4:
                scores[n] += w["dist45_overheated"]

        recent_4_nums = set()
        for _, r in df_dist.tail(4).iterrows():
            for val in r.values[1:]:
                recent_4_nums.update(_extract_nums(val))
        for dn in (11, 22, 33, 44):
            if dn not in recent_4_nums:
                scores[dn] += w["double_num_bonus"]

    # -----------------------------------------------------
    # [3] 03_끝수별_배치표 (최근 5회 저출현/과열 끝수 판별)
    # -----------------------------------------------------
    df_ending = _get_df(notes, "ending")
    if df_ending is not None:
        end_counts = Counter()
        for _, r in df_ending.tail(5).iterrows():
            for val in r.values[1:]:
                for num in _extract_nums(val):
                    end_counts[num % 10] += 1

        for n in range(1, 46):
            ec = end_counts[n % 10]
            if ec <= 2:
                scores[n] += w["ending_cold"]
            elif ec >= 6:
                scores[n] += w["ending_hot"]

    # -----------------------------------------------------
    # [4] 04_궁도별_배치표 (최근 3회 휴면 궁도 / 직전 과밀 궁도)
    # -----------------------------------------------------
    df_gung = _get_df(notes, "gung")
    if df_gung is not None:
        gung_recent3 = Counter()
        gung_last1 = Counter()
        for _, r in df_gung.tail(3).iterrows():
            for val in r.values[1:]:
                for num in _extract_nums(val):
                    gung_recent3[_get_gung(num)] += 1
        for val in df_gung.iloc[-1].values[1:]:
            for num in _extract_nums(val):
                gung_last1[_get_gung(num)] += 1

        for n in range(1, 46):
            g = _get_gung(n)
            if gung_recent3[g] == 0:
                scores[n] += w["gung_dormant"]
            elif gung_last1[g] >= 3:
                scores[n] += w["gung_crowded"]

    # -----------------------------------------------------
    # [5] 05_13코스트 & 06_20코스트 (중앙 핵심 구간 유입 번호)
    # -----------------------------------------------------
    for key, core_cols in [
        ("cost13", ["D", "E", "F", "G", "H", "I", "J"]),
        ("cost20", ["F", "G", "H", "I", "J", "K", "L", "M", "N"]),
    ]:
        df_cost = _get_df(notes, key)
        if df_cost is not None:
            last_row = df_cost.iloc[-1]
            for col in df_cost.columns:
                if any(c in str(col).upper() for c in core_cols):
                    for num in _extract_nums(last_row[col]):
                        scores[num] += w["cost_core"] * 0.5

    # -----------------------------------------------------
    # [6] 08_마이너스표 (직전 회차 7개 번호 기준 -20/-30/-40 교차 후보)
    # -----------------------------------------------------
    df_minus = _get_df(notes, "minus")
    if df_minus is not None:
        last_nums = []
        for val in df_minus.iloc[-1].values[1:]:
            last_nums.extend(_extract_nums(val))
        base_7 = list(dict.fromkeys(last_nums))[:7]

        minus_candidates = Counter()
        for b in base_7:
            for offset in (20, 30, 40):
                cand = b - offset
                if cand <= 0:
                    cand += 45
                if 1 <= cand <= 45:
                    minus_candidates[cand] += 1

        for cand, hit_cnt in minus_candidates.items():
            if hit_cnt >= 2:
                scores[cand] += w["minus_overlap_2plus"]
            elif hit_cnt == 1:
                scores[cand] += w["minus_overlap_1"]

    # -----------------------------------------------------
    # [7] 09_로또용지_세로분포 & 10_로또용지_가로분포 (공백 라인 보정)
    # -----------------------------------------------------
    df_col = _get_df(notes, "col", "vertical")
    if df_col is not None:
        col_recent2 = Counter()
        for _, r in df_col.tail(2).iterrows():
            for val in r.values[1:]:
                for num in _extract_nums(val):
                    col_recent2[(num - 1) % 7 + 1] += 1
        for n in range(1, 46):
            if col_recent2[(n - 1) % 7 + 1] == 0:
                scores[n] += w["paper_line_dormant"]

    df_row = _get_df(notes, "row", "horizontal")
    if df_row is not None:
        row_recent2 = Counter()
        for _, r in df_row.tail(2).iterrows():
            for val in r.values[1:]:
                for num in _extract_nums(val):
                    row_recent2[(num - 1) // 7 + 1] += 1
        for n in range(1, 46):
            if row_recent2[(n - 1) // 7 + 1] == 0:
                scores[n] += w["paper_line_dormant"]

    return {n: round(s, 3) for n, s in scores.items()}


if __name__ == "__main__":
    notes = load_notes_from_dir()
    scores = score_numbers_from_notes(notes, target_round=1250)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("상위 20개 후보군:", [n for n, _ in ranked[:20]])
    print("최대점수:", ranked[0][1], "/ 최소점수:", ranked[-1][1])