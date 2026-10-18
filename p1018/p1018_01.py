import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# 1. 한글 폰트 설정 (Windows 한글 깨짐 방지)
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

print("="*50)
print("🚀 [1/3] 기존 지역별 TEL/MEP 데이터 전처리 시작...")
print("="*50)

# -------------------------------------------------------------------
# [PART 1] 기존 파일 전처리 (file/ 폴더 내 cb_mep, cn_mep, jn_mep 등)
# -------------------------------------------------------------------
file_dir = './file' # 또는 'p1018/file'
tel_mep_files = glob.glob(os.path.join(file_dir, '*.csv'))

region_summary = []

for f in tel_mep_files:
    fname = os.path.basename(f)
    # 인코딩 자동 시도
    df = None
    for enc in ['cp949', 'euc-kr', 'utf-8']:
        try:
            df = pd.read_csv(f, encoding=enc)
            break
        except:
            continue
            
    if df is not None:
        print(f"✅ 읽기 성공: {fname} (행 수: {len(df)})")
        # 데이터 집계 로직
        region_summary.append({
            '파일명': fname,
            '총_데이터_건수': len(df)
        })

print("\n" + "="*50)
print("🚀 [2/3] 연령대별(ALL_TOP_MEP) 데이터 통합 및 3개 지역 필터링...")
print("="*50)

# -------------------------------------------------------------------
# [PART 2] 연령대별 파일 전처리 (all_top_mep/ 폴더 내 파일들)
# -------------------------------------------------------------------
all_top_dir = './all_top_mep' # 또는 'p1018/all_top_mep'
all_top_files = glob.glob(os.path.join(all_top_dir, '*.csv'))

age_dfs = []

for f in all_top_files:
    fname = os.path.basename(f)
    
    # 연령대 판별
    age_tag = '기타'
    for age in ['20', '30', '40', '50', '60']:
        if age in fname:
            age_tag = f'{age}대'
            break
            
    for enc in ['cp949', 'euc-kr', 'utf-8']:
        try:
            df_age = pd.read_csv(f, encoding=enc)
            df_age['연령대_구분'] = age_tag
            age_dfs.append(df_age)
            print(f"✅ 연령대 파일 통합 완료: {fname} -> [{age_tag}]")
            break
        except:
            continue

# 모든 연령대 데이터 하나로 결합
if age_dfs:
    df_all_ages = pd.concat(age_dfs, ignore_index=True)
    
    # -------------------------------------------------------------------
    # [PART 3] 3개 특정 권역(충남, 충북, 전남·광주) 필터링 및 시각화
    # -------------------------------------------------------------------
    target_keywords = ['충남', '충청남도', '천안', '아산', '공주', '태안', '보령',
                       '충북', '충청북도', '청주', '충주', '단양', '제천',
                       '전남', '전라남도', '광주', '여수', '순천', '목포']
    
    # '관심지점명' 또는 '관광지명' 컬럼 자동 찾기
    target_col = '관심지점명' if '관심지점명' in df_all_ages.columns else '관광지명'
    
    mask = df_all_ages[target_col].apply(lambda x: any(kw in str(x) for kw in target_keywords))
    df_3regions = df_all_ages[mask].copy()
    
    # 전처리 완료된 데이터 CSV로 최종 저장
    df_3regions.to_csv('final_3regions_all_data.csv', index=False, encoding='utf-8-sig')
    print("\n🎉 최종 3개 지역 통합 데이터 저장 완료: final_3regions_all_data.csv")

    # 연령대별 Top 10 시각화 그래프 자동 생성 및 저장
    for age in ['20대', '30대', '40대', '50대', '60대']:
        sub = df_3regions[df_3regions['연령대_구분'] == age]
        if not sub.empty:
            top10 = sub.head(10).sort_values(by=sub.columns[-2] if '비율' not in sub.columns else '비율', ascending=True)
            
            plt.figure(figsize=(10, 5))
            val_col = '비율' if '비율' in sub.columns else sub.columns[-2]
            plt.barh(top10[target_col], top10[val_col], color='skyblue')
            plt.title(f'[{age}] 충청 및 전남광주권 선호 장소 TOP 10', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f'graph_top10_{age}.png', dpi=300)
            plt.close()
            print(f"📊 그래프 저장 완료: graph_top10_{age}.png")

print("\n" + "="*50)
print("✨ 모든 전처리 및 시각화 작업이 성공적으로 끝났습니다!")
print("="*50)