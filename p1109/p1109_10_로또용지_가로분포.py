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

total_rows = len(df_raw)
rows_to_excel = []

# 가로 구간 정의 (7개 구간)
ranges = [
    ('1~7', range(1, 8)),
    ('8~14', range(8, 15)),
    ('15~21', range(15, 22)),
    ('22~28', range(22, 29)),
    ('29~35', range(29, 36)),
    ('36~42', range(36, 43)),
    ('43~45', range(43, 46)),
]

for index in range(total_rows + 1):
  if index < total_rows:
    row = df_raw.iloc[index]
    draw_no = row['회차']
    curr_winning = [int(row[f'번호{i}']) for i in range(1, 7)]
    curr_bonus = int(row['보너스'])
    all_nums = curr_winning + [curr_bonus]
    has_winning = True
  else:
    draw_no = 1250
    all_nums = []
    has_winning = False

  row_dict = {'회차': f'{draw_no}회'}

  for label, r in ranges:
    group_nums = []
    for n in all_nums:
      if n in r:
        if n == curr_bonus:
          group_nums.append(f'{n}(보)')
        else:
          group_nums.append(str(n))
    row_dict[label] = ', '.join(group_nums) if group_nums else 0

  rows_to_excel.append(row_dict)

# 2. 데이터프레임 변환 및 결측치 0 처리
df_final = pd.DataFrame(rows_to_excel)
df_final = df_final.fillna(0).replace('', 0)

output_file = 'p1109/data/16_로또용지_가로분포_구간별.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 3. openpyxl 서식 적용 (보라색 당첨번호, 초록색 보너스, 0은 회색)
wb = openpyxl.load_workbook(output_file)
ws = wb.active

green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')
purple_font = Font(name='맑은 고딕', size=10, bold=True, color='4B0082')

for col in range(1, ws.max_column + 1):
  cell = ws.cell(row=1, column=col)
  cell.alignment = Alignment(horizontal='center', vertical='center')

for r_idx in range(2, ws.max_row + 1):
  ws.cell(row=r_idx, column=1).alignment = Alignment(
      horizontal='center', vertical='center'
  )
  for c_idx in range(2, ws.max_column + 1):
    cell = ws.cell(row=r_idx, column=c_idx)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    val = str(cell.value)

    if val == '0' or val == '0.0':
      cell.font = Font(name='맑은 고딕', size=10, color='888888')
    elif '(보)' in val:
      cell.fill = green_fill
      cell.font = green_font
    else:
      cell.font = purple_font

wb.save(output_file)
print('가로 분포 표 생성 및 서식 적용 완료:', output_file)