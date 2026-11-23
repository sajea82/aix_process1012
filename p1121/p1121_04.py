from pathlib import Path
from p1121_02 import NOTE_WEIGHTS, load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers, slice_notes_for_round


TUNED_WEIGHTS = {
    **NOTE_WEIGHTS,
    "absent_sweet_spot": 2.4,
    "absent_super_cold": 1.8,
    "absent_extreme_cold": -1.0,
    "ending_cold": 1.6,
    "ending_hot": -0.7,
    "gung_dormant": 1.5,
    "gung_crowded": -0.7,
    "cost_core": 1.0,
    "dist45_reversion": 1.5,
    "dist45_overheated": -1.5,
    "double_num_bonus": 0.5,
    "minus_overlap_2plus": 2.5,
    "minus_overlap_1": 1.0,
    "paper_line_dormant": 0.6,
}


def evaluate_weights(
    weights: dict[str, float],
    label: str,
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
        actual_win = win_map.get(prev_rnd + 1)
        if not actual_win:
            continue

        notes_at_t = slice_notes_for_round(full_notes, prev_rnd)
        scores = score_numbers_from_notes(notes_at_t, target_round=prev_rnd, weights=weights)
        ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]

        for ps in pool_sizes:
            hit_cnt = len(set(ranked_nums[:ps]) & actual_win)
            st = stats[ps]
            st["hits"].append(hit_cnt)
            st["total"] += 1
            if hit_cnt >= 3:
                st["hit3"] += 1
            if hit_cnt >= 4:
                st["hit4"] += 1
            if hit_cnt >= 5:
                st["hit5"] += 1

    print(f"\n[{label} | {start_prev_round + 1}회 ~ {end_prev_round + 1}회 (총 {stats[pool_sizes[0]]['total']}회차)]")
    print("-" * 74)
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
    evaluate_weights(NOTE_WEIGHTS, "기존 NOTE_WEIGHTS")
    evaluate_weights(TUNED_WEIGHTS, "튜닝 TUNED_WEIGHTS")