
from qna.models import CommunityPost, CommunityComment


# =====================================
# 커뮤니티 게시글 및 댓글 데이터
# =====================================

sample_posts = [
    {
        "title": "제주도 2박 3일 여행 코스 추천해주세요!",
        "author": "여행초보",
        "content": (
            "다음 달 제주도로 2박 3일 여행을 가려고 해요.\n"
            "성산일출봉과 협재해수욕장은 꼭 가고 싶은데 "
            "추천 코스가 있을까요?"
        ),
        "comments": [
            ("제주러버", "첫날은 애월, 둘째 날은 성산 쪽으로 가보세요!"),
            ("바다좋아", "협재해수욕장은 일몰 시간에 추천해요."),
            ("여행메이트", "우도도 일정에 넣으면 좋아요."),
        ],
    },
    {
        "title": "서울에서 가을 단풍 보기 좋은 곳 어디인가요?",
        "author": "가을산책",
        "content": (
            "서울에서 대중교통으로 갈 수 있는 단풍 명소를 찾고 있어요.\n"
            "사진 찍기 좋은 장소 추천 부탁드립니다."
        ),
        "comments": [
            ("서울여행자", "서울숲 추천해요!"),
            ("단풍러버", "덕수궁 돌담길도 예뻐요."),
            ("사진여행", "올림픽공원도 좋아요."),
        ],
    },
    {
        "title": "부산 혼자 여행하기 좋은 장소 추천",
        "author": "혼행족",
        "content": (
            "부산으로 혼자 1박 2일 여행을 가려고 합니다.\n"
            "혼자 돌아다니기 좋은 여행지와 맛집 추천 부탁드려요."
        ),
        "comments": [
            ("부산토박이", "광안리 해변 산책 추천해요."),
            ("여행하는곰", "흰여울문화마을도 좋아요."),
            ("맛집탐험가", "남포동 먹거리 구경도 추천합니다."),
        ],
    },
    {
        "title": "강릉 당일치기 여행 후기 공유해요",
        "author": "커피한잔",
        "content": (
            "주말에 강릉 당일치기로 다녀왔어요.\n"
            "안목해변에서 커피 마시고 경포해변도 산책했는데 "
            "정말 좋았습니다!"
        ),
        "comments": [
            ("강릉좋아", "안목해변 카페거리 정말 좋죠!"),
            ("바다산책", "다음에는 정동진도 가보세요."),
        ],
    },
    {
        "title": "전주 한옥마을 맛집 추천 부탁드려요",
        "author": "먹방여행",
        "content": (
            "전주 한옥마을에 처음 가는데 맛집 추천 부탁드려요.\n"
            "비빔밥 말고도 먹어볼 만한 음식이 있을까요?"
        ),
        "comments": [
            ("전주여행", "전주 콩나물국밥 추천해요."),
            ("맛집지도", "한옥마을 길거리 음식도 드셔보세요."),
            ("여행러", "전주 초코파이도 유명해요."),
        ],
    },
    {
        "title": "부모님과 함께 가기 좋은 국내 여행지",
        "author": "효도여행",
        "content": (
            "부모님과 주말에 국내 여행을 가려고 합니다.\n"
            "많이 걷지 않아도 즐길 수 있는 여행지가 있을까요?"
        ),
        "comments": [
            ("힐링여행", "담양 주변 추천해요."),
            ("가족여행", "경주도 가족 여행으로 좋아요."),
            ("국내여행러", "남해 바다 드라이브도 추천합니다."),
        ],
    },
    {
        "title": "겨울에 가기 좋은 국내 여행지 추천해주세요",
        "author": "겨울감성",
        "content": (
            "겨울 여행을 계획하고 있어요.\n"
            "눈 구경도 하고 사진도 찍기 좋은 국내 여행지 "
            "추천 부탁드립니다."
        ),
        "comments": [
            ("눈꽃여행", "평창 대관령 추천합니다."),
            ("겨울바다", "강릉 겨울바다도 좋아요."),
            ("여행일기", "춘천도 겨울에 분위기가 좋아요."),
            ("사진러버", "설악산 주변 눈 풍경도 멋져요."),
        ],
    },
]


# =====================================
# DB에 게시글 및 댓글 저장
# =====================================

def create_sample_data():

    created_posts = 0
    created_comments = 0

    for item in sample_posts:

        # 동일 제목의 게시글이 있는지 확인
        post = CommunityPost.objects.filter(
            title=item["title"]
        ).first()

        # 기존 게시글이 없다면 새로 등록
        if post is None:

            post = CommunityPost.objects.create(
                title=item["title"],
                author=item["author"],
                content=item["content"],
            )

            created_posts += 1

            # 새 게시글에 댓글 등록
            for author, content in item["comments"]:

                CommunityComment.objects.create(
                    post=post,
                    author=author,
                    content=content,
                )

                created_comments += 1

    print("================================")
    print("커뮤니티 데이터 등록 완료")
    print("새 게시글:", created_posts, "개")
    print("새 댓글:", created_comments, "개")
    print("전체 게시글:", CommunityPost.objects.count(), "개")
    print("전체 댓글:", CommunityComment.objects.count(), "개")
    print("================================")


if __name__ == "__main__":
    create_sample_data()
