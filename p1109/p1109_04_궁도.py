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

# 궁도 레이블 정의 (1궁 ~ 9궁)
gung_labels = [
    '1궁',
    '2궁',
    '3궁',
    '4궁',
    '5궁',
    '6궁',
    '7궁',
    '8궁',
    '9궁',
]


# 노트에 적힌 궁도 분류 규칙 함수
def get_gung_label(num):
  # 1궁: 1, 10, 19, 28, 37
  if num in [1, 10, 19, 28, 37]:
    return '1궁'
  # 2궁: 2, 11, 20, 29, 38
  elif num in [2, 11, 20, 29, 38]:
    return '2궁'
  # 3궁: 3, 12, 21, 30, 39
  elif num in [3, 12, 21, 30, 39]:
    return '3궁'
  # 4궁: 4, 13, 22, 31, 40
  elif num in [4, 13, 22, 31, 40]:
    return '4궁'
  # 5궁: 5, 14, 23, 32, 41
  elif num in [5, 14, 23, 32, 41]:
    return '5궁'
  # 6궁: 6, 15, 24, 33, 42
  elif num in [6, 15, 24, 33, 42]:
    return '6궁'
  # 7궁: 7, 16, 25, 34, 43
  elif num in [7, 16, 25, 34, 43]:
    return '7궁'
  # 8궁: 8, 17, 26, 35, 44
  elif num in [8, 17, 26, 35, 44]:
    return '8궁'
  # 9궁: 9, 18, 27, 36, 45
  elif num in [9, 18, 27, 36, 45]:
    return '9궁'
  return '1궁'


table_rows = []
bonus_tracking = []  # 보너스 번호 위치 추적용

for index, row in df_raw.iterrows():
  draw_no = row['회차']
  winning_nums = [
      row['번호1'],
      row['번호2'],
      row['번호3'],
      row['번호4'],
      row['번호5'],
      row['번호6'],
  ]
  bonus_num = row['보너스']

  row_data = {'회차': draw_no}
  for label in gung_labels:
    row_data[label] = []

  # 일반 당첨 번호 궁도에 배치
  for num in winning_nums:
    g_lbl = get_gung_label(num)
    row_data[g_lbl].append(num)

  # 보너스 번호 궁도 확인
  bonus_gung = get_gung_label(bonus_num)
  bonus_tracking.append({'gung': bonus_gung, 'val': bonus_num})

  # 데이터프레임용 딕셔너리 구성 (빈 공간은 결측치 방지를 위해 일단 0으로 처리)
  formatted_row = {'회차': draw_no}
  for label in gung_labels:
    nums = row_data[label]
    if nums:
      formatted_row[label] = ', '.join(map(str, sorted(nums)))
    else:
      formatted_row[label] = 0  # 빈공간 0 처리

  table_rows.append(formatted_row)

# 2. 데이터프레임 변환
df_final = pd.DataFrame(table_rows)
cols_order = ['회차'] + gung_labels
df_final = df_final[cols_order]
df_final = df_final.fillna(0)

# 3. 엑셀 파일로 저장
output_file = 'p1109/data/05_궁도별_당첨번호_배치표.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 4. openpyxl을 이용해 보너스 번호 초록색 및 (보) 표시 서식 적용
wb = openpyxl.load_workbook(output_file)
ws = wb.active

green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

for idx, b_info in enumerate(bonus_tracking):
  r_idx = idx + 2  # 헤더 제외 행 번호
  b_lbl = b_info['gung']
  b_val = b_info['val']

  col_idx = gung_labels.index(b_lbl) + 2  # 회차 컬럼 다음부터 시작하므로 +2
  cell = ws.cell(row=r_idx, column=col_idx)

  current_val = str(cell.value)
  if current_val == '0':
    cell.value = f'{b_val}(보)'
  else:
    cell.value = f'{current_val}, {b_val}(보)'

  cell.fill = green_fill
  cell.font = green_font

wb.save(output_file)
print(f'노트의 궁도 규칙 반영 완료! 파일이 [{output_file}]에 저장되었습니다.')