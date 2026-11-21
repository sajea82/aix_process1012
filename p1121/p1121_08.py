from itertools import combinations
from pathlib import Path
from p1121_02 import load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers, slice_notes_for_round
from p1121_05 import passes_custom_conditions


def pick_top_score_combos(
    survived: list[tuple[int, ...]],
    scores: dict[int, float],
    k: int = 15,
) -> list[tuple[int, ...]]:
    ranked = sorted(
        survived,
        key=lambda c: (round(sum(scores[n] for n in c), 4), c),
        reverse=True,
    )
    return ranked[:k]


def pick_diverse_combos(
    survived: list[tuple[int, ...]],
    scores: dict[int, float],
    k: int = 15,
    overlap_penalty: float = 1.2,
) -> list[tuple[int, ...]]:
    """
    점수 합계가 높으면서도 이미 뽑힌 조합들과 번호 겹침이 적은 조합을
    탐욕적(Greedy)으로 선택해 다양성을 확보합니다.
    """
    if not survived or k <= 0:
        return []

    scored_pool = sorted(
        survived,
        key=lambda c: (round(sum(scores[n] for n in c), 4), c),
        reverse=True,
    )
    # 상위 후보군 일부(예: 상위 500개) 내에서 다양성을 극대화
    candidate_pool = scored_pool[: min(len(scored_pool), 500)]

    picked: list[tuple[int, ...]] = [candidate_pool[0]]
    picked_sets: list[set[int]] = [set(candidate_pool[0])]

    while len(picked) < min(k, len(candidate_pool)):
        best_combo = None
        best_adj_score = float("-inf")

        for combo in candidate_pool:
            if combo in picked:
                continue
            c_set = set(combo)
            base_score = sum(scores[n] for n in combo)
            max_overlap = max(len(c_set & p_set) for p_set in picked_sets)
            # 이미 뽑힌 조합과 겹치는 번호 수가 많을수록 감점
            adj_score = base_score - (max_overlap * overlap_penalty)
            if adj_score > best_adj_score:
                best_adj_score = adj_score
                best_combo = combo

        if best_combo is None:
            break
        picked.append(best_combo)
        picked_sets.append(set(best_combo))

    return picked


def compare_methods_for_round(
    target_round: int = 1250,
    pool_size: int = 18,
    k: int = 15,
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    prev_win = win_map.get(target_round, set())

    notes = load_notes_from_dir()
    scores = score_numbers_from_notes(notes, target_round=target_round)
    ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
    pool = sorted(ranked_nums[:pool_size])

    survived = [
        c for c in combinations(pool, 6)
        if passes_custom_conditions(c, prev_win_nums=prev_win)
    ]

    top_combos = pick_top_score_combos(survived, scores, k=k)
    div_combos = pick_diverse_combos(survived, scores, k=k)

    top_unique_nums = sorted({n for c in top_combos for n in c})
    div_unique_nums = sorted({n for c in div_combos for n in c})

    print(f"[{target_round + 1}회 예측 비교 | pool_size={pool_size} | 생존 {len(survived):,}개 | 상위 {k}개 기준]")
    print(f"- 점수상위 방식 사용 고유번호({len(top_unique_nums)}개): {top_unique_nums}")
    print(f"- 다양성우선 방식 사용 고유번호({len(div_unique_nums)}개): {div_unique_nums}")
    print("-" * 74)
    print("[A. 점수 상위순 TOP 10]")
    for idx, c in enumerate(top_combos[:10], start=1):
        print(f"  {idx:2d}위 | {list(c)} | 점수합: {sum(scores[n] for n in c):5.2f} | 합계: {sum(c):3d}")

    print("\n[B. 다양성 우선 TOP 10]")
    for idx, c in enumerate(div_combos[:10], start=1):
        print(f"  {idx:2d}위 | {list(c)} | 점수합: {sum(scores[n] for n in c):5.2f} | 합계: {sum(c):3d}")


def backtest_selection_methods(
    start_prev_round: int = 1150,
    end_prev_round: int = 1249,
    pool_size: int = 18,
    top_k_list: tuple[int, ...] = (10, 20),
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    full_notes = load_notes_from_dir()

    print(f"\n{'=' * 74}")
    print(f"[1151~1250회(100회차) 추출 방식 비교 | pool_size={pool_size}]")
    print(f"{'=' * 74}")

    for k in top_k_list:
        top_ge3 = top_ge4 = 0
        div_ge3 = div_ge4 = 0
        rounds = 0

        for prev_rnd in range(start_prev_round, end_prev_round + 1):
            actual_win = win_map.get(prev_rnd + 1)
            prev_win = win_map.get(prev_rnd, set())
            if not actual_win:
                continue
            rounds += 1

            notes_at_t = slice_notes_for_round(full_notes, prev_rnd)
            scores = score_numbers_from_notes(notes_at_t, target_round=prev_rnd)
            ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
            pool = sorted(ranked_nums[:pool_size])

            survived = [
                c for c in combinations(pool, 6)
                if passes_custom_conditions(c, prev_win_nums=prev_win)
            ]
            if not survived:
                continue

            top_pick = pick_top_score_combos(survived, scores, k=k)
            div_pick = pick_diverse_combos(survived, scores, k=k)

            top_best = max(len(set(c) & actual_win) for c in top_pick)
            div_best = max(len(set(c) & actual_win) for c in div_pick)

            if top_best >= 3:
                top_ge3 += 1
            if top_best >= 4:
                top_ge4 += 1
            if div_best >= 3:
                div_ge3 += 1
            if div_best >= 4:
                div_ge4 += 1

        print(f"▶ 상위 {k:2d}개 추출 기준 ({rounds}회차):")
        print(f"   - 점수상위순 : 3개+ {top_ge3:2d}회 ({top_ge3 / max(rounds, 1) * 100:4.1f}%) | 4개+ {top_ge4:2d}회")
        print(f"   - 다양성우선 : 3개+ {div_ge3:2d}회 ({div_ge3 / max(rounds, 1) * 100:4.1f}%) | 4개+ {div_ge4:2d}회")


if __name__ == "__main__":
    compare_methods_for_round(target_round=1250, pool_size=18, k=15)
    backtest_selection_methods(1150, 1249, pool_size=18, top_k_list=(10, 20))