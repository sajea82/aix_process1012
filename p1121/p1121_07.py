from collections import Counter
from itertools import combinations
from pathlib import Path
from p1121_02 import load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers, slice_notes_for_round
from p1121_05 import passes_custom_conditions


def evaluate_survived_best_matches(
    start_prev_round: int = 1150,
    end_prev_round: int = 1249,
    pool_sizes: tuple[int, ...] = (18, 20),
    top_k_list: tuple[int, ...] = (10, 20),
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    full_notes = load_notes_from_dir()

    for ps in pool_sizes:
        best_match_counter = Counter()
        top_k_best_counters = {k: Counter() for k in top_k_list}
        empty_survived_rounds = 0
        total_rounds = 0

        for prev_rnd in range(start_prev_round, end_prev_round + 1):
            target_rnd = prev_rnd + 1
            actual_win = win_map.get(target_rnd)
            prev_win = win_map.get(prev_rnd, set())
            if not actual_win:
                continue

            total_rounds += 1
            notes_at_t = slice_notes_for_round(full_notes, prev_rnd)
            scores = score_numbers_from_notes(notes_at_t, target_round=prev_rnd)
            ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
            pool = sorted(ranked_nums[:ps])

            survived = [
                c for c in combinations(pool, 6)
                if passes_custom_conditions(c, prev_win_nums=prev_win)
            ]

            if not survived:
                empty_survived_rounds += 1
                best_match_counter[0] += 1
                for k in top_k_list:
                    top_k_best_counters[k][0] += 1
                continue

            # 전체 생존 조합 중 최고 일치 개수
            best_hit = max(len(set(c) & actual_win) for c in survived)
            best_match_counter[best_hit] += 1

            # 점수 합계 상위 K개 생존 조합 중 최고 일치 개수
            survived_sorted = sorted(
                survived,
                key=lambda c: round(sum(scores[n] for n in c), 3),
                reverse=True,
            )
            for k in top_k_list:
                top_slice = survived_sorted[:k]
                k_best = max(len(set(c) & actual_win) for c in top_slice)
                top_k_best_counters[k][k_best] += 1

        ge3 = sum(v for m, v in best_match_counter.items() if m >= 3)
        ge4 = sum(v for m, v in best_match_counter.items() if m >= 4)
        ge5 = sum(v for m, v in best_match_counter.items() if m >= 5)
        eq6 = best_match_counter[6]

        print(f"\n{'=' * 74}")
        print(f"[생존 조합 내 회차별 최고 일치 수 집계 | pool_size={ps} | {start_prev_round + 1}~{end_prev_round + 1}회 (총 {total_rounds}회)]")
        print(f"{'=' * 74}")
        print(
            f"▶ 전체 생존 조합 기준: "
            f"3개+ {ge3}회 ({ge3 / max(total_rounds, 1) * 100:.1f}%) | "
            f"4개+ {ge4}회 ({ge4 / max(total_rounds, 1) * 100:.1f}%) | "
            f"5개+ {ge5}회 | 6개 {eq6}회"
        )
        print(
            f"   일치수 분포(0~6개): "
            + ", ".join(f"{m}개:{best_match_counter[m]}회" for m in range(7))
        )
        if empty_survived_rounds:
            print(f"   (참고: 통과 조합 0개인 회차 {empty_survived_rounds}회)")

        for k in top_k_list:
            cnt_map = top_k_best_counters[k]
            k_ge3 = sum(v for m, v in cnt_map.items() if m >= 3)
            k_ge4 = sum(v for m, v in cnt_map.items() if m >= 4)
            k_ge5 = sum(v for m, v in cnt_map.items() if m >= 5)
            k_eq6 = cnt_map[6]
            print(
                f"▶ 점수 상위 {k:2d}개 조합 기준: "
                f"3개+ {k_ge3}회 ({k_ge3 / max(total_rounds, 1) * 100:.1f}%) | "
                f"4개+ {k_ge4}회 ({k_ge4 / max(total_rounds, 1) * 100:.1f}%) | "
                f"5개+ {k_ge5}회 | 6개 {k_eq6}회"
            )


if __name__ == "__main__":
    evaluate_survived_best_matches(
        start_prev_round=1150,
        end_prev_round=1249,
        pool_sizes=(18, 20),
        top_k_list=(10, 20),
    )