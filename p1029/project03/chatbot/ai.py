
# ------------------------------------------------------------
# 맞춤추천 AI 챗봇의 두뇌
#  1) 질문에서 지역·시군구·연령대·기간·동행을 찾아낸다
#  2) Tour 데이터에서 조건에 맞는 관광지를 골라 AI에게 전달한다
#  3) food_data.csv에서 지역별 점심·저녁 정보를 가져온다
#  4) AI 키가 있으면 AI 답변, 없거나 실패하면 기본 응답
# ------------------------------------------------------------

import os
import re
import math
import csv
import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from django.conf import settings

from tour.models import Tour
from tour.regions import REGIONS


load_dotenv(settings.BASE_DIR / '.env')


# ------------------------------------------------------------
# 지역 정보
# ------------------------------------------------------------

REGION_NAME = dict(REGIONS)

REGION_WORDS = {
    name: code for code, name in REGIONS
}

REGION_WORDS.update({
    '제주도': 'jj',
    '강원도': 'gw',
    '경기도': 'gg',
    '전라북도': 'jb',
    '전북특별자치도': 'jb',
    '전라남도': 'jn',
    '경상북도': 'gb',
    '경상남도': 'gn',
    '충청북도': 'cb',
    '충청남도': 'cn',
    '광안리': 'bs',
    '우도': 'jj',
})


DAY_WORDS = {
    '2박3일': ['2박3일', '2박 3일'],
    '1박2일': ['1박2일', '1박 2일'],
    '당일치기': ['당일치기', '당일', '하루'],
}

MATE_WORDS = {
    '부모님': ['부모', '엄마', '아빠', '어머니', '아버지', '효도'],
    '연인': ['연인', '여자친구', '남자친구', '애인', '데이트', '커플'],
    '가족': ['가족', '아이', '아들', '딸', '애들'],
    '친구': ['친구', '동기'],
    '혼자': ['혼자', '나홀로', '혼행'],
}

CATEGORY_WORDS = {
    '관광명소': ['바다', '해변', '해수욕장', '공원', '자연', '명소', '산책'],
    '레저/스포츠': ['레저', '스포츠', '액티비티', '놀이', '체험'],
    '문화생활시설': ['문화', '박물관', '전시', '미술관', '공연'],
    '종교': ['사찰', '절', '성당', '종교'],
}


QUICK_START = [
    '20대 부산 1박2일 코스 짜줘',
    '부모님과 가기 좋은 경북 여행',
    '강릉 당일치기 추천해줘',
    '30대가 많이 가는 제주 관광지는?',
]


# ------------------------------------------------------------
# 추가 기능 1. 음식 CSV 불러오기
# ------------------------------------------------------------

FOOD_CSV_PATH = Path(settings.BASE_DIR) / 'data' / 'food_data.csv'


def load_food_data():
    """
    data/food_data.csv를 읽어 음식 정보 반환

    CSV 컬럼:
    지역코드, 지역명, 연관관광지,
    식사구분, 추천음식및장소, 설명
    """

    if not FOOD_CSV_PATH.exists():
        print('음식 CSV 파일을 찾을 수 없습니다:', FOOD_CSV_PATH)
        return []

    try:
        with FOOD_CSV_PATH.open(
            'r',
            encoding='utf-8-sig',
            newline=''
        ) as file:

            reader = csv.DictReader(file)
            return list(reader)

    except Exception as e:
        print('음식 CSV 읽기 오류:', e)
        return []


def normalize_region_name(name):
    """
    지역 이름 표기를 비교하기 쉽게 변환
    예: 부산광역시 → 부산
    """

    name = str(name or '').strip()

    aliases = {
        '서울특별시': '서울',
        '부산광역시': '부산',
        '대구광역시': '대구',
        '인천광역시': '인천',
        '광주광역시': '광주',
        '대전광역시': '대전',
        '울산광역시': '울산',
        '세종특별자치시': '세종',
        '경기도': '경기',
        '강원특별자치도': '강원',
        '강원도': '강원',
        '충청북도': '충북',
        '충청남도': '충남',
        '전북특별자치도': '전북',
        '전라북도': '전북',
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주',
        '제주도': '제주',
    }

    return aliases.get(name, name)


def pick_foods(cond):
    """
    선택한 지역에 맞는 음식 데이터 조회

    관광지는 기존 Tour 데이터에서 가져오고
    음식만 CSV에서 가져온다.
    """

    region_code = cond.get('region')

    if not region_code:
        return []

    region_name = normalize_region_name(
        REGION_NAME.get(region_code, '')
    )

    # 기존 Tour 코드와 CSV 코드가 다를 수 있어
    # 대표적인 코드 차이를 보완한다.
    code_aliases = {
        'bs': 'busan',
        'busan': 'bs',
        'dg': 'daegu',
        'daegu': 'dg',
        'ic': 'incheon',
        'incheon': 'ic',
        'gj': 'gj',
        'dj': 'daejeon',
        'daejeon': 'dj',
        'us': 'ulsan',
        'ulsan': 'us',
        'sj': 'sejong',
        'sejong': 'sj',
        'se': 'seoul',
        'seoul': 'se',
    }

    valid_codes = {
        region_code,
        code_aliases.get(region_code, region_code)
    }

    result = []

    for food in load_food_data():

        food_code = food.get('지역코드', '').strip()

        food_region = normalize_region_name(
            food.get('지역명', '')
        )

        if (
            food_code in valid_codes
            or food_region == region_name
        ):
            result.append(food)

    return result


def make_food_context(cond):
    """
    AI에게 전달할 음식 참고자료 생성
    """

    foods = pick_foods(cond)

    if not foods:
        return ''

    lines = []

    for food in foods:

        meal = food.get('식사구분', '')
        spot = food.get('추천음식및장소', '')
        related = food.get('연관관광지', '')
        description = food.get('설명', '')

        lines.append(
            f"- {meal}: {spot}\n"
            f"  연관 관광지: {related}\n"
            f"  설명: {description}"
        )

    return '\n'.join(lines)


# ------------------------------------------------------------
# 기존 기능 1. 질문 분석
# ------------------------------------------------------------

def find_one(text, table, default=None):

    for key, words in table.items():
        if any(w in text for w in words):
            return key

    return default


def this_season():

    m = datetime.date.today().month

    return {
        3: '봄',
        4: '봄',
        5: '봄',
        6: '여름',
        7: '여름',
        8: '여름',
        9: '가을',
        10: '가을',
        11: '가을',
    }.get(m, '겨울')


def sigungu_words():

    table = {}

    for region, sigungu in Tour.objects.values_list(
        'region', 'sigungu'
    ).distinct():

        if not sigungu:
            continue

        short = sigungu.split()[0]

        word = re.sub(
            r'(시|군|구)$',
            '',
            short
        )

        if len(word) >= 2 and word not in REGION_WORDS:
            table.setdefault(word, set()).add(
                (region, short)
            )

    return {
        w: list(v)[0]
        for w, v in table.items()
        if len(v) == 1
    }


def read_condition(history, message):

    recent = ' '.join(
        h['content']
        for h in history
        if h['role'] == 'user'
    )

    texts = (
        [message]
        if '다른 지역' in message
        else [message, recent]
    )

    region = None
    sigungu = None

    sg_table = sigungu_words()

    for text in texts:

        for word, code in REGION_WORDS.items():

            if word in text:
                region = code
                break

        for word, (code, sg) in sg_table.items():

            if word in text:
                region = code
                sigungu = sg
                break

        if region:
            break

    def find_age(text):

        m = re.search(
            r'([1-9])0\s*대',
            text
        )

        if not m:
            return None

        return min(
            max(int(m.group(1)) * 10, 20),
            60
        )

    mate = (
        find_one(message, MATE_WORDS)
        or find_one(recent, MATE_WORDS, '친구')
    )

    age = find_age(message)

    if (
        age is None
        and find_one(message, MATE_WORDS) == '부모님'
    ):
        age = 60

    if age is None:
        age = find_age(recent)

    return {
        'region': region,
        'sigungu': sigungu,
        'age': age,
        'mate': mate,
        'days': (
            find_one(message, DAY_WORDS)
            or find_one(recent, DAY_WORDS, '1박2일')
        ),
        'category': find_one(message, CATEGORY_WORDS),
    }


# ------------------------------------------------------------
# 기존 기능 2. 관광지 데이터 선택
# ------------------------------------------------------------

def pick_tours(cond, limit=15):

    qs = Tour.objects.filter(
        region=cond['region']
    ).exclude(
        category='교통시설'
    )

    if cond['sigungu']:
        qs = qs.filter(
            sigungu__startswith=cond['sigungu']
        )

    if cond['age']:
        qs = qs.filter(
            age=cond['age']
        )

    spots = {}

    for t in qs:

        s = spots.setdefault(
            t.name,
            {
                'name': t.name,
                'sigungu': t.sigungu,
                'category': t.category,
                'lat': t.lat,
                'lng': t.lng,
                'ratios': [],
            }
        )

        s['ratios'].append(t.ratio)

    result = []

    for s in spots.values():

        s['ratio'] = round(
            sum(s['ratios']) / len(s['ratios']),
            1
        )

        s['bonus'] = (
            1
            if cond['category']
            and s['category'] == cond['category']
            else 0
        )

        result.append(s)

    result.sort(
        key=lambda s: (
            s['bonus'],
            s['ratio']
        ),
        reverse=True
    )

    return result[:limit]


def distance(a, b):

    lat1, lng1, lat2, lng2 = map(
        math.radians,
        [
            a['lat'],
            a['lng'],
            b['lat'],
            b['lng']
        ]
    )

    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin((lng2 - lng1) / 2) ** 2
    )

    return 6371 * 2 * math.asin(math.sqrt(h))


# ------------------------------------------------------------
# 기존 기능 3. AI 시스템 프롬프트
# 음식 추천 기능 추가
# ------------------------------------------------------------

SYSTEM_PROMPT = """
당신은 국내여행 플랫폼 'TravelMate'의
맞춤추천 AI 챗봇 '트래비'입니다.

[기본 응답 규칙]

- 친절하고 간결한 존댓말로 답하세요.
- 이모지는 가끔만 사용하세요.
- 여행코스를 요청받으면 날짜별로
  '**1일차**'처럼 굵게 제목을 달아 주세요.
- 각 장소는 '- 10:00 장소명 : 한 줄 팁'
  형식으로 작성하세요.

[관광지 추천 규칙]

- [참고 관광지]는 한국관광데이터랩의
  연령대별 인기 관광지 데이터입니다.
- 관광지는 반드시 [참고 관광지]를 우선 사용하세요.
- 관광지 비율은 데이터에 기록된 비율입니다.
- 가까운 관광지끼리 묶어 여행 동선을 작성하세요.
- 관광지 이름을 임의로 만들어내지 마세요.

[음식 추천 규칙]

- [참고 음식 정보]가 있으면 이를 활용하세요.
- 음식 정보는 food_data.csv에서 가져온 자료입니다.
- 관광지는 기존 Tour 데이터를 기준으로 추천하세요.
- 음식 정보에 적힌 연관 관광지가
  실제 관광 코스에 포함되어 있는지 확인하세요.
- 연관 관광지가 코스에 없더라도
  같은 지역의 대표 음식으로 안내할 수 있습니다.
- 단, 관광지 바로 근처에 있는 음식점이라고
  확인 없이 단정하지 마세요.
- 실제 음식점 상호명과 주소를 임의로 만들지 마세요.
- 식사 장소와 메뉴를 구분해서 안내하세요.
- 여행 코스에는 점심 식사 시간을 포함하세요.
- 저녁 일정이 있는 여행 코스에는
  저녁 식사도 자연스럽게 포함하세요.
- 음식 데이터가 없으면 일반적인 식사 안내만 하세요.

[여행 일정 규칙]

- 관광지와 식사 시간을 적절하게 배치하세요.
- 이동시간은 실제 길찾기 결과가 아니라면
  확정된 시간처럼 안내하지 마세요.
- 운영시간, 요금, 휴무일은 방문 전 확인하도록 안내하세요.
- 정보가 부족하면 짧게 되물어보세요.

[기타]

- 여행과 관계없는 질문에는
  여행 상담 챗봇이라 답하기 어렵다고 안내하세요.
- 답변 마지막 줄에 추천 질문 3개를 작성하세요.

추천질문: 질문1 | 질문2 | 질문3
"""


# ------------------------------------------------------------
# 기존 기능 4. AI API 연결
# ------------------------------------------------------------

def ai_ready():

    provider = os.getenv(
        'AI_PROVIDER',
        'anthropic'
    ).lower()

    key = (
        os.getenv('OPENAI_API_KEY')
        if provider == 'openai'
        else os.getenv('ANTHROPIC_API_KEY')
    )

    return bool(key)


def call_ai(system, messages):

    provider = os.getenv(
        'AI_PROVIDER',
        'anthropic'
    ).lower()

    if provider == 'openai':

        res = requests.post(
            'https://api.openai.com/v1/chat/completions',

            headers={
                'Authorization':
                f"Bearer {os.getenv('OPENAI_API_KEY')}"
            },

            json={
                'model': (
                    os.getenv('AI_MODEL')
                    or 'gpt-4o-mini'
                ),
                'messages': [
                    {
                        'role': 'system',
                        'content': system
                    }
                ] + messages
            },

            timeout=60
        )

        res.raise_for_status()

        return res.json()['choices'][0]['message']['content']

    res = requests.post(
        'https://api.anthropic.com/v1/messages',

        headers={
            'x-api-key': os.getenv('ANTHROPIC_API_KEY'),
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },

        json={
            'model': (
                os.getenv('AI_MODEL')
                or 'claude-sonnet-5-5'
            ),
            'max_tokens': 2000,
            'system': system,
            'messages': messages,
        },

        timeout=60
    )

    res.raise_for_status()

    return res.json()['content'][0]['text']


# ------------------------------------------------------------
# 기존 기능 5. 추천 질문 분리
# ------------------------------------------------------------

def split_suggestions(text):

    lines = text.strip().split('\n')

    if (
        lines
        and lines[-1].strip().startswith('추천질문')
    ):

        items = (
            lines[-1]
            .split(':', 1)[-1]
            .split('|')
        )

        return (
            '\n'.join(lines[:-1]).strip(),
            [
                i.strip()
                for i in items
                if i.strip()
            ][:3]
        )

    return text.strip(), []


# ------------------------------------------------------------
# 기존 기능 6. AI 답변 생성
# 음식 CSV 정보 추가
# ------------------------------------------------------------

def ai_reply(history, message, cond):

    system = (
        SYSTEM_PROMPT
        + f"\n\n오늘 날짜: {datetime.date.today()}"
        + f" (계절: {this_season()})"
    )

    if cond['region']:

        age_txt = (
            f"{cond['age']}대"
            if cond['age']
            else '전 연령 평균'
        )

        place = REGION_NAME[cond['region']]

        if cond['sigungu']:
            place += f" {cond['sigungu']}"

        spots = '\n'.join(
            (
                f"- {s['name']} "
                f"({s['sigungu']}, {s['category']}) "
                f"비율:{s['ratio']}% "
                f"좌표:{s['lat']},{s['lng']}"
            )
            for s in pick_tours(cond)
        )

        system += (
            f"\n\n[참고 관광지 - {place}, {age_txt}]"
            f"\n{spots}"
        )

        # 추가된 음식 데이터
        food_context = make_food_context(cond)

        if food_context:

            system += (
                f"\n\n[참고 음식 정보 - {place}]"
                f"\n{food_context}"
            )

    messages = history + [
        {
            'role': 'user',
            'content': message
        }
    ]

    return split_suggestions(
        call_ai(system, messages)
    )


# ------------------------------------------------------------
# 기존 기능 7. AI 키가 없을 때 기본 응답
# 음식 추천 기능 추가
# ------------------------------------------------------------

def basic_reply(message, cond):

    if any(
        w in message
        for w in ['안녕', '하이', '반가', '처음']
    ):

        return (
            '안녕하세요! TravelMate 맞춤추천 AI '
            '**트래비**예요.\n'
            '가고 싶은 지역, 기간, 연령대, '
            '누구와 가는지 알려주시면 '
            '인기 관광지와 음식 정보를 활용해 '
            '여행 코스를 짜 드릴게요.'
        ), QUICK_START[:3]

    if not cond['region']:

        names = ', '.join(
            name for _, name in REGIONS
        )

        return (
            f'어느 지역으로 여행을 가시나요?\n'
            f'전국 17개 시·도를 안내해 드릴 수 있어요.\n'
            f'({names})'
        ), [
            '부산 여행 추천해줘',
            '제주 2박3일 코스',
            '강원 당일치기'
        ]

    day_count = {
        '당일치기': 1,
        '1박2일': 2,
        '2박3일': 3,
    }

    days = day_count.get(
        cond['days'],
        2
    )

    picks = pick_tours(
        cond,
        4 * days
    )

    if not picks:

        return (
            '조건에 맞는 관광지 데이터를 찾지 못했어요. '
            '지역이나 연령대를 바꿔서 물어봐 주세요.'
        ), [
            '다른 지역 추천해줘'
        ]

    # 가까운 관광지끼리 정렬
    route = [picks.pop(0)]

    while picks:

        nxt = min(
            picks,
            key=lambda p: distance(
                route[-1],
                p
            )
        )

        picks.remove(nxt)
        route.append(nxt)

    age_txt = (
        f"{cond['age']}대"
        if cond['age']
        else '전 연령'
    )

    place = REGION_NAME[cond['region']]

    if cond['sigungu']:
        place += f" {cond['sigungu']}"

    lines = [
        f"**{place} {cond['days']}** 코스예요.",
        f"{age_txt} 방문객에게 인기 있는 "
        f"관광지를 가까운 곳끼리 묶었어요.",
        ''
    ]

    base, extra = divmod(
        len(route),
        days
    )

    start = 0

    # 음식 정보 조회
    foods = pick_foods(cond)

    lunch_food = next(
        (
            f for f in foods
            if f.get('식사구분') == '점심'
        ),
        None
    )

    dinner_food = next(
        (
            f for f in foods
            if f.get('식사구분') == '저녁'
        ),
        None
    )

    for d in range(days):

        size = base + (
            1 if d < extra else 0
        )

        items = route[
            start:start + size
        ]

        start += size

        if not items:
            continue

        lines.append(
            f'**{d + 1}일차**'
        )

        t = 10 * 60

        lunch_added = False
        dinner_added = False

        for it in items:

            # 점심 식사 추가
            if t >= 12 * 60 and not lunch_added:

                if lunch_food:

                    lines.append(
                        f"- 12:00 점심 : "
                        f"{lunch_food.get('추천음식및장소', '')}"
                    )

                else:

                    lines.append(
                        '- 12:00 점심 : '
                        '관광지 주변에서 식사'
                    )

                lunch_added = True

                t = max(t, 13 * 60)

            # 저녁 식사 추가
            if t >= 18 * 60 and not dinner_added:

                if dinner_food:

                    lines.append(
                        f"- 18:00 저녁 : "
                        f"{dinner_food.get('추천음식및장소', '')}"
                    )

                else:

                    lines.append(
                        '- 18:00 저녁 : '
                        '지역 음식 즐기기'
                    )

                dinner_added = True

                t = max(t, 19 * 60)

            lines.append(
                f"- {t // 60:02d}:{t % 60:02d} "
                f"{it['name']} : "
                f"{it['sigungu']} · "
                f"{it['category']} · "
                f"인기 비율 {it['ratio']}%"
            )

            t += 120

        # 관광지 개수가 적더라도 점심은 추가
        if not lunch_added:

            if lunch_food:

                lines.append(
                    f"- 12:00 점심 추천 : "
                    f"{lunch_food.get('추천음식및장소', '')}"
                )

            else:

                lines.append(
                    '- 12:00 점심 추천 : 지역 음식'
                )

        # 숙박 일정에는 저녁 정보 추가
        if days > 1 and not dinner_added:

            if dinner_food:

                lines.append(
                    f"- 18:00 저녁 추천 : "
                    f"{dinner_food.get('추천음식및장소', '')}"
                )

            else:

                lines.append(
                    '- 18:00 저녁 추천 : 지역 음식'
                )

        lines.append('')

    lines.append(
        '식사 정보는 지역별 추천 자료이며, '
        '관광지와의 실제 거리는 확인이 필요해요.'
    )

    lines.append(
        '운영시간과 휴무일은 방문 전에 꼭 확인해 주세요.'
    )

    region = (
        re.sub(
            r'(시|군)$',
            '',
            cond['sigungu']
        )
        if cond['sigungu']
        else REGION_NAME[cond['region']]
    )

    other_day = (
        '당일치기'
        if cond['days'] != '당일치기'
        else '1박2일'
    )

    other_age = (
        '60대'
        if cond['age'] != 60
        else '20대'
    )

    chips = [
        f'{region} {other_day}로 바꿔줘',
        f'{other_age} 기준으로 다시 짜줘',
        '다른 지역 추천해줘'
    ]

    return '\n'.join(lines), chips


# ------------------------------------------------------------
# 최종 응답
# ------------------------------------------------------------

def get_reply(history, message):

    cond = read_condition(
        history,
        message
    )

    if ai_ready():

        try:

            text, chips = ai_reply(
                history,
                message,
                cond
            )

            return text, chips, True

        except Exception as e:

            print(
                'AI 호출 실패 → 기본 응답으로 대체:',
                e
            )

    text, chips = basic_reply(
        message,
        cond
    )

    return text, chips, False
