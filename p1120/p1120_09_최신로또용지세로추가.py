from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPDATE_DIR = BASE_DIR / "update"

GROUPS = ["1구", "2구", "3구", "4구", "5구", "6구", "7구"]


def _read_csv_zero(csv_path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc).fillna(0)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(csv_path).fillna(0)


def get_column_group(num: int) -> str:
    """1구~7구 매핑 함수 (7로 나눈 나머지 기준)."""
    rem = int(num) % 7
    if rem == 1:
        return "1구"
    elif rem == 2:
        return "2구"
    elif rem == 3:
        return "3구"
    elif rem == 4:
        return "4구"
    elif rem == 5:
        return "5구"
    elif rem == 6:
        return "6구"
    elif rem == 0:
        return "7구"
    return "1구"


def build_vertical_paper_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "09_로또용지_세로분포.xlsx",
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 로또용지 세로분포(1구~7구) 엑셀을
    p1120/update/09_로또용지_세로분포.xlsx로 생성합니다.
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
        winning_nums = [int(row[c]) for c in num_cols if int(row[c]) > 0]
        bonus_num = int(row["보너스"])

        group_data = {g: [] for g in GROUPS}
        for n in winning_nums:
            group_data[get_column_group(n)].append(str(n))

        if bonus_num > 0:
            group_data[get_column_group(bonus_num)].append(f"{bonus_num}(보)")

        row_dict = {"회차": f"{draw_no}회"}
        for g in GROUPS:
            nums = group_data[g]
            row_dict[g] = ", ".join(nums) if nums else 0

        rows_to_excel.append(row_dict)

    df_final = pd.DataFrame(rows_to_excel).fillna(0).replace("", 0)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    # openpyxl 서식 적용 (보너스 초록색, 당첨번호 보라색, 0은 회색)
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
        for c_idx in range(2, 9):  # 1구 ~ 7구 (B열 ~ H열)
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
    saved_path = build_vertical_paper_excel()
    print(f"로또용지 세로분포 갱신 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")