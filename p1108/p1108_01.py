import pandas as pd

# 파일 경로 지정 (file 폴더 안에 있으므로 경로 맞춤)
file_path = "p1108/file/lotto.xlsx"

try:
    # 엑셀 파일 읽기 (동행복권 엑셀 파일은 상단에 타이틀 행이 있을 수 있어 header 지정이 필요할 수 있습니다)
    df = pd.read_excel(file_path)
    
    print("=== 엑셀 파일 로드 성공! ===")
    print(f"데이터 크기 (행, 열): {df.shape}")
    print("\n--- 컬럼 목록 ---")
    print(df.columns)
    
    print("\n--- 상단 데이터 (Head 5행) ---")
    print(df.head())
    
except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")