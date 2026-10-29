// ======================================================
// TravelMate - 연령대별 인기 관광지 TOP10
// 카카오맵 + 관광지 마커 + 상세정보 팝업
// ======================================================

(() => {
    "use strict";

    // ==================================================
    // 1. HTML 요소
    // ==================================================

    const root = document.querySelector(".tm-top10");

    if (!root) return;

    const buttons = [
        ...root.querySelectorAll("#tm-regions button")
    ];

    const ages = [
        ...root.querySelectorAll(".tm-top10-ages button")
    ];

    const cards = root.querySelector("#tm-cards");
    const mapElement = root.querySelector("#tm-map");
    const titleElement = root.querySelector("#tm-title");
    const mapTitleElement = root.querySelector("#tm-map-title");

    if (!cards || !mapElement) return;

    // ==================================================
    // 2. 기본 설정
    // ==================================================

    let region = root.dataset.region || "seoul";
    let age = 20;

    let map = null;

    let markers = [];

    const markerElements = new Map();

    let selectedPin = null;
    let blinkTimer = null;
    let requestId = 0;

    // ==================================================
    // 3. 관광지 상세정보 팝업창
    // ==================================================

    let activePopup = null;
    let previousBodyOverflow = "";

    // 팝업창 닫기
    function closePopup() {

        if (!activePopup) return;

        activePopup.remove();
        activePopup = null;

        document.body.style.overflow = previousBodyOverflow;
    }

    // 팝업창 열기
    function openPopup(tour) {

        closePopup();

        previousBodyOverflow = document.body.style.overflow;

        // 팝업 배경
        const overlay = document.createElement("div");

        overlay.className = "tour-popup-overlay";

        // 팝업 본체
        const popup = document.createElement("div");

        popup.className = "tour-popup";

        popup.setAttribute("role", "dialog");
        popup.setAttribute("aria-modal", "true");
        popup.setAttribute(
            "aria-label",
            `${tour.name || "관광지"} 상세정보`
        );

        // 닫기 버튼
        const closeBtn = document.createElement("button");

        closeBtn.className = "tour-popup-close";
        closeBtn.type = "button";
        closeBtn.textContent = "×";

        closeBtn.setAttribute("aria-label", "팝업 닫기");

        closeBtn.addEventListener("click", closePopup);

        // 팝업 내부
        const content = document.createElement("div");

        content.className = "tour-popup-content";

        // 추후 관광지 데이터를 넣을 공간
        content.innerHTML = `
            <div class="tour-detail-container">

                <!-- 관광지 사진 영역 -->
                <div class="tour-detail-image">
                </div>

                <!-- 관광지 설명 영역 -->
                <div class="tour-detail-info">
                </div>

                <!-- 유튜브 영상 영역 -->
                <div class="tour-detail-video">
                </div>

            </div>
        `;

        popup.appendChild(closeBtn);
        popup.appendChild(content);

        overlay.appendChild(popup);

        // 팝업 바깥 클릭 시 닫기
        overlay.addEventListener("click", event => {

            if (event.target === overlay) {
                closePopup();
            }

        });

        document.body.appendChild(overlay);

        activePopup = overlay;

        // 배경 스크롤 방지
        document.body.style.overflow = "hidden";

        closeBtn.focus();
    }

    // ESC 키로 팝업 닫기
    document.addEventListener("keydown", event => {

        if (event.key === "Escape") {
            closePopup();
        }

    });

    // ==================================================
    // 4. 마커 효과 초기화
    // ==================================================

    function resetMarkerEffect() {

        if (blinkTimer !== null) {

            clearTimeout(blinkTimer);
            blinkTimer = null;

        }

        markerElements.forEach(pin => {

            pin.classList.remove(
                "tm-pin-selected",
                "tm-pin-blinking"
            );

        });

        selectedPin = null;
    }

    // ==================================================
    // 5. 특정 관광지 마커 확대 및 깜빡임
    // ==================================================

    function highlightMarker(tour, zoomMap = false) {

        if (!map) return;

        resetMarkerEffect();

        const pin = markerElements.get(
            Number(tour.rank)
        );

        if (!pin) return;

        selectedPin = pin;

        pin.classList.add("tm-pin-selected");

        // 애니메이션 다시 실행
        void pin.offsetWidth;

        pin.classList.add("tm-pin-blinking");

        // 관광지 카드 클릭 시 지도 이동 및 확대
        if (zoomMap) {

            const lat = Number(tour.lat);
            const lng = Number(tour.lng);

            if (
                Number.isFinite(lat) &&
                Number.isFinite(lng)
            ) {

                const position = new kakao.maps.LatLng(
                    lat,
                    lng
                );

                // 정확한 좌표로 이동 및 확대
                map.setLevel(5, {
                    anchor: position
                });

                map.setCenter(position);
            }
        }

        // 1.5초 후 마커 효과 종료
        blinkTimer = setTimeout(() => {

            pin.classList.remove(
                "tm-pin-selected",
                "tm-pin-blinking"
            );

            if (selectedPin === pin) {
                selectedPin = null;
            }

            blinkTimer = null;

        }, 1500);
    }

    // ==================================================
    // 6. 기존 마커 제거
    // ==================================================

    function clearMarkers() {

        closePopup();

        resetMarkerEffect();

        markers.forEach(marker => {
            marker.setMap(null);
        });

        markers = [];

        markerElements.clear();
    }

    // ==================================================
    // 7. 관광지 카드 생성
    // ==================================================

    function createCard(tour) {

        const card = document.createElement("button");

        card.type = "button";
        card.className = "tm-top10-card";

        // 관광지 이미지
        const img = document.createElement("img");

        img.src = tour.img;
        img.alt = tour.name;

        img.onerror = () => {
            img.style.visibility = "hidden";
        };

        // 관광지 정보
        const info = document.createElement("div");

        // 순위
        const rank = document.createElement("span");

        rank.className = "tm-rank";
        rank.textContent = `${tour.rank}위`;

        // 관광지 이름
        const name = document.createElement("strong");

        name.textContent = tour.name;

        // 지역
        const area = document.createElement("small");

        area.textContent =
            `${tour.sigungu || ""} · ${tour.category || ""}`;

        // 비율
        const ratio = document.createElement("b");

        ratio.textContent = `${tour.ratio}%`;

        info.append(
            rank,
            name,
            area,
            ratio
        );

        card.append(
            img,
            info
        );

        // 카드에 마우스를 올리면 마커 강조
        card.addEventListener("mouseenter", () => {

            highlightMarker(tour, false);

        });

        // 카드 클릭 시 관광지 위치로 이동 및 확대
        card.addEventListener("click", () => {

            highlightMarker(tour, true);

        });

        return card;
    }

    // ==================================================
    // 8. 카카오맵 관광지 마커 생성
    // ==================================================

    function createMarker(tour, bounds) {

        if (!map) return;

        const lat = Number(tour.lat);
        const lng = Number(tour.lng);

        if (
            !Number.isFinite(lat) ||
            !Number.isFinite(lng)
        ) {
            return;
        }

        // CSV 위도 경도
        const position = new kakao.maps.LatLng(
            lat,
            lng
        );

        // 마커 요소
        const pin = document.createElement("div");

        pin.className = "tm-top10-pin";

        const span = document.createElement("span");

        span.textContent = tour.rank;

        pin.append(span);

        // 카카오맵 마커
        const marker = new kakao.maps.CustomOverlay({

            position: position,
            content: pin,
            yAnchor: 1,
            zIndex: 3

        });

        marker.setMap(map);

        markers.push(marker);

        markerElements.set(
            Number(tour.rank),
            pin
        );

        // ==========================================
        // 마커 클릭 시 큰 반투명 팝업창 표시
        // ==========================================

        pin.addEventListener("click", event => {

            event.stopPropagation();

            // 지도 이동 없이 팝업만 표시
            openPopup(tour);

        });

        // 마커에 마우스를 올리면 강조
        pin.addEventListener("mouseenter", () => {

            highlightMarker(tour, false);

        });

        // 지도 범위에 관광지 좌표 추가
        bounds.extend(position);
    }

    // ==================================================
    // 9. 관광지 데이터 불러오기
    // ==================================================

    async function load(shouldZoom = true) {

        const currentRequestId = ++requestId;

        resetMarkerEffect();

        // 지역 버튼 활성화
        buttons.forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.region === region
            );

        });

        // 연령대 버튼 활성화
        ages.forEach(button => {

            button.classList.toggle(
                "active",
                Number(button.dataset.age) === age
            );

        });

        cards.textContent =
            "관광지 데이터를 불러오는 중입니다.";

        try {

            // Django API
            const apiUrl =
                `${root.dataset.api}` +
                `?region=${encodeURIComponent(region)}` +
                `&age=${age}`;

            const response = await fetch(apiUrl);

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }

            const data = await response.json();

            // 이전 요청 무시
            if (currentRequestId !== requestId) return;

            // 제목 변경
            if (titleElement) {

                titleElement.textContent =
                    `${data.region_name} 인기 관광지 TOP 10`;

            }

            if (mapTitleElement) {

                mapTitleElement.textContent =
                    `${data.region_name} 인기 명소`;

            }

            // 기존 카드 제거
            cards.replaceChildren();

            // 기존 마커 제거
            clearMarkers();

            // 관광지 데이터 없음
            if (!data.tours || !data.tours.length) {

                cards.textContent =
                    "이 지역의 관광지 데이터가 없습니다.";

                return;
            }

            // 지도 범위
            const bounds = map
                ? new kakao.maps.LatLngBounds()
                : null;

            // 관광지 카드 및 마커 생성
            data.tours.forEach(tour => {

                cards.append(
                    createCard(tour)
                );

                if (map && bounds) {

                    createMarker(tour, bounds);

                }

            });

            // 관광지 전체 마커가 보이도록 조정
            if (
                shouldZoom &&
                map &&
                markers.length
            ) {

                map.setBounds(
                    bounds,
                    60,
                    60,
                    60,
                    60
                );

            }

        } catch (error) {

            if (currentRequestId !== requestId) return;

            cards.textContent =
                "관광지 데이터를 불러오지 못했습니다.";

            console.error(error);

        }
    }

    // ==================================================
    // 10. 지역 선택
    // ==================================================

    buttons.forEach(button => {

        button.addEventListener("click", () => {

            region = button.dataset.region;

            load(true);

        });

    });

    // ==================================================
    // 11. 연령대 선택
    // ==================================================

    ages.forEach(button => {

        button.addEventListener("click", () => {

            age = Number(button.dataset.age);

            load(true);

        });

    });

    // ==================================================
    // 12. 카카오맵 생성
    // ==================================================

    function showMap() {

        if (!window.kakao || !window.kakao.maps) {

            mapElement.innerHTML = `
                <p style="
                    padding:180px 20px;
                    text-align:center;
                ">
                    카카오맵 API 연결을 확인해주세요.
                </p>
            `;

            return;
        }

        kakao.maps.load(() => {

            // 서울특별시 중심
            const center = new kakao.maps.LatLng(
                37.5665,
                126.9780
            );

            // 지도 생성
            map = new kakao.maps.Map(
                mapElement,
                {
                    center: center,
                    level: 8
                }
            );

            // 첫 화면 서울 관광지 TOP10 표시
            load(true);

        });
    }

    // ==================================================
    // 13. 팝업창 CSS 자동 추가
    // ==================================================

    const popupStyle = document.createElement("style");

    popupStyle.textContent = `

        /* 팝업 배경 */
        .tour-popup-overlay {

            position: fixed;
            inset: 0;

            background: rgba(0, 0, 0, 0.35);

            display: flex;
            justify-content: center;
            align-items: center;

            z-index: 99999;

            padding: 20px;
            box-sizing: border-box;
        }

        /* 큰 반투명 팝업 */
        .tour-popup {

            position: relative;

            width: 850px;
            max-width: 95vw;

            height: 600px;
            max-height: 90vh;

            background: rgba(255, 255, 255, 0.85);

            border: 1px solid rgba(128, 84, 59, 0.5);
            border-radius: 12px;

            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);

            overflow: hidden;
            box-sizing: border-box;
        }

        /* 닫기 버튼 */
        .tour-popup-close {

            position: absolute;

            top: 15px;
            right: 20px;

            border: none;
            background: transparent;

            font-size: 30px;
            color: #80543b;

            cursor: pointer;
            z-index: 10;
        }

        .tour-popup-close:hover {
            color: #442116;
        }

        /* 팝업 내부 */
        .tour-popup-content {

            width: 100%;
            height: 100%;

            padding: 55px 35px 35px;

            box-sizing: border-box;

            overflow-y: auto;
        }

        /* 상세정보 레이아웃 */
        .tour-detail-container {

            display: grid;

            grid-template-columns: 1fr 1fr;
            grid-template-rows: 250px 220px;

            gap: 20px;
        }

        /* 관광지 사진 영역 */
        .tour-detail-image {
            grid-column: 1;
        }

        /* 관광지 설명 영역 */
        .tour-detail-info {
            grid-column: 2;
        }

        /* 유튜브 영상 영역 */
        .tour-detail-video {
            grid-column: 1 / 3;
        }

        /* 모바일 대응 */
        @media (max-width: 700px) {

            .tour-popup {
                width: 95vw;
                height: 85vh;
            }

            .tour-popup-content {
                padding: 55px 20px 25px;
            }

            .tour-detail-container {

                grid-template-columns: 1fr;
                grid-template-rows: 220px 180px 220px;
            }

            .tour-detail-image,
            .tour-detail-info,
            .tour-detail-video {
                grid-column: 1;
            }
        }

    `;

    document.head.appendChild(popupStyle);

    // ==================================================
    // 14. 실행
    // ==================================================

    showMap();

})();