import pandas as pd

def run_preprocessing():
    print("=== [가평 자라섬] 데이터 전처리 작업을 시작합니다 ===")
    
    # 1. 월별 검색량 데이터 불러오기 및 저장
    try:
        df_month = pd.read_csv('data/gapyeong/jarasum_month.csv', encoding='utf-8')
        print("\n✔ 1. 월별 검색량 파일 로드 성공!")
        df_month['검색량'] = df_month['검색량'].fillna(0)
        
        # 💡 [가공 완료된 1번 파일 저장!] 한글이 깨지지 않는 utf-8-sig로 저장합니다.
        df_month.to_csv('data/gapyeong/jarasum_month_clean.csv', index=False, encoding='utf-8-sig')
        print("👉 jarasum_month_clean.csv 파일 생성 완료!")
        
    except UnicodeDecodeError:
        df_month = pd.read_csv('data/gapyeong/jarasum_month.csv', encoding='cp949')
        print("\n✔ 1. 월별 검색량 파일 로드 성공! (cp949 대체인코딩)")
        df_month.to_csv('data/gapyeong/jarasum_month_clean.csv', index=False, encoding='utf-8-sig')
        print("👉 jarasum_month_clean.csv 파일 생성 완료!")
    except FileNotFoundError:
        print("\n❌ 1번 파일 경로를 찾을 수 없습니다.")


    # 2. 일별 방문 비율 데이터 불러오기 및 저장
    try:
        df_day = pd.read_csv('data/gapyeong/jarasum_day.csv', encoding='utf-8')
        print("\n✔ 2. 일별 방문 비율 파일 로드 성공!")
        df_day['기준연월'] = pd.to_datetime(df_day['기준연월'].astype(str), format='%Y%m%d')
        
        # 💡 [가공 완료된 2번 파일 저장!] 한글이 깨지지 않는 utf-8-sig로 저장합니다.
        df_day.to_csv('data/gapyeong/jarasum_day_clean.csv', index=False, encoding='utf-8-sig')
        print("👉 jarasum_day_clean.csv 파일 생성 완료!")
        
    except UnicodeDecodeError:
        df_day = pd.read_csv('data/gapyeong/jarasum_day.csv', encoding='cp949')
        print("\n✔ 2. 일별 방문 비율 파일 로드 성공! (cp949 대체인코딩)")
        df_day['기준연월'] = pd.to_datetime(df_day['기준연월'].astype(str), format='%Y%m%d')
        df_day.to_csv('data/gapyeong/jarasum_day_clean.csv', index=False, encoding='utf-8-sig')
        print("👉 jarasum_day_clean.csv 파일 생성 완료!")
    except Exception as e:
        print(f"\n❌ 2번 파일 처리 중 오류 발생: {e}")

    print("\n=== 모든 전처리 및 파일 저장 단계 완료 ===")

# 🔥 이 아래 엔진 부분은 절대 지우지 않고 그대로 둡니다!
if __name__ == '__main__':
    run_preprocessing()