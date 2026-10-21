import pandas as pd
import glob
import os

script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
base_dir = script_dir if os.path.exists(os.path.join(script_dir, 'extracted_csvs')) else os.path.abspath(os.path.join(script_dir, '..'))

ages = ['20', '30', '40', '50', '60']

# total_by_generation 폴더 경로 확인 및 생성
target_total_dir = os.path.join(base_dir, 'extracted_csvs', 'total_by_generation')
if not os.path.exists(target_total_dir):
    os.makedirs(target_total_dir, exist_ok=True)

for age in ages:
    total_path = os.path.join(target_total_dir, f'total_{age}.csv')
    
    # 기존 파일 로드 또는 새 데이터프레임 생성
    if os.path.exists(total_path):
        df_total = pd.read_csv(total_path, encoding='utf-8')
        df_filtered = df_total[~df_total['지역코드'].isin(['gj', 'jn'])]
    else:
        df_filtered = pd.DataFrame(columns=['지역코드', '순위', '관광지ID', '관심지점명', '구분', '연령대', '비율', '위도', '경도'])

    # p_file 또는 각 지역 폴더에서 정제된 gj, jn 파일 병합
    sub_dfs = []
    for r_code in ['gj', 'jn']:
        folder = '광주광역시' if r_code == 'gj' else '전라남도'
        matched_files = glob.glob(os.path.join(base_dir, '**', folder, f'{r_code}_{age}.csv'), recursive=True)
        if matched_files:
            sub_dfs.append(pd.read_csv(matched_files[0], encoding='utf-8'))

    if sub_dfs:
        df_sub = pd.concat(sub_dfs, ignore_index=True)
        df_final = pd.concat([df_filtered, df_sub], ignore_index=True)
        df_final.to_csv(total_path, index=False, encoding='utf-8-sig')
        print(f"✅ total_{age}.csv 파일에 광주(gj) 및 전남(jn) 데이터 통합 완료!")

print("\n🎉 모든 세대별 통합 파일(total_20.csv ~ total_60.csv)에 위·경도 포함 데이터가 성공적으로 반영되었습니다!")