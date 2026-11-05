
/* ==========================================
   TravelMate nindex.js
   기존 화면 기능 + 맞춤 추천 TOP3 연동
========================================== */

// 1. 현재 선택된 사용자 취향 상태
const selectionState = {
  age: '30대',
  companion: '👥 친구와',
  season: '🍂 가을',
  concept: '힐링/자연',
  transport: '자차/렌터카'
};

// 2. 칩 파티클 효과
function createParticleBurst(btn) {
  const rect = btn.getBoundingClientRect();
  const count = 7;

  for (let i = 0; i < count; i++) {
    const particle = document.createElement('div');
    particle.classList.add('particle');

    particle.style.left = `${rect.width / 2}px`;
    particle.style.top = `${rect.height / 2}px`;

    const angle = Math.random() * Math.PI * 2;
    const velocity = 24 + Math.random() * 28;

    particle.style.setProperty(
      '--tx',
      `${Math.cos(angle) * velocity}px`
    );
    particle.style.setProperty(
      '--ty',
      `${Math.sin(angle) * velocity}px`
    );

    btn.appendChild(particle);
    setTimeout(() => particle.remove(), 700);
  }
}

// 3. 선택 칩 이벤트
document.querySelectorAll('[data-group]').forEach(groupEl => {
  const groupName = groupEl.getAttribute('data-group');
  const buttons = groupEl.querySelectorAll('.chip-btn');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => {
        b.classList.remove('chip-selected');
        b.classList.add('chip-default');
      });

      btn.classList.add('chip-selected');
      btn.classList.remove('chip-default');

      createParticleBurst(btn);
      selectionState[groupName] = btn.innerText.trim();
    });
  });
});

// 4. 왼쪽 패널 전환
function syncLeftPanel(step) {
  const leftText1 = document.getElementById('leftText1');
  const leftText2 = document.getElementById('leftText2');
  const resultTags = document.getElementById('resultTags');
  const stepIndicatorText =
    document.getElementById('stepIndicatorText');
  const dot1 = document.getElementById('dot1');
  const dot2 = document.getElementById('dot2');

  if (step === 2) {
    leftText1?.classList.add('hidden');
    leftText2?.classList.remove('hidden');

    if (resultTags) {
      resultTags.innerHTML = [
        selectionState.age,
        selectionState.companion,
        selectionState.season,
        selectionState.concept,
        selectionState.transport
      ].map(t =>
        `<span class="bg-brand-100 px-2.5 py-1 rounded-full">#${t}</span>`
      ).join('');
    }

    if (stepIndicatorText) {
      stepIndicatorText.innerHTML =
        `2 <span class="font-normal text-stone-400">/ 2단계</span>`;
    }

    if (dot1 && dot2) {
      dot1.className =
        'w-1.5 h-1.5 rounded-full bg-stone-300 transition-all duration-300';
      dot2.className =
        'w-6 h-1.5 rounded-full bg-brand-800 transition-all duration-300';
    }
  } else {
    leftText2?.classList.add('hidden');
    leftText1?.classList.remove('hidden');

    if (stepIndicatorText) {
      stepIndicatorText.innerHTML =
        `1 <span class="font-normal text-stone-400">/ 2단계</span>`;
    }

    if (dot1 && dot2) {
      dot1.className =
        'w-6 h-1.5 rounded-full bg-brand-800 transition-all duration-300';
      dot2.className =
        'w-1.5 h-1.5 rounded-full bg-stone-300 transition-all duration-300';
    }
  }
}

// ==========================================
// 5. 사용자 선택값을 JSON 코드로 변환
// ==========================================
function getRecommendationConditions() {
  const age =
    (String(selectionState.age).match(/20|30|40|50|60/) || ['30'])[0];

  function convert(group, mapping) {
    const raw = String(selectionState[group] || '');
    const found = Object.entries(mapping).find(
      ([label]) => raw.includes(label)
    );
    return found ? found[1] : null;
  }

  return {
    age: age,

    companion: convert('companion', {
      '혼자': 'solo',
      '친구': 'friends',
      '연인': 'couple',
      '커플': 'couple',
      '가족': 'family'
    }),

    season: convert('season', {
      '봄': 'spring',
      '여름': 'summer',
      '가을': 'autumn',
      '겨울': 'winter'
    }),

    concept: convert('concept', {
      '힐링': 'healing',
      '자연': 'healing',
      '액티비티': 'activity',
      '레저': 'activity',
      '맛집': 'food',
      '카페': 'food',
      '문화': 'culture',
      '역사': 'culture',
      '쇼핑': 'shopping',
      '도심': 'shopping'
    }),

    transport: convert('transport', {
      '대중교통': 'transit',
      '지하철': 'transit',
      '버스': 'transit',
      '기차': 'train',
      '열차': 'train',
      'KTX': 'train',
      '자차': 'car',
      '렌터카': 'car',
      '자동차': 'car'
    })
  };
}

// ==========================================
// 6. 새로운 관광지 추천 API 호출
// ==========================================
async function fetchTravelMateRecommendations() {
  if (!window.TravelMateRecommend) {
    throw new Error(
      'recommend.js가 연결되지 않았습니다.'
    );
  }

  const conditions = getRecommendationConditions();

  const response = await fetch(
    '/api/recommendation-places/?' +
    new URLSearchParams({
      age: conditions.age
    }),
    { cache: 'no-store' }
  );

  if (!response.ok) {
    throw new Error(
      `관광지 API 요청 실패: ${response.status}`
    );
  }

  const data = await response.json();

  if (
    !Array.isArray(data.places) ||
    data.places.length === 0
  ) {
    throw new Error(
      '추천할 관광지 데이터가 없습니다.'
    );
  }

  const weights =
    await window.TravelMateRecommend.loadWeights();

  const rankings =
    window.TravelMateRecommend.calculateRegionRanking(
      data.places,
      conditions,
      weights
    );

  console.table(rankings.map(item => ({
    region: item.region,
    score: item.total_score,
    place: item.representative_place?.title
  })));

  return {
    status: 'success',

    recommendations: rankings.map(item => {
      const place = item.representative_place;

      return {
        ...place,
        region: item.region,
        region_score: item.total_score,
        description:
          `${item.region} ${place.sigungu || ''}의 ` +
          `${place.title} — 선택한 여행 조건과 ` +
          `지역별 추천 점수를 반영한 여행지입니다.`
      };
    })
  };
}

// ==========================================
// 7. 추천 버튼 + 기존 로딩 화면
// ==========================================
const nextBtn = document.getElementById('nextBtn');
const loadingOverlay =
  document.getElementById('loadingOverlay');
const progressBar =
  document.getElementById('progressBar');
const analysisStepText =
  document.getElementById('analysisStepText');
const analysisSummaryBadge =
  document.getElementById('analysisSummaryBadge');
const counterNum =
  document.getElementById('counterNum');

if (nextBtn) {
  nextBtn.addEventListener('click', () => {
    if (
      !loadingOverlay ||
      !progressBar ||
      !analysisStepText ||
      !counterNum
    ) {
      console.error('추천 로딩 화면 요소가 없습니다.');
      return;
    }

    loadingOverlay.classList.remove(
      'pointer-events-none',
      'opacity-0'
    );

    const modalBox =
      loadingOverlay.querySelector('div');

    modalBox?.classList.remove('scale-90');
    modalBox?.classList.add('scale-100');

    if (analysisSummaryBadge) {
      analysisSummaryBadge.innerHTML =
        `<span>${selectionState.age}</span> · ` +
        `<span>${selectionState.companion}</span> · ` +
        `<span>${selectionState.season}</span> · ` +
        `<span>${selectionState.concept}</span>`;
    }

    let progress = 0;

    progressBar.style.width = '0%';
    counterNum.innerText = '0%';

    const steps = [
      '전국 관광 빅데이터 필터링...',
      '연령·동반자 맞춤 추천 점수 계산 중...',
      '맞춤 여행지 TOP3 추출 완료!'
    ];

    analysisStepText.innerText = steps[0];

    const fetchRecommendations =
      fetchTravelMateRecommendations()
        .catch(error => {
          console.error(
            'TravelMate 추천 오류:',
            error
          );
          return null;
        });

    const interval = setInterval(() => {
      progress +=
        Math.floor(Math.random() * 15) + 12;

      if (progress > 100) {
        progress = 100;
      }

      progressBar.style.width = `${progress}%`;
      counterNum.innerText = `${progress}%`;

      if (progress > 30 && progress < 70) {
        analysisStepText.innerText = steps[1];
      } else if (progress >= 70) {
        analysisStepText.innerText = steps[2];
      }

      if (progress >= 100) {
        clearInterval(interval);

        fetchRecommendations.then(data => {
          if (
            !data ||
            !Array.isArray(data.recommendations) ||
            data.recommendations.length === 0
          ) {
            showToast(
              '추천 데이터를 불러오지 못했습니다.'
            );

            loadingOverlay.classList.add(
              'opacity-0',
              'pointer-events-none'
            );

            modalBox?.classList.remove('scale-100');
            modalBox?.classList.add('scale-90');
            return;
          }

          updateStep2Cards(data.recommendations);

          setTimeout(() => {
            loadingOverlay.classList.add(
              'opacity-0',
              'pointer-events-none'
            );

            modalBox?.classList.remove('scale-100');
            modalBox?.classList.add('scale-90');

            const step1 =
              document.getElementById('step1Content');

            step1?.classList.remove('opacity-100');
            step1?.classList.add(
              'opacity-0',
              'hidden'
            );

            syncLeftPanel(2);

            const step2 =
              document.getElementById('step2Content');

            if (step2) {
              step2.classList.remove('hidden');
              step2.classList.add('flex');

              void step2.offsetHeight;

              step2.classList.remove('opacity-0');
              step2.classList.add('opacity-100');
            }
          }, 600);
        });
      }
    }, 210);
  });
}

// ==========================================
// 8. TOP3 추천 카드 표시
// ==========================================
function updateStep2Cards(recs) {
  const cardContainer = document.querySelector(
    '#step2Content .flex.flex-col.gap-3'
  );

  if (!cardContainer) return;

  const badgeColors = [
    'bg-amber-100 text-amber-900 border-amber-200',
    'bg-stone-100 text-stone-700 border-stone-200',
    'bg-orange-50 text-orange-900 border-orange-200'
  ];

  cardContainer.innerHTML = recs.map((rec, idx) => `
    <div
      class="dest-card ${
        idx === 0
          ? 'active bg-[#FBF9F6] border-brand-800 shadow-md'
          : 'bg-white border-stone-200/80 shadow-sm hover:shadow-md'
      } h-[115px] sm:h-[120px] shrink-0 flex items-center rounded-2xl overflow-hidden cursor-pointer border transition-all relative group"
      data-region="${rec.region}"
    >
      <div class="absolute top-2.5 left-2.5 z-10 px-2 py-0.5 rounded-full text-[10px] font-extrabold border ${badgeColors[idx % badgeColors.length]} shadow-sm">
        TOP ${idx + 1}
      </div>

      <div class="w-32 sm:w-36 h-full relative overflow-hidden bg-stone-100 flex-shrink-0">
        <img
          src="${rec.img_url || ''}"
          onerror="this.src='https://placehold.co/400x250/E8E3D9/4A3423?text=Travelmate'"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          alt="${rec.region}"
        >
        <div class="absolute inset-0 bg-gradient-to-t from-stone-900/40 via-transparent to-transparent"></div>
      </div>

      <div class="p-3.5 sm:p-4 flex-1 flex flex-col justify-between h-full relative">
        <div>
          <div class="flex items-center justify-between mb-1">
            <h3 class="font-extrabold text-[15px] sm:text-[16px] text-stone-900 tracking-tight">
              ${rec.region}
              <span class="text-xs font-normal text-stone-500">
                · ${rec.title}
              </span>
            </h3>
          </div>

          <p class="text-[11px] sm:text-[12px] text-stone-600 line-clamp-2 leading-relaxed">
            ${rec.description || ''}
          </p>
        </div>

        <div class="flex items-center justify-end pt-1 border-t border-stone-100/80">
          <div class="text-[11px] sm:text-[12px] font-bold text-brand-800 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
            코스 구경하기 &rarr;
          </div>
        </div>
      </div>
    </div>
  `).join('');

  document.querySelectorAll(
    '#step2Content .dest-card'
  ).forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll(
        '#step2Content .dest-card'
      ).forEach(c => {
        c.classList.remove(
          'active',
          'border-brand-800',
          'bg-[#FBF9F6]',
          'shadow-md'
        );

        c.classList.add(
          'bg-white',
          'border-stone-200/80',
          'shadow-sm'
        );
      });

      card.classList.add(
        'active',
        'border-brand-800',
        'bg-[#FBF9F6]',
        'shadow-md'
      );

      card.classList.remove(
        'bg-white',
        'border-stone-200/80',
        'shadow-sm'
      );

      const region =
        card.getAttribute('data-region');

      const url =
        `/main/`;

      requireAuth(() => {
        window.location.href = url;
      }, url);
    });
  });
}

// ==========================================
// 9. 로그인 및 회원가입 상태
// ==========================================
let isLoggedIn =
  window.DJANGO_IS_LOGGED_IN === true;

let pendingAction = null;
let pendingUrl = null;

window.addEventListener('pageshow', event => {
  if (
    event.persisted &&
    sessionStorage.getItem('tm_logged_in') === 'true'
  ) {
    isLoggedIn = true;
  } else if (!window.DJANGO_IS_LOGGED_IN) {
    sessionStorage.removeItem('tm_logged_in');
    isLoggedIn = false;
  }

  const submitBtn =
    document.getElementById('loginSubmitBtn');

  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.innerText = '로그인';
  }

  const joinBtn =
    document.getElementById('joinSubmitBtn');

  if (joinBtn) {
    joinBtn.disabled = false;
    joinBtn.innerText = '가입하기';
  }

  if (isLoggedIn) {
    closeAuthModal();
  }
});

// ==========================================
// 10. 지역 선택 기본값
// ==========================================
const fallbackRegions = [
  '서울', '경기', '인천', '강원',
  '충북', '충남', '대전', '세종',
  '전북', '전남', '광주', '경북',
  '경남', '대구', '울산', '부산',
  '제주'
];

document.querySelectorAll(
  '.region-select'
).forEach(select => {
  if (
    select.children.length <= 1 ||
    select.innerHTML.includes('{% for')
  ) {
    const defaultText = select.options[0]
      ? select.options[0].text
      : '지역 선택';

    select.innerHTML =
      `<option value="">${defaultText}</option>` +
      fallbackRegions.map(r =>
        `<option value="${r}">${r}</option>`
      ).join('');
  }
});

// ==========================================
// 11. 로그인 모달
// ==========================================
const authModal =
  document.getElementById('authModal');

const authModalBox =
  authModal?.querySelector('div');

const loginView =
  document.getElementById('loginView');

const joinView =
  document.getElementById('joinView');

function requireAuth(actionFunction, destinationUrl) {
  if (isLoggedIn) {
    if (typeof actionFunction === 'function') {
      actionFunction();
    } else if (destinationUrl) {
      window.location.href = destinationUrl;
    }
  } else {
    pendingAction = actionFunction;
    pendingUrl = destinationUrl;

    const nextInput =
      document.getElementById('loginNextUrl');

    if (nextInput && destinationUrl) {
      nextInput.value = destinationUrl;
    }

    openAuthModal();
  }
}

function openAuthModal() {
  toggleAuthView('login');

  const submitBtn =
    document.getElementById('loginSubmitBtn');

  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.innerText = '로그인';
  }

  const errMsg =
    document.getElementById('loginErrMsg');

  errMsg?.classList.add('hidden');

  authModal?.classList.remove(
    'pointer-events-none',
    'opacity-0'
  );

  authModalBox?.classList.remove('scale-95');
  authModalBox?.classList.add('scale-100');
}

function closeAuthModal() {
  authModal?.classList.add(
    'pointer-events-none',
    'opacity-0'
  );

  authModalBox?.classList.remove('scale-100');
  authModalBox?.classList.add('scale-95');
}

document.getElementById('closeAuthBtn')
  ?.addEventListener('click', closeAuthModal);

function toggleAuthView(view) {
  if (!loginView || !joinView) return;

  if (view === 'join') {
    loginView.classList.add('hidden');
    joinView.classList.remove('hidden');

    const joinAgeSelect =
      document.getElementById('joinAgeGroup');

    const selectedAgeRaw =
      selectionState.age.replace(/[^0-9]/g, '');

    if (selectedAgeRaw && joinAgeSelect) {
      Array.from(joinAgeSelect.options).forEach(opt => {
        if (opt.value.includes(selectedAgeRaw)) {
          opt.selected = true;
        }
      });
    }
  } else {
    joinView.classList.add('hidden');
    loginView.classList.remove('hidden');
  }
}

// ==========================================
// 12. 회원가입 아이디 중복확인
// ==========================================
let checkedId = null;

document.getElementById('joinId')
  ?.addEventListener('input', () => {
    checkedId = null;

    const msg =
      document.getElementById('idCheckMsg');

    if (msg) {
      msg.innerText = '';
      msg.classList.add('hidden');
    }
  });

document.getElementById('joinIdCheckBtn')
  ?.addEventListener('click', async function() {
    const input =
      document.getElementById('joinId');

    const msg =
      document.getElementById('idCheckMsg');

    const button =
      document.getElementById('joinIdCheckBtn');

    if (!input || !msg || !button) return;

    const value = input.value.trim();
    input.value = value;
    checkedId = null;

    if (!value) {
      msg.className =
        'text-[11px] mt-1 text-red-500 font-medium block';

      msg.innerText =
        '아이디를 입력해 주세요.';

      input.focus();
      return;
    }

    button.disabled = true;

    msg.className =
      'text-[11px] mt-1 text-stone-500 block';

    msg.innerText = '확인 중입니다.';

    const checkUrl = (
      window.DJANGO_CHECK_ID_URL &&
      !window.DJANGO_CHECK_ID_URL.includes('{%')
    )
      ? window.DJANGO_CHECK_ID_URL
      : '/member/check_id/';

    try {
      const response = await fetch(
        `${checkUrl}?` +
        new URLSearchParams({ id: value }),
        {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          },
          cache: 'no-store'
        }
      );

      if (!response.ok) {
        throw new Error('check failed');
      }

      const result = await response.json();

      if (input.value.trim() !== value) return;

      if (result.available) {
        checkedId = value;

        msg.className =
          'text-[11px] mt-1 text-emerald-600 font-semibold block';

        msg.innerText =
          result.message ||
          '이용가능한 아이디입니다.';
      } else {
        checkedId = null;

        msg.className =
          'text-[11px] mt-1 text-red-500 font-medium block';

        msg.innerText =
          result.message ||
          '중복이 되어 사용할 수 없습니다.';
      }
    } catch (error) {
      msg.className =
        'text-[11px] mt-1 text-red-500 font-medium block';

      msg.innerText =
        '중복확인을 하지 못했습니다.';
    } finally {
      button.disabled = false;
    }
  });

// ==========================================
// 13. 회원가입 제출
// ==========================================
async function handleDjangoJoin(event) {
  event.preventDefault();

  const inputId =
    document.getElementById('joinId');

  const msg =
    document.getElementById('idCheckMsg');

  const pw =
    document.getElementById('joinPw')?.value;

  const pw2 =
    document.getElementById('joinPw2')?.value;

  const submitBtn =
    document.getElementById('joinSubmitBtn');

  if (!inputId || !msg || !submitBtn) return;

  if (
    checkedId === null ||
    inputId.value.trim() !== checkedId
  ) {
    msg.className =
      'text-[11px] mt-1 text-red-500 font-medium block';

    msg.innerText =
      '아이디 중복확인을 먼저 진행해 주세요.';

    inputId.focus();
    return;
  }

  if (pw !== pw2) {
    showToast(
      '비밀번호가 서로 일치하지 않습니다.'
    );

    document.getElementById('joinPw2')?.focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerText = '가입 처리 중...';

  const joinForm =
    document.getElementById('joinForm');

  if (!joinForm) {
    submitBtn.disabled = false;
    return;
  }

const formData = new FormData(joinForm);

  try {
    const response = await fetch(joinForm.action, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrfToken()
      },
      body: formData
    });

    // 응답을 JSON으로 파싱 시도
    let result = {};
    try {
      result = await response.json();
    } catch (e) {
      // JSON 형태가 아닐 경우 대비
    }

    if (response.ok && result.success !== false) {
      showToast(
        result.msg || '회원가입이 완료되었습니다! 로그인해 주세요.'
      );

      toggleAuthView('login');

      const loginId =
        document.getElementById('loginId');

      if (loginId) {
        loginId.value = checkedId;
      }

      document.getElementById('loginPw')?.focus();
    } else {
      // 서버에서 전달받은 구체적인 에러 메시지 출력 (없으면 기본 메시지)
      showToast(result.msg || '회원가입에 실패했습니다.');
    }
  } catch (error) {
    showToast('회원가입 서버와 통신할 수 없습니다.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = '가입하기';
  }
}

function getCsrfToken() {
  const tokenInput =
    document.querySelector(
      '[name=csrfmiddlewaretoken]'
    );

  return tokenInput ? tokenInput.value : '';
}

// ==========================================
// 14. 로그인 폼
// ==========================================
const loginForm =
  document.getElementById('loginForm');

if (loginForm) {
  loginForm.addEventListener(
    'submit',
    async function(e) {
      e.preventDefault();

      const submitBtn =
        document.getElementById('loginSubmitBtn');

      const errMsg =
        document.getElementById('loginErrMsg');

      errMsg?.classList.add('hidden');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = '로그인 중...';
      }

      const formData = new FormData(loginForm);

      const targetUrl =
        pendingUrl ||
        document.getElementById('loginNextUrl')?.value ||
        '/main/';

      try {
        const response = await fetch(
          loginForm.action,
          {
            method: 'POST',
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
              'X-CSRFToken': getCsrfToken()
            },
            body: formData
          }
        );

        const htmlText = await response.text();

        let isLoginSuccess = false;

        const hasErrorText = (
          htmlText.includes('맞지 않습니다') ||
          htmlText.includes('일치하지') ||
          htmlText.includes('틀렸') ||
          htmlText.includes('맞지 않') ||
          htmlText.includes('아이디 또는 비밀번호')
        );

        if (hasErrorText) {
          isLoginSuccess = false;
        } else if (response.redirected) {
          const redirectedPath = new URL(
            response.url,
            window.location.origin
          ).pathname;

          isLoginSuccess =
            !redirectedPath.includes('login');
        } else {
          const hasLoginForm =
            htmlText.includes('name="pw"') ||
            htmlText.includes("name='pw'");

          isLoginSuccess = !hasLoginForm;
        }

        if (isLoginSuccess) {
          isLoggedIn = true;

          sessionStorage.setItem(
            'tm_logged_in',
            'true'
          );

          closeAuthModal();

          let finalRedirectUrl = targetUrl;

          if (
            response.url &&
            response.url.includes('/admin/')
          ) {
            finalRedirectUrl = '/admin/';
          }

          window.location.href = finalRedirectUrl;
        } else {
          if (errMsg) {
            errMsg.innerText =
              '아이디 또는 비밀번호가 맞지 않습니다.';

            errMsg.classList.remove('hidden');
          }
        }
      } catch (error) {
        if (errMsg) {
          errMsg.innerText =
            '로그인 서버와 통신할 수 없습니다.';

          errMsg.classList.remove('hidden');
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = '로그인';
        }
      }
    }
  );
}

// ==========================================
// 15. 기존 카드 클릭 및 페이지 이동
// ==========================================
const destCards =
  document.querySelectorAll('.dest-card');

destCards.forEach(card => {
  card.addEventListener('click', () => {
    const region =
      card.getAttribute('data-region') || '';

    destCards.forEach(c => {
      c.classList.remove(
        'active',
        'border-brand-800',
        'bg-[#FBF9F6]'
      );

      c.classList.add(
        'border-transparent',
        'bg-white',
        'shadow-sm'
      );
    });

    card.classList.add(
      'active',
      'border-brand-800',
      'bg-[#FBF9F6]'
    );

    card.classList.remove(
      'border-transparent',
      'bg-white',
      'shadow-sm'
    );

    const tourUrl =
      `/main/`;

    requireAuth(() => {
      window.location.href = tourUrl;
    }, tourUrl);
  });
});

// ==========================================
// 16. 이전 단계 버튼
// ==========================================
document.getElementById('backBtn')
  ?.addEventListener('click', () => {
    const step1 =
      document.getElementById('step1Content');

    const step2 =
      document.getElementById('step2Content');

    if (!step1 || !step2) return;

    step2.classList.remove(
      'opacity-100',
      'flex'
    );

    step2.classList.add(
      'opacity-0',
      'hidden'
    );

    syncLeftPanel(1);

    step1.classList.remove('hidden');
    void step1.offsetHeight;

    step1.classList.remove('opacity-0');
    step1.classList.add('opacity-100');
  });

// ==========================================
// 17. 첫 번째 추천 지역
// ==========================================
function getFirstRegion() {
  const firstCard =
    document.querySelector(
      '#step2Content .dest-card'
    );

  return firstCard
    ? firstCard.getAttribute('data-region') ||
      '강원 강릉시'
    : '강원 강릉시';
}

// 1위 이유 보기
document.getElementById('btnStats')
  ?.addEventListener('click', () => {
    const region = getFirstRegion();

    const url =
      `/main/`;

    requireAuth(() => {
      window.location.href = url;
    }, url);
  });

// 1위 핫플 TOP10
document.getElementById('btnTop10')
  ?.addEventListener('click', () => {
    const url = '/main/';

    requireAuth(() => {
      window.location.href = url;
    }, url);
  });


// ==========================================
// 18. 알림 메시지
// ==========================================
function showToast(message) {
  const existingToast =
    document.getElementById('toast');

  const existingToastMsg =
    document.getElementById('toastMsg');

  if (existingToast && existingToastMsg) {
    existingToastMsg.innerText = message;

    existingToast.classList.remove(
      'opacity-0',
      'pointer-events-none'
    );

    setTimeout(() => {
      existingToast.classList.add(
        'opacity-0',
        'pointer-events-none'
      );
    }, 2500);
  } else {
    console.warn(message);
  }
}
