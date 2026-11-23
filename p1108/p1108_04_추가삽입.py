import pandas as pd

# 1. 기존 엑셀 파일 경로
file_path = r'C:\workspace\process\aix_process1012\p1108\file/lotto.xlsx'

# 2. 기존 데이터 불러오기
df = pd.read_excel(file_path)

# 3. 추가할 1250회 데이터 만들기 (이미지 속 열 이름과 동일하게 맞춤)
new_row = pd.DataFrame([{
    '회차': 1250,
    '번호1': 1,
    '번호2': 5,
    '번호3': 18,
    '번호4': 23,
    '번호5': 27,
    '번호6': 28,
    '보너스': 8,
}])

# 4. 새 데이터를 맨 위에 배치하고 기존 데이터와 합치기
updated_df = pd.concat([new_row, df], ignore_index=True)

# 5. 원래 파일에 덮어쓰기 (index=False를 해야 왼쪽에 불필요한 번호 열이 안 생깁니다)
updated_df.to_excel(file_path, index=False)

print('1250회 추가 및 저장 완료!')