from django.conf import settings
from django.shortcuts import render
import os
import pandas as pd


def index(request):
  return render(request, 'index.html')

def detail(request):
  # 사용자가 클릭한 지역 이름 가져오기 (예: '서울특별시')
  region_name = request.GET.get('region', '기본지역')

  # 나중에 이 지역에 맞는 세부 데이터나 CSV 파일을 여기서 불러올 수 있습니다.
  context = {'region_name': region_name}
  return render(request, 'detail.html', context)


def sample(request):
  # 1. 메인 배너 슬라이드 이미지
  banner_images = [
      'seoul/경복궁.jpg',
      'jj/금오름.jpg',
      'bs/태종대.jpg',
      'dj/갑천생태호수공원.jpg',
  ]

  # 2. 전국 17개 지역 파노라마 데이터 (17개 전체 준비)
  regions_data = [
      {'name': '서울특별시', 'desc': '전통과 현대가 공존하는 수도', 'img': 'seoul/경복궁.jpg'},
      {'name': '부산광역시', 'desc': '푸른 바다와 해변 도시', 'img': 'bs/범어사.jpg'},
      {'name': '강원특별자치도', 'desc': '청정 자연과 힐링 산림', 'img': 'gw/낙산사.jpg'},
      {'name': '제주특별자치도', 'desc': '사계절 아름다운 환상의 섬', 'img': 'jj/금오름.jpg'},
      {'name': '인천광역시', 'desc': '바다와 공항이 있는 항구 도시', 'img': 'ic/월미도.jpg'}, # 파일명에 맞춰 추가 가능
      {'name': '대구광역시', 'desc': '분수와 맛의 도시', 'img': 'dg/이월드.jpg'},
      {'name': '대전광역시', 'desc': '과학과 교통의 중심', 'img': 'dj/대전아쿠아리움.jpg'},
      {'name': '광주광역시', 'desc': '예술과 민주주의의 고향', 'img': 'gj/국립광주과학관.jpg'},
      # ... 필요에 따라 17개 지역 모두 추가 가능합니다 ...
  ]

  # 3. static/file 폴더의 세대별 CSV 파일에서 실제 통계치 읽어오기
  file_dir = os.path.join(settings.BASE_DIR, 'static', 'file')
  
  # 각 파일에서 상위 1위 장고 데이터를 안전하게 읽는 함수
  def get_top_place(filename):
      try:
          df = pd.read_csv(os.path.join(file_dir, filename))
          top_row = df.iloc[0] # 가장 첫 번째 행(1위)
          return {
              'top_place': f"{top_row['시군구']} {top_row['관심지점명']}",
              'ratio': f"{top_row['비율']}%",
              'keyword': top_row['구분']
          }
      except:
          return {'top_place': '데이터 준비중', 'ratio': '0%', 'keyword': '기타'}

  age_stats_data = [
      {'age': '20대', **get_top_place('total_20_corrected.csv')},
      {'age': '30대', **get_top_place('total_30_corrected.csv')},
      {'age': '40대', **get_top_place('total_40_corrected.csv')},
      {'age': '50대', **get_top_place('total_50_corrected.csv')},
      {'age': '60대 이상', **get_top_place('total_60_corrected.csv')},
  ]

  context = {
      'banner_imgs': banner_images,
      'regions': regions_data,
      'age_stats': age_stats_data,
  }
  return render(request, 'sample.html', context)