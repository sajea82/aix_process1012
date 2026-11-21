from collections import Counter
from itertools import combinations
from pathlib import Path
from p1121_02 import _get_gung, load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers, slice_notes_for_round
from p1121_05 import passes_custom_conditions


def diagnose_filter_rejection(
    combo: tuple[int, ...],
    prev_win_nums: set[int],
    sum_range: tuple[int, int] = (85, 185),
    max_prev_overlap: int = 2,
) -> list[str]:
    """실제 당첨 조합이 필터에서 탈락한 경우 구체적인 탈락 사유를 반환합니다."""
    reasons = []
    c_set = set(combo)

    if prev_win_nums and len(c_set & prev_win_nums) > max_prev_overlap:
        reasons.append(f"전화차초과({len(c_set & prev_win_nums)}개)")

    total_sum = sum(combo)
    if not (sum_range[0] <= total_sum <= sum_range[1]):
        reasons.append(f"총합범위외({total_sum})")

    odd_cnt = sum(1 for n in combo if n % 2 == 1)
    if odd_cnt == 0 or odd_cnt == 6:
        reasons.append(f"홀짝극단({odd_cnt}:{6 - odd_cnt})")

    low_cnt = sum(1 for n in combo if n <= 22)
    if low_cnt == 0 or low_cnt == 6:
        reasons.append(f"고저극단({low_cnt}:{6 - low_cnt})")

    sorted_c = sorted(combo)
    consec_pairs = sum(1 for i in range(5) if sorted_c[i + 1] - sorted_c[i] == 1)
    if consec_pairs >= 3:
        reasons.append(f"연속번호과다({consec_pairs}쌍)")

    if max(Counter(n % 10 for n in combo).values()) >= 3:
        reasons.append("동일끝수3개+")

    if len({_get_gung(n) for n in combo}) < 3:
        reasons.append("궁도분산부족(<3)")

    cols = {(n - 1) % 7 + 1 for n in combo}
    rows = {(n - 1) // 7 + 1 for n in combo}
    if len(cols) < 3 or len(rows) < 3:
        reasons.append("용지가로세로부족(<3)")

    return reasons


def backtest_filter_preservation(
    start_prev_round: int = 1150,
    end_prev_round: int = 1249,
    pool_sizes: tuple[int, ...] = (18, 20),
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    full_notes = load_notes_from_dir()

    # [파트 1] 실제 당첨번호 자체의 필터 통과율 및 탈락 사유 집계
    actual_pass_cnt = 0
    actual_total = 0
    reject_reason_counter = Counter()

    for prev_rnd in range(start_prev_round, end_prev_round + 1):
        target_rnd = prev_rnd + 1
        actual_win = win_map.get(target_rnd)
        prev_win = win_map.get(prev_rnd, set())
        if not actual_win:
            continue

        actual_total += 1
        win_tuple = tuple(sorted(actual_win))
        if passes_custom_conditions(win_tuple, prev_win_nums=prev_win):
            actual_pass_cnt += 1
        else:
            for r in diagnose_filter_rejection(win_tuple, prev_win):
                reject_reason_counter[r.split("(")[0]] += 1

    print(f"[1. 실제 1등 당첨번호 필터 보존율 ({start_prev_round + 1}회 ~ {end_prev_round + 1}회)]")
    print(f"- 통과: {actual_pass_cnt}/{actual_total}회 ({actual_pass_cnt / max(actual_total, 1) * 100:.1f}%)")
    if reject_reason_counter:
        print(f"- 탈락 사유별 건수: {dict(reject_reason_counter)}")
    print("-" * 74)

    # [파트 2] 후보군(pool_size) 내 6개·5개·4개 적중 조합의 필터 생존 검증
    print("[2. 후보군(pool_size) 내 고액 적중(6개·5개·4개) 보존율 및 압축률]")
    for ps in pool_sizes:
        raw_total_sum = 0
        surv_total_sum = 0

        hit6_raw_rounds = 0
        hit6_surv_rounds = 0
        hit5_raw_rounds = 0
        hit5_surv_rounds = 0
        hit4_raw_rounds = 0
        hit4_surv_rounds = 0

        for prev_rnd in range(start_prev_round, end_prev_round + 1):
            target_rnd = prev_rnd + 1
            actual_win = win_map.get(target_rnd)
            prev_win = win_map.get(prev_rnd, set())
            if not actual_win:
                continue

            notes_at_t = slice_notes_for_round(full_notes, prev_rnd)
            scores = score_numbers_from_notes(notes_at_t, target_round=prev_rnd)
            ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
            pool = sorted(ranked_nums[:ps])

            raw_combos = list(combinations(pool, 6))
            surv_combos = [
                c for c in raw_combos
                if passes_custom_conditions(c, prev_win_nums=prev_win)
            ]

            raw_total_sum += len(raw_combos)
            surv_total_sum += len(surv_combos)

            pool_hit = len(set(pool) & actual_win)
            if pool_hit >= 6:
                hit6_raw_rounds += 1
                if any(len(set(c) & actual_win) == 6 for c in surv_combos):
                    hit6_surv_rounds += 1
            if pool_hit >= 5:
                hit5_raw_rounds += 1
                if any(len(set(c) & actual_win) >= 5 for c in surv_combos):
                    hit5_surv_rounds += 1
            if pool_hit >= 4:
                hit4_raw_rounds += 1
                if any(len(set(c) & actual_win) >= 4 for c in surv_combos):
                    hit4_surv_rounds += 1

        surv_rate = (surv_total_sum / max(raw_total_sum, 1)) * 100
        print(f"▶ pool_size={ps:2d} | 평균 생존율: {surv_rate:5.2f}% ({surv_total_sum // actual_total:,} / {raw_total_sum // actual_total:,}개)")
        print(f"   - 6개 일치 보존: {hit6_surv_rounds}/{hit6_raw_rounds}회")
        print(f"   - 5개+ 일치 보존: {hit5_surv_rounds}/{hit5_raw_rounds}회")
        print(f"   - 4개+ 일치 보존: {hit4_surv_rounds}/{hit4_raw_rounds}회")


if __name__ == "__main__":
    backtest_filter_preservation(1150, 1249, (18, 20))