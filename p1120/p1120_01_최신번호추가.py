from itertools import combinations
import math
from pathlib import Path
import numpy as np
import pandas as pd

NUM_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
BINS = [0, 10, 20, 30, 40, 45]
ZONE_LABELS = ["1_10", "11_20", "21_30", "31_40", "41_45"]

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_lotto_csv(filename: str = "lotto.csv") -> pd.DataFrame:
    """
    p1120/data/lotto.csv를 불러와 컬럼명을 표준화하고
    결측치는 0으로 채운 뒤 회차 오름차순으로 정렬합니다.
    """
    csv_path = DATA_DIR / filename
    df = None
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        df = pd.read_csv(csv_path)

    df = df.fillna(0)

    rename_map = {
        "회차": "round",
        "번호1": "n1",
        "번호2": "n2",
        "번호3": "n3",
        "번호4": "n4",
        "번호5": "n5",
        "번호6": "n6",
        "보너스": "bonus",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).fillna(0)

    df["round"] = df["round"].astype(int)
    for col in NUM_COLS:
        df[col] = df[col].astype(int)
    if "bonus" in df.columns:
        df["bonus"] = df["bonus"].astype(int)

    return df.sort_values("round", ascending=True).reset_index(drop=True)


def get_zone_counts(nums: list[int]) -> np.ndarray:
    """6개 번호의 구간별 출현 개수를 반환합니다."""
    counts = np.zeros(len(ZONE_LABELS), dtype=int)
    for x in nums:
        for idx in range(len(ZONE_LABELS)):
            left, right = BINS[idx], BINS[idx + 1]
            if (idx == 0 and left <= x <= right) or (idx > 0 and left < x <= right):
                counts[idx] += 1
                break
    return counts


def extract_features(curr_nums: list[int], prev_nums: list[int]) -> dict:
    """직전 회차(prev_nums) 대비 현재/후보 조합(curr_nums)의 전화차 지표를 추출합니다."""
    curr_s = sorted(curr_nums)
    prev_s = sorted(prev_nums)

    pos_diffs = [c - p for c, p in zip(curr_s, prev_s)]
    pos_abs_sum = int(np.sum(np.abs(pos_diffs)))
    pos_max_abs = int(np.max(np.abs(pos_diffs)))

    zone_shift_mag = int(np.sum(np.abs(get_zone_counts(curr_s) - get_zone_counts(prev_s))))

    end_sum_diff = int(sum(x % 10 for x in curr_s) - sum(x % 10 for x in prev_s))
    common_end_cnt = len(set(x % 10 for x in curr_s) & set(x % 10 for x in prev_s))

    return {
        "pos_abs_sum": pos_abs_sum,
        "pos_max_abs": pos_max_abs,
        "zone_shift_mag": zone_shift_mag,
        "end_sum_diff": end_sum_diff,
        "common_end_cnt": common_end_cnt,
    }


def build_thresholds(df: pd.DataFrame, lower_q: float = 0.10, upper_q: float = 0.90) -> dict:
    """과거 회차의 전화차 분포로부터 조건식 임계값을 산출합니다."""
    sorted_matrix = df[NUM_COLS].apply(lambda r: sorted(int(v) for v in r), axis=1).tolist()
    rows = [
        extract_features(sorted_matrix[idx], sorted_matrix[idx - 1])
        for idx in range(1, len(sorted_matrix))
    ]
    if not rows:
        return {
            "pos_abs_sum_min": 0.0,
            "pos_abs_sum_max": 999.0,
            "pos_max_abs_max": 99.0,
            "zone_shift_max": 99.0,
            "end_sum_diff_min": -99.0,
            "end_sum_diff_max": 99.0,
            "common_end_min": 0,
        }

    feat_df = pd.DataFrame(rows).fillna(0)
    return {
        "pos_abs_sum_min": float(feat_df["pos_abs_sum"].quantile(lower_q)),
        "pos_abs_sum_max": float(feat_df["pos_abs_sum"].quantile(upper_q)),
        "pos_max_abs_max": float(feat_df["pos_max_abs"].quantile(upper_q)),
        "zone_shift_max": float(feat_df["zone_shift_mag"].quantile(upper_q)),
        "end_sum_diff_min": float(feat_df["end_sum_diff"].quantile(lower_q)),
        "end_sum_diff_max": float(feat_df["end_sum_diff"].quantile(upper_q)),
        "common_end_min": 1,
    }


def passes_all_conditions(candidate: list[int], prev_nums: list[int], rules: dict) -> bool:
    """위치별·구간별·끝수별 전화차 조건식 통과 여부를 반환합니다."""
    f = extract_features(candidate, prev_nums)
    cond_pos = (
        rules["pos_abs_sum_min"] <= f["pos_abs_sum"] <= rules["pos_abs_sum_max"]
    ) and (f["pos_max_abs"] <= rules["pos_max_abs_max"])
    cond_zone = f["zone_shift_mag"] <= rules["zone_shift_max"]
    cond_end = (
        rules["end_sum_diff_min"] <= f["end_sum_diff"] <= rules["end_sum_diff_max"]
    ) and (f["common_end_cnt"] >= rules["common_end_min"])
    return bool(cond_pos and cond_zone and cond_end)


def compute_number_stats(history_df: pd.DataFrame, recent_k: int = 30) -> pd.DataFrame:
    """이전 회차 데이터(history_df)만 사용해 1~45 번호별 통계 점수를 계산합니다."""
    df_clean = history_df.fillna(0).sort_values("round").reset_index(drop=True)
    num_matrix = df_clean[NUM_COLS].apply(
        lambda r: [int(v) for v in r if int(v) > 0], axis=1
    ).tolist()

    total_draws = len(num_matrix)
    recent_slice = num_matrix[-recent_k:] if total_draws > 0 else []

    rows = []
    for num in range(1, 46):
        total_cnt = sum(1 for draw in num_matrix if num in draw)
        recent_cnt = sum(1 for draw in recent_slice if num in draw)

        last_seen_idx = None
        for idx in range(total_draws - 1, -1, -1):
            if num in num_matrix[idx]:
                last_seen_idx = idx
                break
        gap_draws = (total_draws - 1 - last_seen_idx) if last_seen_idx is not None else total_draws

        rows.append(
            {
                "num": num,
                "end_digit": num % 10,
                "total_cnt": total_cnt,
                "recent_cnt": recent_cnt,
                "gap_draws": gap_draws,
            }
        )

    stats_df = pd.DataFrame(rows).fillna(0)
    for col in ["total_cnt", "recent_cnt", "gap_draws"]:
        c_min, c_max = stats_df[col].min(), stats_df[col].max()
        stats_df[f"{col}_norm"] = (stats_df[col] - c_min) / (c_max - c_min) if c_max > c_min else 0.0

    stats_df["stat_score"] = (
        0.35 * stats_df["recent_cnt_norm"]
        + 0.35 * stats_df["total_cnt_norm"]
        + 0.30 * stats_df["gap_draws_norm"]
    ).round(4)

    return stats_df.sort_values(["stat_score", "num"], ascending=[False, True]).reset_index(drop=True)


def select_candidate_pool(
    stats_df: pd.DataFrame,
    pool_size: int = 18,
    excluded_nums: set[int] | None = None,
    required_nums: set[int] | None = None,
    max_per_end_digit: int | None = 3,
) -> list[int]:
    """통계 점수와 노트별 규칙을 반영해 번호 후보군(pool_nums)을 추출합니다."""
    excluded = excluded_nums or set()
    required = {n for n in (required_nums or set()) if 1 <= n <= 45 and n not in excluded}
    df_f = stats_df[~stats_df["num"].isin(excluded)].copy()

    selected = list(required)
    end_counter: dict[int, int] = {}
    for n in selected:
        end_counter[n % 10] = end_counter.get(n % 10, 0) + 1

    for _, row in df_f.iterrows():
        n = int(row["num"])
        end_d = int(row["end_digit"])
        if n in selected:
            continue
        if max_per_end_digit is not None and end_counter.get(end_d, 0) >= max_per_end_digit:
            continue
        selected.append(n)
        end_counter[end_d] = end_counter.get(end_d, 0) + 1
        if len(selected) >= pool_size:
            break

    return sorted(selected)


def is_junk_combination(combo: list[int]) -> bool:
    """쓰레기 조합 필터(True면 제외). 실제 노트 기준에 맞게 조정하세요."""
    s = sorted(combo)

    # 3연속 이상 번호 제외
    run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
            if run >= 3:
                return True
        else:
            run = 1

    # 1~10 구간에 4개 이상 쏠린 조합 제외
    if sum(1 for x in s if 1 <= x <= 10) >= 4:
        return True

    # 동일 끝수 3개 이상 조합 제외
    end_counts: dict[int, int] = {}
    for x in s:
        end_counts[x % 10] = end_counts.get(x % 10, 0) + 1
    if max(end_counts.values()) >= 3:
        return True

    return False


def compare_pool_sizes(
    df: pd.DataFrame,
    pool_sizes: list[int] = [15, 18, 20, 24],
    recent_k: int = 30,
    lookback_rounds: int = 100,
    lower_q: float = 0.10,
    upper_q: float = 0.90,
    excluded_nums: set[int] | None = None,
    required_nums: set[int] | None = None,
    max_per_end_digit: int | None = 3,
) -> pd.DataFrame:
    """pool_size별 과거 회차 적중률과 단계별 조합 개수를 비교합니다."""
    df_sorted = df.fillna(0).sort_values("round", ascending=True).reset_index(drop=True)
    history_df = df_sorted.iloc[:-1].reset_index(drop=True)
    prev_row = df_sorted.iloc[-1]
    prev_nums = [int(prev_row[c]) for c in NUM_COLS]
    diff_rules = build_thresholds(history_df, lower_q=lower_q, upper_q=upper_q)
    latest_stats_df = compute_number_stats(history_df, recent_k=recent_k)

    start_idx = max(1, len(df_sorted) - lookback_rounds)
    round_actuals = []
    round_stats = []
    for idx in range(start_idx, len(df_sorted)):
        actual_set = {
            int(df_sorted.loc[idx, c]) for c in NUM_COLS if int(df_sorted.loc[idx, c]) > 0
        }
        round_actuals.append(actual_set)
        round_stats.append(
            compute_number_stats(df_sorted.iloc[:idx].reset_index(drop=True), recent_k=recent_k)
        )

    rows = []
    for p_size in pool_sizes:
        hit_counts = []
        for actual_set, s_df in zip(round_actuals, round_stats):
            pool = select_candidate_pool(
                s_df,
                pool_size=p_size,
                excluded_nums=excluded_nums,
                required_nums=required_nums,
                max_per_end_digit=max_per_end_digit,
            )
            hit_counts.append(len(actual_set & set(pool)))

        hits_arr = np.array(hit_counts, dtype=int) if hit_counts else np.array([0], dtype=int)

        current_pool = select_candidate_pool(
            latest_stats_df,
            pool_size=p_size,
            excluded_nums=excluded_nums,
            required_nums=required_nums,
            max_per_end_digit=max_per_end_digit,
        )
        raw_combo_cnt = math.comb(len(current_pool), 6) if len(current_pool) >= 6 else 0

        diff_passed = [
            list(c)
            for c in combinations(current_pool, 6)
            if passes_all_conditions(list(c), prev_nums, diff_rules)
        ]
        final_passed = [c for c in diff_passed if not is_junk_combination(c)]

        rows.append(
            {
                "pool_size": len(current_pool),
                "avg_hits": round(float(hits_arr.mean()), 2),
                "hit_ge_3_pct": round(float(np.mean(hits_arr >= 3)) * 100, 2),
                "hit_ge_4_pct": round(float(np.mean(hits_arr >= 4)) * 100, 2),
                "raw_combos": raw_combo_cnt,
                "after_diff_filter": len(diff_passed),
                "after_junk_filter": len(final_passed),
                "survival_pct": round((len(final_passed) / raw_combo_cnt) * 100, 2)
                if raw_combo_cnt > 0
                else 0.0,
            }
        )

    return pd.DataFrame(rows).fillna(0)


if __name__ == "__main__":
    df = load_lotto_csv("lotto.csv")
    print(f"로드 완료: {int(df['round'].iloc[0])}회 ~ {int(df['round'].iloc[-1])}회 (총 {len(df)}회차)")

    comp_df = compare_pool_sizes(
        df=df,
        pool_sizes=[15, 18, 20, 24],
        recent_k=30,
        lookback_rounds=100,
        lower_q=0.10,
        upper_q=0.90,
        max_per_end_digit=3,
    )
    print("\n=== pool_size별 비교 결과 ===")
    print(comp_df.to_string(index=False))