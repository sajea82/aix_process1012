from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def build_long_absent_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "02_장기미출수.xlsx",
    max_rows: int = 40,
    include_next_round: bool = True,
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 장기미출수 시뮬레이션 엑셀을
    p1120/update/02_장기미출수.xlsx로 생성합니다.
    """
    df_raw = _read_csv_zero(input_csv)

    if "회차" not in df_raw.columns:
        df_raw = df_raw.reset_index()
        df_raw.rename(columns={df_raw.columns[0]: "회차"}, inplace=True)

    rename_map = {
        "round": "회차",
        "n1": "번호1",
        "n2": "번호2",
        "n3": "번호3",
        "n4": "번호4",
        "n5": "번호5",
        "n6": "번호6",
        "bonus": "보너스",
    }
    df_raw = df_raw.rename(columns={k: v for k, v in rename_map.items() if k in df_raw.columns}).fillna(0)

    num_cols = ["번호1", "번호2", "번호3", "번호4", "번호5", "번호6"]
    df_raw["회차"] = pd.to_numeric(df_raw["회차"], errors="coerce").fillna(0).astype(int)
    for col in num_cols:
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce").fillna(0).astype(int)
    if "보너스" in df_raw.columns:
        df_raw["보너스"] = pd.to_numeric(df_raw["보너스"], errors="coerce").fillna(0).astype(int)
    else:
        df_raw["보너스"] = 0

    df_raw = df_raw.sort_values("회차", ascending=True).reset_index(drop=True)

    result_data = []
    current_state = {i: [] for i in range(1, max_rows + 1)}

    for _, row in df_raw.iterrows():
        draw_no = int(row["회차"])
        winning_nums = [int(row[c]) for c in num_cols]

        # 1. 현재 회차 기준 상태 기록
        row_result = {"회차": draw_no}
        for r in range(1, max_rows + 1):
            nums = current_state[r]
            for idx in range(6):
                row_result[f"{r}행_번호{idx+1}"] = nums[idx] if idx < len(nums) else 0
        result_data.append(row_result)

        # 2. 이번 회차 당첨 번호 제거(중복 방지)
        for r in range(1, max_rows + 1):
            current_state[r] = [num for num in current_state[r] if num not in winning_nums]

        # 3. 기존 번호들을 한 칸씩 아래로 밀어냄
        for r in range(max_rows, 1, -1):
            current_state[r] = current_state[r - 1].copy()

        # 4. 이번 회차 당첨 번호를 맨 위(1행)에 올림
        current_state[1] = winning_nums.copy()

    # 최신 회차 다음 회차 행 추가
    if include_next_round and not df_raw.empty:
        last_draw = int(df_raw["회차"].max())
        next_draw_row = {"회차": last_draw + 1}
        for r in range(1, max_rows + 1):
            nums = current_state[r]
            for idx in range(6):
                next_draw_row[f"{r}행_번호{idx+1}"] = nums[idx] if idx < len(nums) else 0
        result_data.append(next_draw_row)

    df_result = pd.DataFrame(result_data).fillna(0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_result.to_excel(output_xlsx, index=False)

    # openpyxl 서식 및 색상 적용
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    sec1_fill = PatternFill(start_color="EBF1F5", end_color="EBF1F5", fill_type="solid")
    sec2_fill = PatternFill(start_color="F2F5EB", end_color="F2F5EB", fill_type="solid")
    sec3_fill = PatternFill(start_color="FDF5E6", end_color="FDF5E6", fill_type="solid")

    purple_fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
    purple_font = Font(name="맑은 고딕", size=10, bold=True, color="4B0082")

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")

    for r_idx in range(2, ws.max_row + 1):
        draw_no = ws.cell(row=r_idx, column=1).value
        if draw_no is None:
            continue

        match_row = df_raw[df_raw["회차"] == draw_no]
        if match_row.empty:
            continue

        winning_set = set(match_row[num_cols].values[0])
        bonus_val = int(match_row["보너스"].values[0])

        for c_idx in range(2, ws.max_column + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            val = cell.value

            if 2 <= c_idx <= 31:
                cell.fill = sec1_fill
            elif 32 <= c_idx <= 61:
                cell.fill = sec2_fill
            else:
                cell.fill = sec3_fill

            if val in winning_set and val != 0:
                cell.fill = purple_fill
                cell.font = purple_font
            elif val == bonus_val and val != 0:
                cell.fill = green_fill
                cell.font = green_font

    wb.save(output_xlsx)
    return output_xlsx


if __name__ == "__main__":
    saved_path = build_long_absent_excel()
    print(f"최신 회차 반영 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")