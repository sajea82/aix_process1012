import glob
import json
import os
import pandas as pd

# 1. total_gen 폴더 안의 모든 CSV 파일 경로 가져오기
csv_files = glob.glob("total_gen/total_*.csv")
total_data = {}

for file_path in csv_files:
  # 파일 이름 추출 (예: total_20.csv -> total_20)
  file_name = os.path.basename(file_path)
  key_name = os.path.splitext(file_name)[0]

  # CSV 읽기 (인코딩 문제 발생 시 utf-8 또는 cp949 지정)
  df = pd.read_csv(file_path, encoding="utf-8")

  # 결측치(NaN)가 있으면 자바스크립트에서 에러가 날 수 있으므로 빈 문자열 등으로 처리 가능
  df = df.fillna("")

  # 딕셔너리 형태로 변환하여 저장
  total_data[key_name] = df.to_dict(orient="records")

# 2. 자바스크립트 파일 형식(const 변수)으로 문자열 생성
js_content = (
    "// 자동으로 생성된 데이터 파일입니다.\nconst totalData ="
    f" {json.dumps(total_data, ensure_ascii=False, indent=4)};\n"
)

# 3. 바깥쪽 경로에 data.js 파일로 저장
output_path = "data.js"
with open(output_path, "w", encoding="utf-8") as f:
  f.write(js_content)

print(f"성공! {output_path} 파일이 최신 CSV 데이터로 업그레이드되었습니다.")