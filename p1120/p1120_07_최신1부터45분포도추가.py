from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"

NUM_COLUMNS = [str(i) for i in range(1, 46)]
TWIN_NUMBERS = {"11", "22", "33", "44"}


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def build_num1_to_45_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "07_1부터45_분포도.xlsx",
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 1~45 분포도 엑셀을
    p1120/update/07_1부터45_분포도.xlsx로 생성합니다.
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

    table_rows = []
    bonus_tracking = []

    for idx, row in df_raw.iterrows():
        draw_no = int(row["회차"])
        winning_nums = [int(row[c]) for c in num_cols]
        bonus_num = int(row["보너스"])

        row_data = {"회차": draw_no}
        for col in NUM_COLUMNS:
            row_data[col] = 0

        for num in winning_nums:
            s_num = str(num)
            if s_num in row_data:
                row_data[s_num] = int(num)

        bonus_tracking.append({"row_idx": idx + 2, "val": str(bonus_num)})
        table_rows.append(row_data)

    df_final = pd.DataFrame(table_rows).fillna(0)
    cols_order = ["회차"] + NUM_COLUMNS
    df_final = df_final[cols_order].fillna(0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    # openpyxl을 이용해 쌍수(주황색) 및 보너스(초록색) 서식 적용
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")

    twin_fill = PatternFill(start_color="FFE4B5", end_color="FFE4B5", fill_type="solid")
    twin_font = Font(name="맑은 고딕", size=10, bold=True, color="B8860B")

    for r_idx in range(2, ws.max_row + 1):
        for c_idx in range(2, ws.max_column + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            col_name = str(ws.cell(row=1, column=c_idx).value)
            val = cell.value

            if val != 0 and val is not None and col_name in TWIN_NUMBERS:
                cell.fill = twin_fill
                cell.font = twin_font

    for b_info in bonus_tracking:
        r_idx = b_info["row_idx"]
        b_val = b_info["val"]

        if b_val in NUM_COLUMNS:
            col_idx = NUM_COLUMNS.index(b_val) + 2
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.value = f"{b_val}(보)"
            cell.fill = green_fill
            cell.font = green_font

    wb.save(output_xlsx)
    return output_xlsx


if __name__ == "__main__":
    saved_path = build_num1_to_45_excel()
    print(f"1~45 분포도 갱신 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")