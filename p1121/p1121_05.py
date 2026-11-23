from collections import Counter
from itertools import combinations
from pathlib import Path
from p1121_02 import _get_gung, load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers


def passes_custom_conditions(
    combo: tuple[int, ...],
    prev_win_nums: set[int] | None = None,
    fixed_nums: set[int] | None = None,
    excluded_nums: set[int] | None = None,
    sum_range: tuple[int, int] = (85, 185),
    max_prev_overlap: int = 2,
) -> bool:
    """
    6개 번호 조합에 대해 [고정수/제외수 -> 전화차 -> 쓰레기 조합 -> 노트 균형]
    순으로 통과 여부를 판정합니다.
    """
    c_set = set(combo)

    # 1. 고정수 / 제외수 필터
    if fixed_nums and not fixed_nums.issubset(c_set):
        return False
    if excluded_nums and not c_set.isdisjoint(excluded_nums):
        return False

    # 2. 전화차(이월수) 필터: 직전 회차 당첨번호와 0~2개 중복만 허용
    if prev_win_nums:
        if len(c_set & prev_win_nums) > max_prev_overlap:
            return False

    # 3. 쓰레기 조합 필터
    # (3-1) 총합 범위
    total_sum = sum(combo)
    if not (sum_range[0] <= total_sum <= sum_range[1]):
        return False

    # (3-2) 홀짝 비율 (전홀 6:0, 전짝 0:6 제외)
    odd_cnt = sum(1 for n in combo if n % 2 == 1)
    if odd_cnt == 0 or odd_cnt == 6:
        return False

    # (3-3) 고저 비율 (1~22 저번호 vs 23~45 고번호, 6:0 / 0:6 제외)
    low_cnt = sum(1 for n in combo if n <= 22)
    if low_cnt == 0 or low_cnt == 6:
        return False

    # (3-4) 연속번호 쌍 개수 (최대 2쌍까지 허용, 3연속 쌍 이상 제외)
    sorted_c = sorted(combo)
    consec_pairs = sum(1 for i in range(5) if sorted_c[i + 1] - sorted_c[i] == 1)
    if consec_pairs >= 3:
        return False

    # (3-5) 동일 끝수 개수 (같은 끝수 3개 이상 제외)
    end_counts = Counter(n % 10 for n in combo)
    if max(end_counts.values()) >= 3:
        return False

    # 4. 노트 균형 필터 (궁도·로또용지 가로/세로 편중 방지)
    # (4-1) 최소 3개 이상의 궁도에 분산
    gungs = {_get_gung(n) for n in combo}
    if len(gungs) < 3:
        return False

    # (4-2) 로또용지 세로(1~7구) 및 가로(1~7행) 최소 3개 라인 이상 분산
    cols = {(n - 1) % 7 + 1 for n in combo}
    rows = {(n - 1) // 7 + 1 for n in combo}
    if len(cols) < 3 or len(rows) < 3:
        return False

    return True


def generate_filtered_combinations(
    target_round: int = 1250,
    pool_size: int = 18,
    fixed_nums: set[int] | None = None,
    excluded_nums: set[int] | None = None,
    top_k_output: int = 15,
):
    base_dir = Path(__file__).resolve().parent
    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    prev_win = win_map.get(target_round, set())

    notes = load_notes_from_dir()
    scores = score_numbers_from_notes(notes, target_round=target_round)
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))

    # 후보군 구성 (고정수가 있다면 후보군에 강제 포함, 제외수는 후보군에서 제외)
    fixed_set = set(fixed_nums or set())
    excl_set = set(excluded_nums or set())

    pool = sorted(fixed_set)
    for n, _ in ranked:
        if n in excl_set or n in fixed_set:
            continue
        pool.append(n)
        if len(pool) >= pool_size:
            break
    pool = sorted(pool)

    raw_combos = list(combinations(pool, 6))
    survived = [
        c for c in raw_combos
        if passes_custom_conditions(
            c,
            prev_win_nums=prev_win,
            fixed_nums=fixed_set,
            excluded_nums=excl_set,
        )
    ]

    # 생존 조합을 번호 점수 합계 높은 순으로 정렬
    survived_scored = sorted(
        survived,
        key=lambda c: round(sum(scores[n] for n in c), 3),
        reverse=True,
    )

    survival_pct = (len(survived) / len(raw_combos) * 100) if raw_combos else 0.0

    print(f"[{target_round + 1}회 예측 조합 필터링 결과 | pool_size={pool_size}]")
    print(f"- 직전({target_round}회) 당첨번호: {sorted(prev_win)}")
    print(f"- 선별 후보군 ({len(pool)}개): {pool}")
    print(f"- 원조합: {len(raw_combos):,}개 → 최종 통과: {len(survived):,}개 (생존율 {survival_pct:.2f}%)")
    print("-" * 72)
    print(f"점수 합계 상위 {min(top_k_output, len(survived_scored))}개 조합:")
    for idx, combo in enumerate(survived_scored[:top_k_output], start=1):
        c_score = round(sum(scores[n] for n in combo), 2)
        c_sum = sum(combo)
        print(f"  {idx:2d}위 | {list(combo)} | 점수합: {c_score:5.2f} | 번호합: {c_sum:3d}")

    return survived_scored


if __name__ == "__main__":
    # 예시: 1250회 기준 1251회 예측 (고정수/제외수 없이 실행, 필요 시 set({3, 23}) 등으로 지정)
    generate_filtered_combinations(
        target_round=1250,
        pool_size=18,
        fixed_nums=set(),
        excluded_nums=set(),
        top_k_output=15,
    )