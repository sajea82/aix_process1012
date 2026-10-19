import glob
import os
import pandas as pd

# 전남광주(jn) 파일들이 있는 경로
pfile_dir = "./p1019/pfile"

# 전남광주 연령대별 파일 매핑
jn_files = {
    "20대": os.path.join(pfile_dir, "jn_p20.csv"),
    "30대": os.path.join(pfile_dir, "jn_p30.csv"),
    "40대": os.path.join(pfile_dir, "jn_p40.csv"),
    "50대": os.path.join(pfile_dir, "jn_p50.csv"),
    "60대": os.path.join(pfile_dir, "jn_p60.csv"),
}

print("=" * 60)
print(" 🗺️ 전남광주 연령대별 TOP 10 관광지 및 유니크 장소 분석")
print("=" * 60)

place_ages = {}

for age, filepath in jn_files.items():
  if os.path.exists(filepath):
    df = pd.read_csv(filepath)
    # 순위 1~10위 필터링 및 정렬
    top10 = df[df["순위"] <= 10].sort_values("순위")
    print(f"\n📍 [{age} TOP 10]")
    for _, row in top10.iterrows():
      place = row["관심지점명"]
      category = row["구분"]
      ratio = row["비율"]
      print(
          f"  {str(row['순위']).zfill(2)}위 | {place} ({category}) - 검색비율:"
          f" {ratio}%"
      )

      # 유니크 장소 수집 (어떤 연령대에 등장했는지 기록)
      if place not in place_ages:
        place_ages[place] = []
      place_ages[place].append(age)
  else:
    print(f"\n[{age}] 파일을 찾을 수 없습니다: {filepath}")

print("\n" + "=" * 60)
print(" 🖼️ 이미지 수집용 전체 유니크 장소 통합 리스트 (중복 1회 표기)")
print("=" * 60)
for place, ages in place_ages.items():
  ages_str = ", ".join(ages)
  print(f"* **{place}** ({ages_str})")

print(f"\n총 유니크 장소 개수: {len(place_ages)}곳")
print("=" * 60)