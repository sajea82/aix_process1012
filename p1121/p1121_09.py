from itertools import combinations
import json
from pathlib import Path
import pandas as pd

from p1121_02 import load_notes_from_dir, score_numbers_from_notes
from p1121_03 import load_winning_numbers
from p1121_05 import passes_custom_conditions
from p1121_08 import pick_diverse_combos, pick_top_score_combos


def save_weekly_prediction_log(
    target_round: int = 1250,
    pool_size: int = 18,
    k: int = 15,
) -> tuple[Path, Path]:
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    lotto_csv = base_dir.parent / "p1120" / "data" / "lotto.csv"
    win_map = load_winning_numbers(lotto_csv)
    prev_win = sorted(win_map.get(target_round, set()))

    notes = load_notes_from_dir()
    scores = score_numbers_from_notes(notes, target_round=target_round)
    ranked_nums = [n for n, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))]
    pool = sorted(ranked_nums[:pool_size])

    survived = [
        c for c in combinations(pool, 6)
        if passes_custom_conditions(c, prev_win_nums=set(prev_win))
    ]

    top_combos = pick_top_score_combos(survived, scores, k=k)
    div_combos = pick_diverse_combos(survived, scores, k=k)

    pred_round = target_round + 1
    actual_win_set = win_map.get(pred_round)
    actual_win_str = " ".join(str(n) for n in sorted(actual_win_set)) if actual_win_set else ""

    # 1. 회차별 상세 JSON 저장
    json_path = log_dir / f"pred_{pred_round}회.json"
    payload = {
        "pred_round": pred_round,
        "base_round": target_round,
        "prev_win_nums": prev_win,
        "pool_size": pool_size,
        "pool": pool,
        "survived_count": len(survived),
        "top_k": k,
        "top_score_combos": [list(c) for c in top_combos],
        "diverse_combos": [list(c) for c in div_combos],
        "actual_win_nums": sorted(actual_win_set) if actual_win_set else None,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. 누적 CSV 로그 갱신(동일 pred_round + method는 덮어쓰기)
    csv_path = log_dir / "predictions_history.csv"
    rows = []
    for method_name, combo_list in [("top_score", top_combos), ("diversity_greedy", div_combos)]:
        for rank_idx, c in enumerate(combo_list, start=1):
            c_set = set(c)
            hit_cnt = len(c_set & actual_win_set) if actual_win_set else ""
            rows.append({
                "pred_round": pred_round,
                "base_round": target_round,
                "method": method_name,
                "rank": rank_idx,
                "n1": c[0],
                "n2": c[1],
                "n3": c[2],
                "n4": c[3],
                "n5": c[4],
                "n6": c[5],
                "score_sum": round(sum(scores[n] for n in c), 2),
                "num_sum": sum(c),
                "actual_win": actual_win_str,
                "hit_cnt": hit_cnt,
            })

    new_df = pd.DataFrame(rows)
    if csv_path.exists():
        old_df = pd.read_csv(csv_path, encoding="utf-8-sig")
        old_df = old_df[old_df["pred_round"] != pred_round]
        merged_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        merged_df = new_df

    merged_df = merged_df.sort_values(["pred_round", "method", "rank"]).reset_index(drop=True)
    merged_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"[기록 저장 완료] {pred_round}회 예측 (pool_size={pool_size}, 생존 {len(survived):,}개)")
    print(f"- JSON: {json_path}")
    print(f"- CSV : {csv_path} (총 누적 {len(merged_df)}행)")
    return json_path, csv_path


if __name__ == "__main__":
    save_weekly_prediction_log(target_round=1250, pool_size=18, k=15)