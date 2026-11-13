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

# 13코스트 레이블 정의 (A ~ M) 및 요약 컬럼
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
]
summary_labels = ['D/J', 'A·C / K·M']


# 노트에 적힌 13코스트 분류 매핑 함수
def get_cost_label(num):
  if num in [10]:
    return 'A'
  elif num in [6, 31]:
    return 'B'
  elif num in [35, 40]:
    return 'C'
  elif num in [7, 9, 11, 43]:
    return 'D'
  elif num in [1, 13, 25, 37]:
    return 'E'
  elif num in [2, 4, 23, 27, 28]:
    return 'F'
  elif num in [16, 19, 21, 22, 33, 34, 39]:
    return 'G'
  elif num in [18, 30, 32, 38, 42]:
    return 'H'
  elif num in [5, 14, 17, 26, 45]:
    return 'I'
  elif num in [3, 8, 12, 44]:
    return 'J'
  elif num in [15, 29, 36]:
    return 'K'
  elif num in [24, 41]:
    return 'L'
  elif num in [20]:
    return 'M'
  return 'A'


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

  # --- [핵심 수정] D~J 구간 및 A·C/K·M 구간에 포함된 당첨 번호 총 개수 정밀 계산 ---
  # 1. D/J 구간: D, E, F, G, H, I, J 코스트에 포함된 당첨 번호들의 총 개수
  dj_group = ['D', 'E', 'F', 'G', 'H', 'I', 'J']
  dj_count = sum(len(row_data[c]) for c in dj_group)

  # 보너스가 이 구간에 포함되었다면 개수 뒤에 작은따옴표(') 추가
  if bonus_cost in dj_group:
    dj_str = f"{dj_count}'" if dj_count > 0 else "0'"
  else:
    dj_str = str(dj_count)

  # 2. A·C / K·M 구간: A, B(혹은 C), K, M 등 노트에 지정된 그룹의 당첨 번호 총 개수
  ackm_group = ['A', 'C', 'K', 'M']
  ackm_count = sum(len(row_data[c]) for c in ackm_group)

  if bonus_cost in ackm_group:
    ackm_str = f"{ackm_count}'" if ackm_count > 0 else "0'"
  else:
    ackm_str = str(ackm_count)

  # 데이터프레임용 딕셔너리 구성
  formatted_row = {'회차': draw_no}
  for label in cost_labels:
    nums = row_data[label]
    if nums:
      formatted_row[label] = ', '.join(map(str, sorted(nums)))
    else:
      formatted_row[label] = 0  # 빈공간 0 처리

  # 요약 컬럼 값 세팅
  formatted_row['D/J'] = dj_str
  formatted_row['A·C / K·M'] = ackm_str

  table_rows.append(formatted_row)

# 2. 데이터프레임 변환
df_final = pd.DataFrame(table_rows)
cols_order = ['회차'] + cost_labels + summary_labels
df_final = df_final[cols_order]
df_final = df_final.fillna(0)

# 3. 엑셀 파일로 저장
output_file = 'p1109/data/06_13코스트_당첨번호_배치표.xlsx'
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
print(f'구간별 당첨 개수 산출 로직 수정 완료! [{output_file}]')