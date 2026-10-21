import json
import os
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
total_dir = os.path.join(script_dir, "total_by_generation")

# 데이터를 담을 구조체 초기화
dataset = {}

generations = ["20", "30", "40", "50", "60"]

if not os.path.exists(total_dir):
  print(f"❌ 오류: '{total_dir}' 폴더를 찾을 수 없습니다. 경로를 확인해 주세요.")
else:
  for gen in generations:
    file_path = os.path.join(total_dir, f"total_{gen}.csv")
    if os.path.exists(file_path):
      df = pd.read_csv(file_path, encoding="utf-8-sig")

      for _, row in df.iterrows():
        # 지역코드 가져오기 (없으면 기본 'gw')
        r_code = str(row.get("지역코드", "gw")).lower().strip()

        if r_code not in dataset:
          dataset[r_code] = {}
        if gen not in dataset[r_code]:
          dataset[r_code][gen] = []

        dataset[r_code][gen].append({
            "rank": int(row.get("순위", 1)),
            "name": str(row.get("관심지점명", "")),
            "cat": str(row.get("구분", "관광명소")),
            "ratio": f"{row.get('비율', 0)}%",
            "lat": float(row.get("위도", 37.5)),
            "lng": float(row.get("경도", 127.0)),
        })

  # JavaScript 파일로 저장 (HTML에서 바로 로드 가능)
  js_content = (
      "const REAL_TOUR_DATA ="
      f" {json.dumps(dataset, ensure_ascii=False, indent=2)};"
  )
  output_js_path = os.path.join(script_dir, "data.js")

  with open(output_js_path, "w", encoding="utf-8") as js_file:
    js_file.write(js_content)

  print("=" * 50)
  print(" 🎉 'data.js' 파일 변환 완료!")
  print(
      " 이제 사용자님이 조사하신 실제 데이터가 대시보드에 완벽하게"
      " 연동됩니다."
  )
  print("=" * 50)