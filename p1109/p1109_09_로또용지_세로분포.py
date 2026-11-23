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


# 1구~7구 매핑 함수 (7로 나눈 나머지 기준)
def get_column_group(num):
  rem = num % 7
  if rem == 1:
    return '1구'
  elif rem == 2:
    return '2구'
  elif rem == 3:
    return '3구'
  elif rem == 4:
    return '4구'
  elif rem == 5:
    return '5구'
  elif rem == 6:
    return '6구'
  elif rem == 0:
    return '7구'
  return '1구'


rows_to_excel = []
groups = ['1구', '2구', '3구', '4구', '5구', '6구', '7구']

for index, row in df_raw.iterrows():
  draw_no = row['회차']
  winning_nums = [int(row[f'번호{i}']) for i in range(1, 7)]
  bonus_num = int(row['보너스'])

  all_nums = winning_nums + [bonus_num]
  group_data = {g: [] for g in groups}

  for n in all_nums:
    g_name = get_column_group(n)
    if n == bonus_num:
      group_data[g_name].append(f'{n}(보)')
    else:
      group_data[g_name].append(str(n))

  row_dict = {'회차': f'{draw_no}회'}
  for g in groups:
    nums = group_data[g]
    # 값이 없는 칸은 빈 문자열 대신 숫자 0 입력
    row_dict[g] = ', '.join(nums) if nums else 0

  rows_to_excel.append(row_dict)

# 2. 데이터프레임 변환 및 빈 문자열/결측치 모두 0으로 치환
df_final = pd.DataFrame(rows_to_excel)
df_final = df_final.fillna(0).replace('', 0)

output_file = 'p1109/data/15_로또용지_세로분포_1구~7구_결측치0.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 3. openpyxl을 이용한 상세 서식 적용 (보너스 초록색, 당첨번호 보라색, 0은 회색)
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
  for c_idx in range(2, 9):  # 1구 ~ 7구 (B열 ~ H열)
    cell = ws.cell(row=r_idx, column=c_idx)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    val = str(cell.value)

    if val == '0' or val == '0.0':
      cell.font = Font(
          name='맑은 고딕', size=10, color='888888'
      )  # 0은 연한 회색 처리
    elif '(보)' in val:
      cell.fill = green_fill
      cell.font = green_font
    else:
      cell.font = purple_font

wb.save(output_file)
print('세로 분포 표 최종 코드 실행 완료:', output_file)