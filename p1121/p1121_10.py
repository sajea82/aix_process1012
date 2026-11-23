from itertools import combinations
from pathlib import Path

from p1121_02 import load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers
from p1121_05 import passes_custom_conditions

# 1251회 임시 구간표 (노트 기준)
TEMP_BAND_1251: dict[int, int] = {
    1: 1, 5: 1, 18: 1, 23: 1, 27: 1, 28: 1,
    2: 2, 11: 2, 16: 2, 25: 2, 34: 2, 35: 2,
    36: 3, 38: 3, 42: 3,
    8: 4, 14: 4, 21: 4, 22: 4, 45: 4,
    24: 5,
    4: 6, 32: 6,
    13: 7, 26: 7,
    9: 8, 43: 8, 44: 8,
    10: 9, 31: 9, 41: 9,
    7: 10,
    19: 11, 20: 11,
    33: 12,
    37: 14, 40: 14,
    12: 15, 29: 15,
    6: 16, 15: 16, 39: 16,
    3: 21,
    30: 23,
    17: 25,
}

GROUP_16_NUMS = {6, 15, 39}


def get_major_zone(num: int) -> int:
    """1구간(1), 2구간(2~5), 3구간(6~25) 반환"""
    band = TEMP_BAND_1251.get(num, 99)
    if band == 1:
        return 1
    if 2 <= band <= 5:
        return 2
    return 3


def zone_counts(combo: tuple[int, ...]) -> tuple[int, int, int]:
    """(1구간 개수, 2구간 개수, 3구간 개수)"""
    z1 = sum(1 for n in combo if get_major_zone(n) == 1)
    z2 = sum(1 for n in combo if get_major_zone(n) == 2)
    z3 = sum(1 for n in combo if get_major_zone(n) == 3)
    return z1, z2, z3


def zone_priority_score(combo: tuple[int, ...], scores: dict[int, float]) -> float:
    """3구간 비중에 가점을 주고, 기본 번호 점수 합계를 결합"""
    _, z2, z3 = zone_counts(combo)
    base_score = sum(scores[n] for n in combo)
    # 3구간 비중을 가장 높게 우대하고, 2구간도 보조 가점
    zone_weight = (z3 * 2.5) + (z2 * 0.8)
    return round(base_score + zone_weight, 4)


def run_temp_1251_custom(target_round: int = 1250, pool_size: int = 18, top_k: int = 10):
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

    # 1차: 1·2·3구간 각각 최대 3수 제한
    cap_filtered = [
        c for c in survived
        if all(cnt <= 3 for cnt in zone_counts(c))
    ]

    # 2차: 16구간(6, 15, 39) 2수 포함 우선 적용
    g16_exact2 = [c for c in cap_filtered if len(set(c) & GROUP_16_NUMS) == 2]
    if len(g16_exact2) >= top_k:
        final_candidates = g16_exact2
        mode_msg = "1·2·3구간 각 최대 3수 + 16구간 2수 포함 + 3구간 가중"
    else:
        g16_atleast1 = [c for c in cap_filtered if len(set(c) & GROUP_16_NUMS) >= 1]
        final_candidates = g16_atleast1 if g16_atleast1 else cap_filtered
        mode_msg = (
            f"1·2·3구간 각 최대 3수 + 16구간 2수 조합({len(g16_exact2)}개) 부족으로 "
            f"16구간 1수+ 포함 보완 + 3구간 가중"
        )

    ranked_combos = sorted(
        final_candidates,
        key=lambda c: (zone_priority_score(c, scores), sum(scores[n] for n in c), c),
        reverse=True,
    )

    print(f"[1251회 임시 맞춤 추출 | 기존 필터 통과 {len(survived):,}개 -> 조건 후보 {len(final_candidates):,}개]")
    print(f"- 적용 기준: {mode_msg}")
    print("-" * 82)
    for idx, c in enumerate(ranked_combos[:top_k], start=1):
        z1, z2, z3 = zone_counts(c)
        g16_hits = sorted(set(c) & GROUP_16_NUMS)
        base_s = round(sum(scores[n] for n in c), 2)
        tot_s = zone_priority_score(c, scores)
        print(
            f"{idx:2d}위 | {list(c)} | 구간(1:2:3)={z1}:{z2}:{z3} "
            f"| 16구간={g16_hits} | 기본점수:{base_s:5.2f} | 가중점수:{tot_s:5.2f}"
        )


if __name__ == "__main__":
    run_temp_1251_custom(target_round=1250, pool_size=18, top_k=10)