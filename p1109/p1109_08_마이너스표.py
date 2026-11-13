import os
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
import pandas as pd

# 1. 데이터 불러오기
file_path = 'p1109/data/lotto.csv'
df_raw = pd.read_csv(file_path)

if '회차' not in df_raw.columns:
  df_raw = df_raw.reset_index()
  df_raw.rename(columns={df_raw.columns[0]: '회차'}, inplace=True)

df_raw = df_raw.sort_values('회차').reset_index(drop=True)

rows_to_excel = []
total_rows = len(df_raw)

# 2. 1249회까지의 데이터 + 1250회 가상 행(1249회 당첨번호 기준 마이너스 수 적용) 생성
for index in range(total_rows + 1):
  if index < total_rows:
    row = df_raw.iloc[index]
    draw_no = row['회차']
    curr_winning = [int(row[f'번호{i}']) for i in range(1, 7)]
    curr_bonus = int(row['보너스'])
    has_winning = True
  else:
    draw_no = 1250
    curr_winning = []
    curr_bonus = 0
    has_winning = False

  # 이전 회차 7개 번호 (당첨번호 6개 + 보너스 1개)
  if index == 0:
    prev_nums = (
        [int(df_raw.iloc[0][f'번호{i}']) for i in range(1, 7)]
        + [int(df_raw.iloc[0]['보너스'])]
    )
  else:
    prev_row = (
        df_raw.iloc[index - 1]
        if index < total_rows
        else df_raw.iloc[total_rows - 1]
    )
    prev_winning = [int(prev_row[f'번호{i}']) for i in range(1, 7)]
    prev_bonus = int(prev_row['보너스'])
    prev_nums = prev_winning + [prev_bonus]

  m20_vals = [abs(n - 20) for n in prev_nums]
  m30_vals = [abs(n - 30) for n in prev_nums]
  m40_vals = [abs(n - 40) for n in prev_nums]

  if has_winning:
    winning_str = ', '.join(map(str, curr_winning))
    bonus_str = str(curr_bonus)
    last_digits = [n % 10 for n in curr_winning]
    sum_last_digits = sum(last_digits)

    curr_set = set(curr_winning)
    all_prev_minus_pool = set(m20_vals + m30_vals + m40_vals)
    hit_count = len([n for n in curr_winning if n in all_prev_minus_pool])
    bonus_hit = curr_bonus in all_prev_minus_pool

    if hit_count == 0 and not bonus_hit:
      cnt_str = 'X'
    else:
      cnt_str = f"{hit_count}'" if bonus_hit else f'{hit_count}'
  else:
    winning_str = ''
    bonus_str = ''
    sum_last_digits = ''
    cnt_str = ''

  row_dict = {'회차': f'{draw_no}회', '당첨번호': winning_str, '보너스': bonus_str}

  for i, val in enumerate(m20_vals):
    row_dict[f'-20_{i+1}'] = val
  for i, val in enumerate(m30_vals):
    row_dict[f'-30_{i+1}'] = val
  for i, val in enumerate(m40_vals):
    row_dict[f'-40_{i+1}'] = val

  row_dict['합계'] = sum_last_digits
  row_dict['당첨갯수'] = cnt_str

  rows_to_excel.append(row_dict)

df_final = pd.DataFrame(rows_to_excel)
output_file = 'p1109/data/14_마이너스_7칸분할표_1250포함.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 3. openpyxl 서식 적용 (보라색 배경, 초록색 보너스 배경, 미당첨 구간 빨간색)
wb = openpyxl.load_workbook(output_file)
ws = wb.active

purple_fill = PatternFill(
    start_color='E6E6FA', end_color='E6E6FA', fill_type='solid'
)  # 연보라색 배경
purple_font = Font(name='맑은 고딕', size=10, bold=True, color='4B0082')

green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

red_fill = PatternFill(
    start_color='FFD2D2', end_color='FFD2D2', fill_type='solid'
)
red_font = Font(name='맑은 고딕', size=10, bold=True, color='C00000')

for col in range(1, ws.max_column + 1):
  cell = ws.cell(row=1, column=col)
  cell.alignment = Alignment(horizontal='center', vertical='center')

for r_idx in range(2, ws.max_row + 1):
  ws.cell(row=r_idx, column=1).alignment = Alignment(
      horizontal='center', vertical='center'
  )

  w_cell = ws.cell(row=r_idx, column=2)
  w_cell.alignment = Alignment(horizontal='center', vertical='center')

  b_cell = ws.cell(row=r_idx, column=3)
  b_val = str(b_cell.value)
  if b_val and b_val != 'nan' and b_val != '':
    b_cell.value = f'{b_val}(보)'
    b_cell.fill = green_fill
    b_cell.font = green_font
    b_cell.alignment = Alignment(horizontal='center', vertical='center')

  curr_winning_nums = (
      [int(x.strip()) for x in str(w_cell.value).split(',')]
      if w_cell.value and str(w_cell.value).strip() != ''
      else []
  )
  raw_b = (
      str(ws.cell(row=r_idx, column=3).value).replace('(보)', '').strip()
  )
  curr_bonus_num = int(raw_b) if raw_b.isdigit() else 0

  # -20(7칸: D~J), -30(7칸: K~Q), -40(7칸: R~X)
  m20_cells = [ws.cell(row=r_idx, column=c) for c in range(4, 11)]
  m30_cells = [ws.cell(row=r_idx, column=c) for c in range(11, 18)]
  m40_cells = [ws.cell(row=r_idx, column=c) for c in range(18, 25)]

  for section_cells in [m20_cells, m30_cells, m40_cells]:
    section_has_hit = False
    for cell in section_cells:
      val = cell.value
      if val is not None and str(val).isdigit():
        num_val = int(val)
        if num_val in curr_winning_nums:
          cell.fill = purple_fill  # 당첨 칸 배경 보라색
          cell.font = purple_font
          section_has_hit = True
        elif num_val == curr_bonus_num:
          cell.fill = green_fill
          cell.font = green_font
          cell.value = f'{num_val}(보)'
          section_has_hit = True
      cell.alignment = Alignment(horizontal='center', vertical='center')

    # 미당첨 구간 빨간색 표시 (1250회 제외)
    is_last_row = (r_idx == ws.max_row) and (
        str(ws.cell(row=r_idx, column=1).value) == '1250회'
    )
    if not section_has_hit and not is_last_row:
      for cell in section_cells:
        cell.fill = red_fill
        cell.font = red_font

wb.save(output_file)
print('최종 완료 파일:', output_file)