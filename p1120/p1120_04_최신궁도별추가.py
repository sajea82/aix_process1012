from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"

GUNG_LABELS = [
    "1궁",
    "2궁",
    "3궁",
    "4궁",
    "5궁",
    "6궁",
    "7궁",
    "8궁",
    "9궁",
]

GUNG_MAP = {
    "1궁": {1, 10, 19, 28, 37},
    "2궁": {2, 11, 20, 29, 38},
    "3궁": {3, 12, 21, 30, 39},
    "4궁": {4, 13, 22, 31, 40},
    "5궁": {5, 14, 23, 32, 41},
    "6궁": {6, 15, 24, 33, 42},
    "7궁": {7, 16, 25, 34, 43},
    "8궁": {8, 17, 26, 35, 44},
    "9궁": {9, 18, 27, 36, 45},
}


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def get_gung_label(num: int) -> str:
    """노트에 적힌 궁도 분류 규칙 함수 (1궁 ~ 9궁)."""
    n = int(num)
    for label, nums in GUNG_MAP.items():
        if n in nums:
            return label
    return "1궁"


def build_gung_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "04_궁도별_배치표.xlsx",
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 궁도별 배치표 엑셀을
    p1120/update/04_궁도별_배치표.xlsx로 생성합니다.
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

    for _, row in df_raw.iterrows():
        draw_no = int(row["회차"])
        winning_nums = [int(row[c]) for c in num_cols]
        bonus_num = int(row["보너스"])

        row_data = {label: [] for label in GUNG_LABELS}
        for num in winning_nums:
            if num > 0:
                row_data[get_gung_label(num)].append(num)

        bonus_gung = get_gung_label(bonus_num)
        bonus_tracking.append({"gung": bonus_gung, "val": bonus_num})

        formatted_row = {"회차": draw_no}
        for label in GUNG_LABELS:
            nums = row_data[label]
            formatted_row[label] = ", ".join(map(str, sorted(nums))) if nums else 0

        table_rows.append(formatted_row)

    df_final = pd.DataFrame(table_rows).fillna(0)
    cols_order = ["회차"] + GUNG_LABELS
    df_final = df_final[cols_order].fillna(0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    # openpyxl을 이용해 보너스 번호 초록색 및 (보) 표시 서식 적용
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")

    for idx, b_info in enumerate(bonus_tracking):
        b_val = int(b_info["val"])
        if b_val <= 0:
            continue

        r_idx = idx + 2
        b_lbl = b_info["gung"]
        col_idx = GUNG_LABELS.index(b_lbl) + 2
        cell = ws.cell(row=r_idx, column=col_idx)

        current_val = str(cell.value)
        if current_val == "0":
            cell.value = f"{b_val}(보)"
        else:
            tokens = [t.strip() for t in current_val.split(",")]
            if str(b_val) in tokens:
                tokens = [f"{b_val}(보)" if t == str(b_val) else t for t in tokens]
                cell.value = ", ".join(tokens)
            else:
                cell.value = f"{current_val}, {b_val}(보)"

        cell.fill = green_fill
        cell.font = green_font

    wb.save(output_xlsx)
    return output_xlsx


if __name__ == "__main__":
    saved_path = build_gung_excel()
    print(f"궁도별 배치표 갱신 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")