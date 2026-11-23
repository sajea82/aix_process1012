from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"

ENDING_LABELS = [
    "1끝",
    "2끝",
    "3끝",
    "4끝",
    "5끝",
    "6끝",
    "7끝",
    "8끝",
    "9끝",
    "0끝",
]


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def get_ending_label(num: int) -> str:
    """끝수 분류 함수 (0은 0끝으로 매칭)."""
    digit = int(num) % 10
    return "0끝" if digit == 0 else f"{digit}끝"


def build_ending_digit_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "03_끝수별_배치표.xlsx",
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 끝수별 배치표 엑셀을
    p1120/update/03_끝수별_배치표.xlsx로 생성합니다.
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
    for _, row in df_raw.iterrows():
        draw_no = int(row["회차"])
        winning_nums = [int(row[c]) for c in num_cols]
        bonus_num = int(row["보너스"])

        row_data = {label: [] for label in ENDING_LABELS}
        for num in winning_nums:
            if num > 0:
                row_data[get_ending_label(num)].append(num)

        bonus_lbl = get_ending_label(bonus_num)

        formatted_row = {"회차": draw_no}
        for label in ENDING_LABELS:
            nums = row_data[label]
            formatted_row[label] = ", ".join(map(str, sorted(nums))) if nums else 0

        formatted_row["_bonus_val"] = bonus_num
        formatted_row["_bonus_lbl"] = bonus_lbl
        table_rows.append(formatted_row)

    df_final = pd.DataFrame(table_rows).fillna(0)

    bonus_info = df_final[["_bonus_lbl", "_bonus_val"]].copy()
    df_final = df_final.drop(columns=["_bonus_lbl", "_bonus_val"])

    cols_order = ["회차"] + ENDING_LABELS
    df_final = df_final[cols_order].fillna(0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    # openpyxl을 이용해 보너스 번호 (보) 표기 및 초록색 서식 적용
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")

    for idx, row_info in bonus_info.iterrows():
        b_val = int(row_info["_bonus_val"])
        if b_val <= 0:
            continue

        r_idx = idx + 2
        b_lbl = row_info["_bonus_lbl"]
        col_idx = ENDING_LABELS.index(b_lbl) + 2

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
    saved_path = build_ending_digit_excel()
    print(f"끝수별 배치표 갱신 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")