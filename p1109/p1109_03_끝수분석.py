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

ending_labels = [
    '1끝',
    '2끝',
    '3끝',
    '4끝',
    '5끝',
    '6끝',
    '7끝',
    '8끝',
    '9끝',
    '0끝',
]
table_rows = []

# 각 회차별로 번호와 보너스 번호를 함께 추적하기 위한 데이터 구성
for index, row in df_raw.iterrows():
  draw_no = row['회차']
  # 일반 당첨 번호 6개
  winning_nums = [
      row['번호1'],
      row['번호2'],
      row['번호3'],
      row['번호4'],
      row['번호5'],
      row['번호6'],
  ]
  # 보너스 번호
  bonus_num = row['보너스']

  row_data = {'회차': draw_no}
  for label in ending_labels:
    row_data[label] = []

  # 끝수 분류 함수 (0은 0끝으로 매칭)
  def get_ending_label(num):
    digit = num % 10
    if digit == 1:
      return '1끝'
    elif digit == 2:
      return '2끝'
    elif digit == 3:
      return '3끝'
    elif digit == 4:
      return '4끝'
    elif digit == 5:
      return '5끝'
    elif digit == 6:
      return '6끝'
    elif digit == 7:
      return '7끝'
    elif digit == 8:
      return '8끝'
    elif digit == 9:
      return '9끝'
    else:
      return '0끝'

  # 일반 당첨 번호 배치
  for num in winning_nums:
    lbl = get_ending_label(num)
    row_data[lbl].append(num)

  # 보너스 번호 배치 (보너스 번호임을 구별할 수 있도록 튜플 형태나 표식 추가 가능, 여기서는 값과 보너스 여부 함께 관리)
  # 엑셀에 문자열로 이쁘게 표현하기 위해 보너스는 별도 리스트나 표기법 적용 가능
  # 보기 편하게 보너스는 숫자 뒤에 (보)를 붙이거나 색상 구분을 위해 원본 값을 저장
  bonus_lbl = get_ending_label(bonus_num)

  formatted_row = {'회차': draw_no}
  for label in ending_labels:
    nums = row_data[label]
    # 해당 끝수에 당첨 번호가 있다면 정렬해서 문자열로
    if nums:
      formatted_row[label] = ', '.join(map(str, sorted(nums)))
    else:
      formatted_row[label] = 0  # 빈공간은 0으로 처리하여 오류 방지

  # 보너스 번호가 어느 끝수에 들어갔는지 기록하기 위해 따로 저장
  formatted_row['_bonus_val'] = bonus_num
  formatted_row['_bonus_lbl'] = bonus_lbl

  table_rows.append(formatted_row)

# 2. 데이터프레임 변환
df_final = pd.DataFrame(table_rows)

# 임시로 쓴 보너스 추적 컬럼은 분리하고 최종 컬럼 정렬
bonus_info = df_final[['_bonus_lbl', '_bonus_val']]
df_final = df_final.drop(columns=['_bonus_lbl', '_bonus_val'])

cols_order = ['회차'] + ending_labels
df_final = df_final[cols_order]

# 결측치(NaN)가 혹시 있다면 모두 0으로 치환
df_final = df_final.fillna(0)

# 3. 엑셀 파일로 저장
output_file = 'p1109/data/04_끝수별_당첨번호_배치표.xlsx'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_final.to_excel(output_file, index=False)

# 4. openpyxl을 이용해 보너스 번호 초록색 서식 적용
wb = openpyxl.load_workbook(output_file)
ws = wb.active

# 초록색 글꼴 및 배경 스타일 정의 (보너스용)
green_fill = PatternFill(
    start_color='E0F8E0', end_color='E0F8E0', fill_type='solid'
)
green_font = Font(name='맑은 고딕', size=10, bold=True, color='006400')

# 각 행을 돌면서 보너스 번호가 들어간 셀을 찾아 초록색으로 하이라이트
for idx, row_info in bonus_info.iterrows():
  r_idx = idx + 2  # 엑셀은 1행이 헤더이므로 +2부터 시작
  b_lbl = row_info['_bonus_lbl']
  b_val = row_info['_bonus_val']

  # 해당 끝수 컬럼 찾기 (끝수 레이블의 컬럼 인덱스 매칭)
  col_idx = ending_labels.index(b_lbl) + 2  # 회차 컬럼이 1번이므로 +2

  cell = ws.cell(row=r_idx, column=col_idx)
  # 기존 값에 보너스 번호가 포함되어 있으므로, 텍스트에 보너스 번호가 들어가 있다면 해당 셀에 스타일 적용
  # 혹은 보너스 번호를 명확히 구분하기 위해 셀 값에 표시
  current_val = str(cell.value)
  if str(b_val) not in current_val:
    if current_val == '0':
      cell.value = f'{b_val}(보)'
    else:
      cell.value = f'{current_val}, {b_val}(보)'
  else:
    cell.value = current_val.replace(str(b_val), f'{b_val}(보)')

  cell.fill = green_fill
  cell.font = green_font

wb.save(output_file)
print(
    f'보너스 번호(초록색) 및 빈공간 0 처리 완료! 파일이 [{output_file}]에 저장되었습니다.'
)