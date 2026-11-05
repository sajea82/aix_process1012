
/* ==========================================
   TravelMate 맞춤 여행 추천
   관광객 수 보정 + 가중치 기반 지역 TOP3
   static/js/recommend.js
========================================== */

window.TravelMateRecommend = (() => {

    let weightData = null;

    // 1. JSON 가중치 불러오기
    async function loadWeights() {
        if (weightData) return weightData;

        const response = await fetch(
            "/static/json/recommend_weights.json"
        );

        if (!response.ok) {
            throw new Error("가중치 JSON 파일을 불러올 수 없습니다.");
        }

        weightData = await response.json();
        return weightData;
    }

    // 2. 사용자 선택 조건 가져오기
    function getSelectedConditions() {
        const groups = [
            "age",
            "companion",
            "season",
            "concept",
            "transport"
        ];

        const selected = {};

        groups.forEach(group => {
            const button = document.querySelector(
                `[data-group="${group}"] .chip-selected`
            );

            selected[group] = button
                ? button.dataset.value
                : null;
        });

        return selected;
    }

    // 3. 지역코드 변환
    function normalizeRegion(region, weights) {
        const code = String(region || "").trim().toLowerCase();

        return weights.regions?.[code] || region;
    }

    // 4. 지역 가중치 확인
    function matchesRegion(rule, region) {
        if (!rule) return false;

        if (Array.isArray(rule.regions)) {
            return rule.regions.includes(region);
        }

        if (Array.isArray(rule.exclude_regions)) {
            return !rule.exclude_regions.includes(region);
        }

        return false;
    }

    // 5. 카테고리 가중치 확인
    function matchesCategory(rule, category) {
        if (!rule || !Array.isArray(rule.categories)) {
            return false;
        }

        return rule.categories.some(keyword =>
            String(category || "").includes(keyword)
        );
    }

    // 6. 조건별 가중치 계산
    function calculateMultiplier(place, conditions, weights) {
        let multiplier = weights.default_multiplier ?? 1.0;

        const region = normalizeRegion(place.region, weights);
        const category = place.category;

        const groups = [
            "transport",
            "concept",
            "companion",
            "season"
        ];

        groups.forEach(group => {
            const selectedValue = conditions[group];

            if (!selectedValue) return;

            const rule = weights[group]?.[selectedValue];

            if (!rule) return;

            if (
                matchesRegion(rule, region) ||
                matchesCategory(rule, category)
            ) {
                multiplier *= Number(rule.weight) || 1;
            }
        });

        return multiplier;
    }

    // 7. 관광객 수 제곱근 보정 + 가중치 계산
    
    function calculatePlaceScore(place, conditions, weights) {

    const baseVisitors = Math.max(
        0,
        Number(place.base_visitors) || 0
    );

    // 관광객 수 제곱근 보정
    const normalizedVisitors = Math.sqrt(baseVisitors);

    // 이동수단, 컨셉, 동반자, 계절 가중치
    const multiplier = calculateMultiplier(
        place,
        conditions,
        weights
    );

    // 지역명 통일
    const region = normalizeRegion(place.region, weights);

    // 서울·경기 외 지역 균형 가중치
    const balanceWeight = Number(
        weights.region_balance?.[region] ?? 1.0
    );

    // 최종 추천 점수
    const finalScore =
        normalizedVisitors *
        multiplier *
        balanceWeight;

    return {
        ...place,
        region: region,
        base_visitors: baseVisitors,
        multiplier: Number(multiplier.toFixed(4)),
        balance_weight: balanceWeight,
        recommendation_score: Number(finalScore.toFixed(2))
    };
    }


    // 8. 지역별 점수 계산
    function calculateRegionRanking(places, conditions, weights) {

        const scoredPlaces = places.map(place =>
            calculatePlaceScore(place, conditions, weights)
        );

        const regionMap = {};

        scoredPlaces.forEach(place => {

            const region = place.region;

            if (!regionMap[region]) {
                regionMap[region] = {
                    region: region,
                    total_score: 0,
                    places: []
                };
            }

            regionMap[region].places.push(place);
        });

        const rankings = Object.values(regionMap);

        rankings.forEach(item => {

            item.places.sort(
                (a, b) =>
                    b.recommendation_score -
                    a.recommendation_score
            );

            // 지역 내 상위 관광지 3개 평균
            const topPlaces = item.places.slice(0, 3);

            const scoreSum = topPlaces.reduce(
                (sum, place) =>
                    sum + place.recommendation_score,
                0
            );

            item.total_score = Number(
                (scoreSum / topPlaces.length).toFixed(2)
            );

            // 해당 지역 대표 관광지
            item.representative_place = item.places[0];
        });

        // 지역 점수 내림차순
        rankings.sort(
            (a, b) => b.total_score - a.total_score
        );

        // 시도별 TOP3
        return rankings.slice(0, 3);
    }

    // 9. 최종 추천 실행
    async function recommend(places) {

        const weights = await loadWeights();
        const conditions = getSelectedConditions();

        if (!Array.isArray(places)) {
            throw new Error("관광지 데이터는 배열이어야 합니다.");
        }

        const results = calculateRegionRanking(
            places,
            conditions,
            weights
        );

        return {
            conditions,
            recommendations: results
        };
    }

    return {
        loadWeights,
        getSelectedConditions,
        calculateMultiplier,
        calculatePlaceScore,
        calculateRegionRanking,
        recommend
    };

})();
