
document.addEventListener("DOMContentLoaded", function () {

    // =====================================
    // 1. 커뮤니티 / 1:1 문의 탭 전환
    // =====================================

    const tabs = document.querySelectorAll(".qa-tab");
    const panels = document.querySelectorAll(".qa-panel");

    function openTab(panelId) {

        tabs.forEach(function (tab) {
            tab.classList.toggle(
                "active",
                tab.dataset.panel === panelId
            );
        });

        panels.forEach(function (panel) {
            panel.classList.toggle(
                "active",
                panel.id === panelId
            );
        });

    }

    tabs.forEach(function (tab) {

        tab.addEventListener("click", function () {
            openTab(tab.dataset.panel);
        });

    });


    // =====================================
    // 2. 기존 1:1 문의 작성 폼
    // =====================================

    const writeButton = document.getElementById("qa-write-toggle");
    const writeForm = document.getElementById("qa-write-form");

    if (writeButton && writeForm) {

        writeButton.addEventListener("click", function () {

            writeForm.hidden = !writeForm.hidden;

            if (!writeForm.hidden) {

                writeButton.textContent = "작성 취소";

                writeForm.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            } else {

                writeButton.textContent = "+ 질문 작성";

            }

        });

    }


    // =====================================
    // 3. 커뮤니티 화면 전환
    // =====================================

    const communityList = document.getElementById("community-list");
    const communityWrite = document.getElementById("community-write");
    const communityDetail = document.getElementById("community-detail");

    const communityWriteButton = document.getElementById(
        "community-write-toggle"
    );

    const communityBackButtons = document.querySelectorAll(
        ".community-back"
    );

    function showCommunityScreen(screen) {

        if (communityList) {
            communityList.hidden = screen !== "list";
        }

        if (communityWrite) {
            communityWrite.hidden = screen !== "write";
        }

        if (communityDetail) {
            communityDetail.hidden = screen !== "detail";
        }

    }

    // 커뮤니티 글쓰기 버튼
    if (communityWriteButton) {

        communityWriteButton.addEventListener("click", function () {
            showCommunityScreen("write");
        });

    }

    // 커뮤니티 취소 / 목록으로 돌아가기
    communityBackButtons.forEach(function (button) {

        button.addEventListener("click", function () {
            showCommunityScreen("list");
        });

    });


    // =====================================
    // 4. URL에 따라 탭 자동 선택
    // =====================================

    // params는 한 번만 선언
    const params = new URLSearchParams(window.location.search);

    // 1:1 문의 검색 후에도 1:1 문의 탭 유지
    if (
        window.location.hash === "#question-panel" ||
        params.get("tab") === "question"
    ) {
        openTab("question-panel");
    } else {
        openTab("faq-panel");
    }


    // =====================================
    // 5. 커뮤니티 게시글 상세 화면
    // =====================================

    // URL에 post 번호가 있으면 상세 화면 표시
    if (params.has("post")) {

        showCommunityScreen("detail");

    } else {

        showCommunityScreen("list");

    }

});
