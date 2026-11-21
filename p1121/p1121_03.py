from pathlib import Path
import pandas as pd
from p1121_02 import load_notes_from_dir, score_numbers_from_notes, _extract_nums


def load_winning_numbers(csv_path: Path) -> dict[int, set[int]]:
    """lotto.csv에서 회차별 실제 당첨번호 6개 집합을 로드합니다."""
    df = pd.read_csv(csv_path)
    win_map: dict[int, set[int]] = {}
    for _, row in df.iterrows():
        # 회차 컬럼명 자동 탐색 (round, 회차, draw 등)
        round_col = next((c for c in df.columns if str(c).lower() in ("round", "회차", "draw", "no")), df.columns[0])
        rnd = int(row[round_col])
        num_cols = [c for c in ["n1", "n2", "n3", "n4", "n5", "n6", "번호1", "번호2", "번호3", "번호4", "번호5", "번호6"] if c in df.columns]
        if len(num_cols) == 6:
            nums = {int(row[c]) for c in num_cols}
        else:
            # fallback: 행에서 앞쪽 1~45 숫자 6개 추출
            extracted = []
            for val in row.values[1:]:
                extracted.extend(_extract_nums(val))
                if len(extracted) >= 6:
                    break
            nums = set(extracted[:6])
        if len(nums) == 6:
            win_map[rnd] = nums
    return win_map


def slice_notes_for_round(notes: dict[str, pd.DataFrame], prev_round: int) -> dict[str, pd.DataFrame]:
    """
    prev_round(예: 1249) 시점까지의 데이터만 남기도록 각 노트 DataFrame을 슬라이싱합니다.
    (next_round = prev_round + 1 당첨번호 예측용)
    """
    sliced: dict[str, pd.DataFrame] = {}
    for key, df in notes.items():
        if df is None or df.empty:
            sliced[key] = df
            continue
        # 첫 번째 컬럼에 회차(예: 1250 또는 '1250회')가 있는 경우 회차 기준으로 필터링
        first_col = df.columns[0]
        parsed_rounds = pd.to_numeric(
            df[first_col].astype(str).str.replace("회", "", regex=False).str.strip(),
            errors="coerce",
        )
        if parsed_rounds.notna().sum() >= 100:
            sliced[key] = df[parsed_rounds <= prev_round].copy()
        else:
            # 회차 컬럼이 없거나 누적 행 구조인 경우 행 수 제한
            sliced[key] = df.iloc[:prev_round].copy()
    return sliced


def run_backtest(
    start_prev_round: int = 1150,
    end_prev_round: int = 1249,
    pool_sizes: tuple[int, ...] = (15, 18, 20, 24),
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    full_notes = load_notes_from_dir()

    stats = {
        ps: {"hits": [], "hit3": 0, "hit4": 0, "hit5": 0, "total": 0}
        for ps in pool_sizes
    }

    for prev_rnd in range(start_prev_round, end_prev_round + 1):
        target_rnd = prev_rnd + 1
        actual_win = win_map.get(target_rnd)
        if not actual_win:
            continue

        notes_at_t = slice_notes_for_round(full_notes, prev_rnd)
        scores = score_numbers_from_notes(notes_at_t, target_round=prev_rnd)
        ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]

        for ps in pool_sizes:
            pool = set(ranked_nums[:ps])
            hit_cnt = len(pool & actual_win)
            st = stats[ps]
            st["hits"].append(hit_cnt)
            st["total"] += 1
            if hit_cnt >= 3:
                st["hit3"] += 1
            if hit_cnt >= 4:
                st["hit4"] += 1
            if hit_cnt >= 5:
                st["hit5"] += 1

    print(f"[백테스트 결과: {start_prev_round + 1}회 ~ {end_prev_round + 1}회 (총 {stats[pool_sizes[0]]['total']}회차)]")
    print("-" * 72)
    for ps in pool_sizes:
        st = stats[ps]
        tot = max(st["total"], 1)
        avg_hit = sum(st["hits"]) / tot
        pct3 = st["hit3"] / tot * 100
        pct4 = st["hit4"] / tot * 100
        print(
            f"pool_size={ps:2d} | 평균적중: {avg_hit:.2f} | "
            f"3개+: {pct3:5.1f}% ({st['hit3']}/{tot}) | "
            f"4개+: {pct4:5.1f}% ({st['hit4']}/{tot}) | "
            f"5개+: {st['hit5']}회"
        )


if __name__ == "__main__":
    run_backtest(1150, 1249, (15, 18, 20, 24))