from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"

HORIZONTAL_RANGES = [
    ("1~7", range(1, 8)),
    ("8~14", range(8, 15)),
    ("15~21", range(15, 22)),
    ("22~28", range(22, 29)),
    ("29~35", range(29, 36)),
    ("36~42", range(36, 43)),
    ("43~45", range(43, 46)),
]


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def build_horizontal_paper_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "10_로또용지_가로분포.xlsx",
) -> Path:
    """
    p1120/data/lotto.csv에 등록된 최신 회차까지 자동으로 반영해
    p1120/update/10_로또용지_가로분포.xlsx 파일을 생성합니다.
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

    rows_to_excel = []
    for _, row in df_raw.iterrows():
        draw_no = int(row["회차"])
        curr_winning = [int(row[c]) for c in num_cols if int(row[c]) > 0]
        curr_bonus = int(row["보너스"])
        all_nums = curr_winning + ([curr_bonus] if curr_bonus > 0 else [])

        row_dict = {"회차": f"{draw_no}회"}
        for label, r in HORIZONTAL_RANGES:
            group_nums = []
            for n in all_nums:
                if n in r:
                    if curr_bonus > 0 and n == curr_bonus:
                        group_nums.append(f"{n}(보)")
                    else:
                        group_nums.append(str(n))
            row_dict[label] = ", ".join(group_nums) if group_nums else 0

        rows_to_excel.append(row_dict)

    df_final = pd.DataFrame(rows_to_excel).fillna(0).replace("", 0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")
    purple_font = Font(name="맑은 고딕", size=10, bold=True, color="4B0082")
    gray_font = Font(name="맑은 고딕", size=10, color="888888")

    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx in range(2, ws.max_row + 1):
        ws.cell(row=r_idx, column=1).alignment = Alignment(horizontal="center", vertical="center")
        for c_idx in range(2, ws.max_column + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            val = str(cell.value)

            if val in {"0", "0.0", "None", ""}:
                cell.value = 0
                cell.font = gray_font
            elif "(보)" in val:
                cell.fill = green_fill
                cell.font = green_font
            else:
                cell.font = purple_font

    wb.save(output_xlsx)
    return output_xlsx


if __name__ == "__main__":
    saved_path = build_horizontal_paper_excel()
    print(f"로또용지 가로분포 갱신 완료 -> [{saved_path}]")