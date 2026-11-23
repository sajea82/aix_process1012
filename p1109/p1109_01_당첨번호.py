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

for index, row in df_raw.iterrows():
  draw_no = row['회차']
  winning_nums = [int(row[f'번호{i}']) for i in range(1, 7)]
  bonus_num = int(row['보너스'])

  winning_str = ', '.join(map(str, winning_nums))
  bonus_str = f'{bonus_num}(보)'

  # 1번째(인덱스 0) - 3번째(인덱스 2) 뺄셈 계산 후 절댓값(마이너스 제거) 적용
  num_1st = winning_nums[0]
  num_3rd = winning_nums[2]
  diff_1_3 = abs(num_1st - num_3rd)

  row_dict = {
      '회차': f'{draw_no}회',
      '당첨번호': winning_str,
      '보너스': bonus_str,
      '합계': diff_1_3,  # 마이너스 뗀 순수 숫자 입력
  }
  rows_to_excel.append(row_dict)

df_final = pd.DataFrame(rows_to_excel)
output_file = 'p1109/data/17_당첨번호_1_3번째뺄셈절댓값표_다음회차매칭.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 2. openpyxl 서식 적용
wb = openpyxl.load_workbook(output_file)
ws = wb.active

purple_fill = PatternFill(
    start_color='E6E6FA', end_color='E6E6FA', fill_type='solid'
)
purple_font = Font(name='맑은 고딕', size=10, bold=True, color='4B0082')

green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

for col in range(1, ws.max_column + 1):
  cell = ws.cell(row=1, column=col)
  cell.alignment = Alignment(horizontal='center', vertical='center')

for r_idx in range(2, ws.max_row + 1):
  ws.cell(row=r_idx, column=1).alignment = Alignment(
      horizontal='center', vertical='center'
  )

  w_cell = ws.cell(row=r_idx, column=2)
  w_cell.font = purple_font
  w_cell.alignment = Alignment(horizontal='center', vertical='center')

  b_cell = ws.cell(row=r_idx, column=3)
  b_cell.fill = green_fill
  b_cell.font = green_font
  b_cell.alignment = Alignment(horizontal='center', vertical='center')

  s_cell = ws.cell(row=r_idx, column=4)
  s_cell.alignment = Alignment(horizontal='center', vertical='center')

# 다음 회차 매칭 검사 및 서식 적용
for r_idx in range(2, ws.max_row + 1):
  s_cell = ws.cell(row=r_idx, column=4)
  if s_cell.value is None or not str(s_cell.value).isdigit():
    continue
  val = int(s_cell.value)

  if r_idx < ws.max_row:
    next_w_str = str(ws.cell(row=r_idx + 1, column=2).value)
    next_b_str = str(ws.cell(row=r_idx + 1, column=3).value)

    next_winning_nums = [
        int(x.strip()) for x in next_w_str.split(',') if x.strip().isdigit()
    ]
    raw_next_b = next_b_str.replace('(보)', '').strip()
    next_bonus_num = int(raw_next_b) if raw_next_b.isdigit() else -1

    if val in next_winning_nums:
      s_cell.fill = purple_fill
      s_cell.font = purple_font
    elif val == next_bonus_num:
      s_cell.fill = green_fill
      s_cell.font = green_font

wb.save(output_file)
print('절댓값 뺄셈 표 생성 및 다음회차 매칭 완료:', output_file)