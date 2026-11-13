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

# 20코스트 레이블 정의 (A ~ T) 및 마지막 요약 칸 2개
cost_labels = [
    'A',
    'B',
    'C',
    'D',
    'E',
    'F',
    'G',
    'H',
    'I',
    'J',
    'K',
    'L',
    'M',
    'N',
    'O',
    'P',
    'Q',
    'R',
    'S',
    'T',
]
summary_labels = ['F~N', 'A~E / O~T']


# 노트에 적힌 20코스트 분류 매핑 함수 (수정 반영)
def get_cost_label(num):
  if num in [10]:
    return 'A'
  elif num in [24]:
    return 'B'
  elif num in [6]:
    return 'C'
  elif num in [9]:
    return 'D'
  elif num in [13]:
    return 'E'
  elif num in [15, 35, 37, 40]:
    return 'F'
  elif num in [1, 8, 44]:
    return 'G'
  elif num in [2, 23, 43]:
    return 'H'
  elif num in [21, 30, 33]:
    return 'I'
  elif num in [18, 42, 45]:
    return 'J'
  elif num in [14, 16, 22, 28, 38, 39]:
    return 'K'
  elif num in [17, 19, 26]:
    return 'L'
  elif num in [5, 32, 34]:
    return 'M'
  elif num in [3, 4, 27]:
    return 'N'
  elif num in [7, 11]:
    return 'O'
  elif num in [12, 25]:
    return 'P'
  elif num in [29, 36]:
    return 'Q'
  elif num in [41]:
    return 'R'
  elif num in [31]:
    return 'S'
  elif num in [20]:
    return 'T'
  return 'A'  # 예외 번호 기본값


table_rows = []
bonus_tracking = []

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
  for label in cost_labels:
    row_data[label] = []

  # 일반 당첨 번호 코스트에 배치
  for num in winning_nums:
    c_lbl = get_cost_label(num)
    row_data[c_lbl].append(num)

  # 보너스 번호 코스트 확인
  bonus_cost = get_cost_label(bonus_num)
  bonus_tracking.append({'cost': bonus_cost, 'val': bonus_num})

  # --- 요약 칸 계산 (`F~N`, `A~E / O~T`) ---
  # 1. F~N 구간: F, G, H, I, J, K, L, M, N 코스트에 포함된 당첨 번호 총 개수
  fn_group = ['F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
  fn_count = sum(len(row_data[c]) for c in fn_group)
  if bonus_cost in fn_group:
    fn_str = f"{fn_count}'" if fn_count > 0 else "0'"
  else:
    fn_str = str(fn_count)

  # 2. A~E / O~T 구간: A, B, C, D, E 및 O, P, Q, R, S, T 코스트에 포함된 당첨 번호 총 개수
  aeot_group = ['A', 'B', 'C', 'D', 'E', 'O', 'P', 'Q', 'R', 'S', 'T']
  aeot_count = sum(len(row_data[c]) for c in aeot_group)
  if bonus_cost in aeot_group:
    aeot_str = f"{aeot_count}'" if aeot_count > 0 else "0'"
  else:
    aeot_str = str(aeot_count)

  # 데이터프레임용 딕셔너리 구성
  formatted_row = {'회차': draw_no}
  for label in cost_labels:
    nums = row_data[label]
    if nums:
      formatted_row[label] = ', '.join(map(str, sorted(nums)))
    else:
      formatted_row[label] = 0  # 빈공간 0 처리

  # 요약 컬럼 값 세팅
  formatted_row['F~N'] = fn_str
  formatted_row['A~E / O~T'] = aeot_str

  table_rows.append(formatted_row)

# 2. 데이터프레임 변환
df_final = pd.DataFrame(table_rows)
cols_order = ['회차'] + cost_labels + summary_labels
df_final = df_final[cols_order]
df_final = df_final.fillna(0)

# 3. 엑셀 파일로 저장
output_file = 'p1109/data/07_20코스트_당첨번호_배치표.xlsx'
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
  b_lbl = b_info['cost']
  b_val = b_info['val']

  col_idx = cost_labels.index(b_lbl) + 2  # 회차 컬럼 다음부터 시작하므로 +2
  cell = ws.cell(row=r_idx, column=col_idx)

  current_val = str(cell.value)
  if current_val == '0':
    cell.value = f'{b_val}(보)'
  else:
    cell.value = f'{current_val}, {b_val}(보)'

  cell.fill = green_fill
  cell.font = green_font

wb.save(output_file)
print(f'20코스트 매핑 수정 완료! 파일이 [{output_file}]에 저장되었습니다.')