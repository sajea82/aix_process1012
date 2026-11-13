import os
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pandas as pd

# 1. 데이터 불러오기
file_path = 'p1109/data/lotto.csv'
df_raw = pd.read_csv(file_path)

if '회차' not in df_raw.columns:
  df_raw = df_raw.reset_index()
  df_raw.rename(columns={df_raw.columns[0]: '회차'}, inplace=True)

df_raw = df_raw.sort_values('회차').reset_index(drop=True)

# 1부터 45까지의 번호 리스트 컬럼 생성
num_columns = [str(i) for i in range(1, 46)]
table_rows = []
bonus_tracking = []  # (회차 행 인덱스, 번호) 추적용

for index, row in df_raw.iterrows():
  draw_no = row['회차']
  winning_nums = [
      str(row['번호1']),
      str(row['번호2']),
      str(row['번호3']),
      str(row['번호4']),
      str(row['번호5']),
      str(row['번호6']),
  ]
  bonus_num = str(row['보너스'])

  # 해당 회차의 1~45번 기본값은 0 (빈공간 0 처리)
  row_data = {'회차': draw_no}
  for col in num_columns:
    row_data[col] = 0

  # 당첨 번호 배치 (당첨된 번호 자리에 해당 번호 숫자 기록)
  for num in winning_nums:
    if num in num_columns:
      row_data[num] = int(num)

  # 보너스 번호 위치 추적
  bonus_tracking.append({'row_idx': index + 2, 'val': bonus_num})

  table_rows.append(row_data)

# 2. 데이터프레임 변환 및 저장
df_final = pd.DataFrame(table_rows)
cols_order = ['회차'] + num_columns
df_final = df_final[cols_order]

output_file = 'p1109/data/08_1부터45_분포도.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 3. openpyxl을 이용해 보너스(초록색) 및 쌍수(다른 색상 강조) 서식 적용
wb = openpyxl.load_workbook(output_file)
ws = wb.active

# 스타일 정의
green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

# 쌍수 강조 스타일 (주황색/다크오렌지 계열)
twin_fill = PatternFill(
    start_color='FFE4B5', end_color='FFE4B5', fill_type='solid'
)
twin_font = Font(name='맑은 고딕', size=10, bold=True, color='B8860B')

twin_numbers = ['11', '22', '33', '44']

# 셀 전체를 돌며 쌍수 번호와 보너스 번호 서식 적용
for r_idx in range(2, ws.max_row + 1):
  for c_idx in range(3, ws.max_column + 1):  # C열(번호 1번)부터 끝까지
    cell = ws.cell(row=r_idx, column=c_idx)
    col_name = str(ws.cell(row=1, column=c_idx).value)

    val = cell.value
    if val != 0 and val is not None:
      # 쌍수 번호인 경우 다른 색상으로 강조
      if col_name in twin_numbers:
        cell.fill = twin_fill
        cell.font = twin_font

# 보너스 번호 처리 (초록색 + (보) 표시)
for b_info in bonus_tracking:
  r_idx = b_info['row_idx']
  b_val = b_info['val']

  if b_val in num_columns:
    col_idx = num_columns.index(b_val) + 2  # 회차 컬럼(1) + 번호 시작(2)
    cell = ws.cell(row=r_idx, column=col_idx)

    cell.value = f'{b_val}(보)'
    cell.fill = green_fill
    cell.font = green_font

wb.save(output_file)
print(f'1숲 분포도 표가 [{output_file}]에 성공적으로 생성되었습니다!')