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

result_data = []
max_rows = 40  # 넉넉한 행 수 설정

# 전체 1~45번 로또 번호 세트
all_lotto_nums = set(range(1, 46))

# 초기 상태: 1회차가 시작되기 전에는 모든 번호가 대기 중(미출수 상태)이라고 가정하거나,
# 혹은 1회차 당첨번호가 나오기 전 상태를 세팅합니다.
current_state = {i: [] for i in range(1, max_rows + 1)}

# 전체 회차를 순회하며 시뮬레이션 진행
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

  # [핵심 로직]
  # 현재 행(draw_no)에 기록될 내용은 '직전 회차까지의 상태' 혹은 당첨 직후의 상태입니다.
  # 사용자가 노트에 적으신 대로, 해당 회차 행에는 이전까지 누적된 미출수들이 아래로 밀려 내려간 상태가 기록되어야 합니다.

  # 1. 현재 회차의 상태를 먼저 결과에 기록 (이 행은 해당 회차 기준의 상태를 나타냄)
  row_result = {'회차': draw_no}
  for r in range(1, max_rows + 1):
    nums = current_state[r]
    for idx in range(6):
      if idx < len(nums):
        row_result[f'{r}행_번호{idx+1}'] = nums[idx]
      else:
        row_result[f'{r}행_번호{idx+1}'] = 0
  result_data.append(row_result)

  # 2. 이번 회차 당첨 번호가 기존 상태에 있다면 제거 (중복 방지)
  for r in range(1, max_rows + 1):
    current_state[r] = [
        num for num in current_state[r] if num not in winning_nums
    ]

  # 3. 기존 번호들을 한 칸씩 아래로 밀어냄
  for r in range(max_rows, 1, -1):
    current_state[r] = current_state[r - 1].copy()

  # 4. 이번 회차 당첨 번호를 맨 위(1행)에 올림
  current_state[1] = winning_nums.copy()

# 만약 마지막 회차 다음 회차(예: 1250회)까지 빈 행으로 표현하고 싶다면 추가 가능
# (현재 데이터의 마지막 회차 기준 다음 회차 행 추가)
last_draw = df_raw['회차'].max()
next_draw_row = {'회차': last_draw + 1}
for r in range(1, max_rows + 1):
  nums = current_state[r]
  for idx in range(6):
    if idx < len(nums):
      next_draw_row[f'{r}행_번호{idx+1}'] = nums[idx]
    else:
      next_draw_row[f'{r}행_번호{idx+1}'] = 0
result_data.append(next_draw_row)

df_result = pd.DataFrame(result_data)
df_result = df_result.fillna(0)

# 엑셀 파일 저장
output_file = 'p1109/data/02_장기미출수_시뮬레이션결과.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_result.to_excel(output_file, index=False)

# 2. openpyxl 서식 및 색상 적용
wb = openpyxl.load_workbook(output_file)
ws = wb.active

sec1_fill = PatternFill(
    start_color='EBF1F5', end_color='EBF1F5', fill_type='solid'
)
sec2_fill = PatternFill(
    start_color='F2F5EB', end_color='F2F5EB', fill_type='solid'
)
sec3_fill = PatternFill(
    start_color='FDF5E6', end_color='FDF5E6', fill_type='solid'
)

purple_fill = PatternFill(
    start_color='E6E6FA', end_color='E6E6FA', fill_type='solid'
)
purple_font = Font(name='맑은 고딕', size=10, bold=True, color='4B0082')

green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

for r_idx in range(2, ws.max_row + 1):
  draw_no = ws.cell(row=r_idx, column=1).value
  if draw_no is None:
    continue

  match_row = df_raw[df_raw['회차'] == draw_no]
  if match_row.empty:
    continue  # 다음 회차 등 매칭 안 되는 행 스킵

  winning_set = set(
      match_row[['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']].values[0]
  )
  bonus_val = match_row['보너스'].values[0]

  for c_idx in range(2, ws.max_column + 1):
    cell = ws.cell(row=r_idx, column=c_idx)
    val = cell.value

    if 2 <= c_idx <= 31:
      cell.fill = sec1_fill
    elif 32 <= c_idx <= 61:
      cell.fill = sec2_fill
    else:
      cell.fill = sec3_fill

    if val in winning_set and val != 0:
      cell.fill = purple_fill
      cell.font = purple_font
    elif val == bonus_val and val != 0:
      cell.fill = green_fill
      cell.font = green_font

wb.save(output_file)
print(f'회차별 미출수 정렬 및 시뮬레이션 완료! [{output_file}] 파일이 갱신되었습니다.')