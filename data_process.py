import pandas as pd

def run_preprocessing():
    # ==========================================
    # 🌲 1. 가평 자라섬 데이터 전처리
    # ==========================================
    print("=== [가평 자라섬] 데이터 전처리 작업을 시작합니다 ===")
    try:
        df_month = pd.read_csv('data/gapyeong/jarasum_month.csv', encoding='utf-8')
        df_month['검색량'] = df_month['검색량'].fillna(0)
        df_month.to_csv('data/gapyeong/jarasum_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 가평 월별 검색량 clean 파일 생성 완료!")
    except UnicodeDecodeError:
        df_month = pd.read_csv('data/gapyeong/jarasum_month.csv', encoding='cp949')
        df_month.to_csv('data/gapyeong/jarasum_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 가평 월별 검색량 clean 파일 생성 완료! (cp949)")
    except FileNotFoundError:
        print("❌ 가평 1번 파일 경로를 찾을 수 없습니다.")

    try:
        df_day = pd.read_csv('data/gapyeong/jarasum_day.csv', encoding='utf-8')
        df_day['기준연월'] = pd.to_datetime(df_day['기준연월'].astype(str), format='%Y%m%d')
        df_day.to_csv('data/gapyeong/jarasum_day_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 가평 일별 방문 비율 clean 파일 생성 완료!")
    except UnicodeDecodeError:
        df_day = pd.read_csv('data/gapyeong/jarasum_day.csv', encoding='cp949')
        df_day['기준연월'] = pd.to_datetime(df_day['기준연월'].astype(str), format='%Y%m%d')
        df_day.to_csv('data/gapyeong/jarasum_day_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 가평 일별 방문 비율 clean 파일 생성 완료! (cp949)")
    except Exception as e:
        print(f"❌ 가평 2번 파일 처리 중 오류: {e}")


    # ==========================================
    # 🌾 2. 순천만 생태공원 데이터 전처리 (추가된 파트!)
    # ==========================================
    print("\n=== [순천만 생태공원] 데이터 전처리 작업을 시작합니다 ===")
    try:
        # 💡 아까 정리한 sc_month.csv 파일을 순천 폴더 경로에서 읽어옵니다.
        df_sc_month = pd.read_csv('data/suncheon/sc_month.csv', encoding='utf-8')
        
        # [전처리] 컬럼명 확인 후 목적지 검색량(또는 검색량) 결측치 채우기
        # 데이터랩 단독 관광지 파일은 컬럼명이 '검색량' 혹은 '내비게이션 목적지 검색량'일 수 있습니다.
        # 여기서는 안전하게 전체 결측치를 0으로 채웁니다.
        df_sc_month = df_sc_month.fillna(0)
        
        # [저장] 순천 전용 clean 파일로 내보냅니다.
        df_sc_month.to_csv('data/suncheon/sc_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 순천 월별 검색량 clean 파일 생성 완료!")
        
    except UnicodeDecodeError:
        df_sc_month = pd.read_csv('data/suncheon/sc_month.csv', encoding='cp949')
        df_sc_month = df_sc_month.fillna(0)
        df_sc_month.to_csv('data/suncheon/sc_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 순천 월별 검색량 clean 파일 생성 완료! (cp949)")
    except FileNotFoundError:
        print("❌ 순천 sc_month.csv 파일 경로를 찾을 수 없습니다. 폴더명이나 파일명을 확인해주세요.")
    except Exception as e:
        print(f"❌ 순천 파일 처리 중 오류 발생: {e}")

    print("\n=== 모든 지역 전처리 및 파일 저장 단계 완료 ===")


    # ==========================================
    # 🌸 3. 양주 나리공원 데이터 전처리 (새로 추가된 3층!)
    # ==========================================
    print("\n=== [양주 나리공원] 데이터 전처리 작업을 시작합니다 ===")
    try:
        # 💡 nari_month.csv 파일을 양주 폴더 경로에서 읽어옵니다.
        df_nari_month = pd.read_csv('data/yangju/nari_month.csv', encoding='utf-8')
        df_nari_month = df_nari_month.fillna(0)
        
        # [저장] 양주 전용 clean 파일로 내보냅니다.
        df_nari_month.to_csv('data/yangju/nari_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 양주 월별 검색량 clean 파일 생성 완료!")
        
    except UnicodeDecodeError:
        df_nari_month = pd.read_csv('data/yangju/nari_month.csv', encoding='cp949')
        df_nari_month = df_nari_month.fillna(0)
        df_nari_month.to_csv('data/yangju/nari_month_clean.csv', index=False, encoding='utf-8-sig')
        print("✔ 양주 월별 검색량 clean 파일 생성 완료! (cp949)")
    except FileNotFoundError:
        print("❌ 양주 nari_month.csv 파일 경로를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 양주 파일 처리 중 오류 발생: {e}")

    print("\n=== 모든 지역 전처리 및 파일 저장 단계 완료 ===")

if __name__ == '__main__':
    run_preprocessing()