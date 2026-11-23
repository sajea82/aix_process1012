from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
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


def build_minus_table_excel(
    input_csv: Path = DATA_DIR / "lotto.csv",
    output_xlsx: Path = UPDATE_DIR / "08_마이너스표.xlsx",
    include_next_round: bool = True,
) -> Path:
    """
    p1120/data/lotto.csv의 최신 회차까지 반영해 마이너스(-20, -30, -40) 7칸 분할표와
    색상 서식을 생성해 p1120/update/08_마이너스표.xlsx로 저장합니다.
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
    total_rows = len(df_raw)
    extra_count = 1 if (include_next_round and total_rows > 0) else 0
    next_draw_no = int(df_raw["회차"].max()) + 1 if total_rows > 0 else 1

    for index in range(total_rows + extra_count):
        if index < total_rows:
            row = df_raw.iloc[index]
            draw_no = int(row["회차"])
            curr_winning = [int(row[c]) for c in num_cols]
            curr_bonus = int(row["보너스"])
            has_winning = True
        else:
            draw_no = next_draw_no
            curr_winning = []
            curr_bonus = 0
            has_winning = False

        # 이전 회차 7개 번호 (당첨번호 6개 + 보너스 1개)
        if index == 0:
            prev_nums = [int(df_raw.iloc[0][c]) for c in num_cols] + [int(df_raw.iloc[0]["보너스"])]
        else:
            prev_row = df_raw.iloc[index - 1] if index < total_rows else df_raw.iloc[total_rows - 1]
            prev_winning = [int(prev_row[c]) for c in num_cols]
            prev_bonus = int(prev_row["보너스"])
            prev_nums = prev_winning + [prev_bonus]

        m20_vals = [abs(n - 20) for n in prev_nums]
        m30_vals = [abs(n - 30) for n in prev_nums]
        m40_vals = [abs(n - 40) for n in prev_nums]

        if has_winning:
            winning_str = ", ".join(map(str, curr_winning))
            bonus_str = str(curr_bonus) if curr_bonus != 0 else 0
            last_digits = [n % 10 for n in curr_winning]
            sum_last_digits = sum(last_digits)

            all_prev_minus_pool = set(m20_vals + m30_vals + m40_vals)
            hit_count = len([n for n in curr_winning if n in all_prev_minus_pool])
            bonus_hit = (curr_bonus != 0) and (curr_bonus in all_prev_minus_pool)

            if hit_count == 0 and not bonus_hit:
                cnt_str = "X"
            else:
                cnt_str = f"{hit_count}'" if bonus_hit else f"{hit_count}"
        else:
            winning_str = 0
            bonus_str = 0
            sum_last_digits = 0
            cnt_str = 0

        row_dict = {
            "회차": f"{draw_no}회",
            "당첨번호": winning_str,
            "보너스": bonus_str,
        }

        for i, val in enumerate(m20_vals):
            row_dict[f"-20_{i+1}"] = val
        for i, val in enumerate(m30_vals):
            row_dict[f"-30_{i+1}"] = val
        for i, val in enumerate(m40_vals):
            row_dict[f"-40_{i+1}"] = val

        row_dict["합계"] = sum_last_digits
        row_dict["당첨갯수"] = cnt_str

        rows_to_excel.append(row_dict)

    df_final = pd.DataFrame(rows_to_excel).fillna(0)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(output_xlsx, index=False)

    # openpyxl 서식 적용
    wb = openpyxl.load_workbook(output_xlsx)
    ws = wb.active

    purple_fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
    purple_font = Font(name="맑은 고딕", size=10, bold=True, color="4B0082")

    green_fill = PatternFill(start_color="E0F8E0", end_color="E0F8E0", fill_type="solid")
    green_font = Font(name="맑은 고딕", size=10, bold=True, color="006400")

    red_fill = PatternFill(start_color="FFD2D2", end_color="FFD2D2", fill_type="solid")
    red_font = Font(name="맑은 고딕", size=10, bold=True, color="C00000")

    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx in range(2, ws.max_row + 1):
        round_label = str(ws.cell(row=r_idx, column=1).value)
        ws.cell(row=r_idx, column=1).alignment = Alignment(horizontal="center", vertical="center")

        w_cell = ws.cell(row=r_idx, column=2)
        w_cell.alignment = Alignment(horizontal="center", vertical="center")

        b_cell = ws.cell(row=r_idx, column=3)
        b_val = str(b_cell.value)
        if b_val and b_val not in {"0", "nan", "None", ""}:
            b_cell.value = f"{b_val}(보)"
            b_cell.fill = green_fill
            b_cell.font = green_font
        b_cell.alignment = Alignment(horizontal="center", vertical="center")

        raw_w = str(w_cell.value) if w_cell.value is not None else ""
        curr_winning_nums = [
            int(x.strip()) for x in raw_w.split(",") if x.strip().isdigit() and int(x.strip()) > 0
        ]
        raw_b = str(ws.cell(row=r_idx, column=3).value).replace("(보)", "").strip()
        curr_bonus_num = int(raw_b) if raw_b.isdigit() and int(raw_b) > 0 else 0

        # -20(7칸: D~J), -30(7칸: K~Q), -40(7칸: R~X)
        m20_cells = [ws.cell(row=r_idx, column=c) for c in range(4, 11)]
        m30_cells = [ws.cell(row=r_idx, column=c) for c in range(11, 18)]
        m40_cells = [ws.cell(row=r_idx, column=c) for c in range(18, 25)]

        is_future_row = include_next_round and (r_idx == ws.max_row) and (round_label == f"{next_draw_no}회")

        for section_cells in [m20_cells, m30_cells, m40_cells]:
            section_has_hit = False
            for cell in section_cells:
                val = cell.value
                if val is not None and str(val).isdigit():
                    num_val = int(val)
                    if num_val in curr_winning_nums:
                        cell.fill = purple_fill
                        cell.font = purple_font
                        section_has_hit = True
                    elif curr_bonus_num > 0 and num_val == curr_bonus_num:
                        cell.fill = green_fill
                        cell.font = green_font
                        cell.value = f"{num_val}(보)"
                        section_has_hit = True
                cell.alignment = Alignment(horizontal="center", vertical="center")

            if not section_has_hit and not is_future_row:
                for cell in section_cells:
                    cell.fill = red_fill
                    cell.font = red_font

    wb.save(output_xlsx)
    return output_xlsx


if __name__ == "__main__":
    saved_path = build_minus_table_excel()
    print(f"마이너스표 갱신 완료 -> [{saved_path}] 파일이 생성/갱신되었습니다.")