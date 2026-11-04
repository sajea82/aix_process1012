// 1. 현재 선택된 사용자 취향 상태 저장 객체
const selectionState = {
  age: '30대',
  companion: '👥 친구와',
  season: '🍂 가을',
  concept: '힐링/자연',
  transport: '자차/렌터카'
};

// 2. 칩 파티클 버스트 효과 함수
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
    const tx = Math.cos(angle) * velocity;
    const ty = Math.sin(angle) * velocity;

    particle.style.setProperty('--tx', `${tx}px`);
    particle.style.setProperty('--ty', `${ty}px`);

    btn.appendChild(particle);
    setTimeout(() => particle.remove(), 700);
  }
}

// 3. 칩 버튼 클릭 토글 (각 그룹별 단일 선택)
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

// 좌측 패널 1단계 <-> 2단계 상태 동기화 헬퍼 함수
function syncLeftPanel(step) {
  const leftText1 = document.getElementById('leftText1');
  const leftText2 = document.getElementById('leftText2');
  const resultTags = document.getElementById('resultTags');
  const stepIndicatorText = document.getElementById('stepIndicatorText');
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
      ].map(t => `<span class="bg-brand-100 px-2.5 py-1 rounded-full">#${t}</span>`).join('');
    }
    if (stepIndicatorText) {
      stepIndicatorText.innerHTML = `2 <span class="font-normal text-stone-400">/ 2단계</span>`;
    }
    if (dot1 && dot2) {
      dot1.className = 'w-1.5 h-1.5 rounded-full bg-stone-300 transition-all duration-300';
      dot2.className = 'w-6 h-1.5 rounded-full bg-brand-800 transition-all duration-300';
    }
  } else {
    leftText2?.classList.add('hidden');
    leftText1?.classList.remove('hidden');
    if (stepIndicatorText) {
      stepIndicatorText.innerHTML = `1 <span class="font-normal text-stone-400">/ 2단계</span>`;
    }
    if (dot1 && dot2) {
      dot1.className = 'w-6 h-1.5 rounded-full bg-brand-800 transition-all duration-300';
      dot2.className = 'w-1.5 h-1.5 rounded-full bg-stone-300 transition-all duration-300';
    }
  }
}

// 4. 다음(Let's Travel) 버튼 클릭 시 다단계 분석 로딩 후 2단계 결과로 전환
const nextBtn = document.getElementById('nextBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const progressBar = document.getElementById('progressBar');
const analysisStepText = document.getElementById('analysisStepText');
const analysisSummaryBadge = document.getElementById('analysisSummaryBadge');
const counterNum = document.getElementById('counterNum');

if (nextBtn) {
  nextBtn.addEventListener('click', () => {
    loadingOverlay.classList.remove('pointer-events-none', 'opacity-0');
    const modalBox = loadingOverlay.querySelector('div');
    modalBox.classList.remove('scale-90');
    modalBox.classList.add('scale-100');

    analysisSummaryBadge.innerHTML = `<span>${selectionState.age}</span> · <span>${selectionState.companion}</span> · <span>${selectionState.season}</span> · <span>${selectionState.concept}</span>`;

    let progress = 0;
    progressBar.style.width = '0%';
    counterNum.innerText = '0%';

    const steps = [
      "전국 관광 빅데이터 필터링...",
      "연령·동반자 맞춤 만족도 연산 중...",
      "맞춤 여행지 TOP3 추출 완료!"
    ];
    analysisStepText.innerText = steps[0];

    // 백엔드 추천 API 비동기 호출 실행
    const fetchRecommendations = fetch(`/tour/recommendations/?` + new URLSearchParams({
      age: selectionState.age,
      companion: selectionState.companion,
      season: selectionState.season,
      concept: selectionState.concept
    })).then(res => res.json()).catch(() => null);

    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 15) + 12;
      if (progress > 100) progress = 100;
      
      progressBar.style.width = `${progress}%`;
      counterNum.innerText = `${progress}%`;

      if (progress > 30 && progress < 70) {
        analysisStepText.innerText = steps[1];
      } else if (progress >= 70) {
        analysisStepText.innerText = steps[2];
      }

      if (progress >= 100) {
        clearInterval(interval);
        
        // API 응답 완료 후 카드 데이터 주입 및 화면 전환
        fetchRecommendations.then(data => {
          if (data && data.recommendations && data.recommendations.length > 0) {
            updateStep2Cards(data.recommendations);
          }
          setTimeout(() => {
            loadingOverlay.classList.add('opacity-0', 'pointer-events-none');
            modalBox.classList.remove('scale-100');
            modalBox.classList.add('scale-90');
            
            const step1 = document.getElementById('step1Content');
            step1.classList.remove('opacity-100');
            step1.classList.add('opacity-0', 'hidden');
            
            syncLeftPanel(2);

            const step2 = document.getElementById('step2Content');
            step2.classList.remove('hidden');
            step2.classList.add('flex');
            void step2.offsetHeight;
            step2.classList.remove('opacity-0');
            step2.classList.add('opacity-100');
          }, 600);
        });
      }
    }, 210);
  });
}


// 2단계 카드 동적 렌더링 함수 (균형 잡힌 프리미엄 카드 디자인 적용)
// 2단계 카드 동적 렌더링 함수 (불필요한 뱃지와 문구 제거)
function updateStep2Cards(recs) {
  const cardContainer = document.querySelector('#step2Content .flex.flex-col.gap-3');
  if (!cardContainer) return;

  const badgeColors = ['bg-amber-100 text-amber-900 border-amber-200', 'bg-stone-100 text-stone-700 border-stone-200', 'bg-orange-50 text-orange-900 border-orange-200'];

  cardContainer.innerHTML = recs.map((rec, idx) => `
    <div class="dest-card ${idx === 0 ? 'active bg-[#FBF9F6] border-brand-800 shadow-md' : 'bg-white border-stone-200/80 shadow-sm hover:shadow-md'} h-[115px] sm:h-[120px] shrink-0 flex items-center rounded-2xl overflow-hidden cursor-pointer border transition-all relative group" data-region="${rec.region}">
      <!-- 순위 배지 -->
      <div class="absolute top-2.5 left-2.5 z-10 px-2 py-0.5 rounded-full text-[10px] font-extrabold border ${badgeColors[idx]} shadow-sm">
        TOP ${idx + 1}
      </div>

      <!-- 썸네일 이미지 -->
      <div class="w-32 sm:w-36 h-full relative overflow-hidden bg-stone-100 flex-shrink-0">
        <img src="${rec.img_url}" onerror="this.src='https://placehold.co/400x250/E8E3D9/4A3423?text=Travelmate'" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt="${rec.region}">
        <div class="absolute inset-0 bg-gradient-to-t from-stone-900/40 via-transparent to-transparent"></div>
      </div>

      <!-- 본문 영역 (빅데이터 검증 완료 및 우측 상단 카테고리 태그 제거됨) -->
      <div class="p-3.5 sm:p-4 flex-1 flex flex-col justify-between h-full relative">
        <div>
          <div class="flex items-center justify-between mb-1">
            <h3 class="font-extrabold text-[15px] sm:text-[16px] text-stone-900 tracking-tight">
              ${rec.region} <span class="text-xs font-normal text-stone-500">· ${rec.title}</span>
            </h3>
          </div>
          <p class="text-[11px] sm:text-[12px] text-stone-600 line-clamp-2 leading-relaxed">
            ${rec.description}
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

  // 새로 생성된 카드들에 클릭 이벤트 부착
  document.querySelectorAll('.dest-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.dest-card').forEach(c => {
        c.classList.remove('active', 'border-brand-800', 'bg-[#FBF9F6]', 'shadow-md');
        c.classList.add('bg-white', 'border-stone-200/80', 'shadow-sm');
      });
      card.classList.add('active', 'border-brand-800', 'bg-[#FBF9F6]', 'shadow-md');
      card.classList.remove('bg-white', 'border-stone-200/80', 'shadow-sm');
      
      const region = card.getAttribute('data-region');
      requireAuth(`/tour/?region=${encodeURIComponent(region)}`);
    });
  });
}

// 5. 로그인 & 회원가입 가드 및 뒤로가기 복원 로직
let isLoggedIn = window.DJANGO_IS_LOGGED_IN === true;
let pendingAction = null;
let pendingUrl = null;

window.addEventListener('pageshow', (event) => {
  if (event.persisted && sessionStorage.getItem('tm_logged_in') === 'true') {
    isLoggedIn = true;
  } else if (!window.DJANGO_IS_LOGGED_IN) {
    sessionStorage.removeItem('tm_logged_in');
    isLoggedIn = false;
  }

  const submitBtn = document.getElementById('loginSubmitBtn');
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.innerText = '로그인';
  }
  const joinBtn = document.getElementById('joinSubmitBtn');
  if (joinBtn) {
    joinBtn.disabled = false;
    joinBtn.innerText = '가입하기';
  }
  if (isLoggedIn) {
    closeAuthModal();
  }
});

const fallbackRegions = [
  "서울", "경기", "인천", "강원", "충북", "충남", "대전", "세종", 
  "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"
];

document.querySelectorAll('.region-select').forEach(select => {
  if (select.children.length <= 1 || select.innerHTML.includes('{% for')) {
    const defaultText = select.options[0] ? select.options[0].text : '지역 선택';
    select.innerHTML = `<option value="">${defaultText}</option>` + 
      fallbackRegions.map(r => `<option value="${r}">${r}</option>`).join('');
  }
});

const authModal = document.getElementById('authModal');
const authModalBox = authModal.querySelector('div');
const loginView = document.getElementById('loginView');
const joinView = document.getElementById('joinView');

function requireAuth(actionFunction, destinationUrl) {
  if (isLoggedIn) {
    window.location.href = destinationUrl;
  } else {
    pendingAction = actionFunction;
    pendingUrl = destinationUrl;
    
    const nextInput = document.getElementById('loginNextUrl');
    if (nextInput && destinationUrl) {
      nextInput.value = destinationUrl;
    }
    openAuthModal();
  }
}

function openAuthModal() {
  toggleAuthView('login');
  const submitBtn = document.getElementById('loginSubmitBtn');
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.innerText = '로그인';
  }
  const errMsg = document.getElementById('loginErrMsg');
  if (errMsg) {
    errMsg.classList.add('hidden');
  }
  authModal.classList.remove('pointer-events-none', 'opacity-0');
  authModalBox.classList.remove('scale-95');
  authModalBox.classList.add('scale-100');
}

function closeAuthModal() {
  authModal.classList.add('pointer-events-none', 'opacity-0');
  authModalBox.classList.remove('scale-100');
  authModalBox.classList.add('scale-95');
}

document.getElementById('closeAuthBtn')?.addEventListener('click', closeAuthModal);

function toggleAuthView(view) {
  if (view === 'join') {
    loginView.classList.add('hidden');
    joinView.classList.remove('hidden');
    
    const joinAgeSelect = document.getElementById('joinAgeGroup');
    const selectedAgeRaw = selectionState.age.replace(/[^0-9]/g, '');
    if (selectedAgeRaw && joinAgeSelect) {
      Array.from(joinAgeSelect.options).forEach(opt => {
        if (opt.value.includes(selectedAgeRaw)) opt.selected = true;
      });
    }
  } else {
    joinView.classList.add('hidden');
    loginView.classList.remove('hidden');
  }
}

// 아이디 중복확인 연동 (views.py check_id 연동)
let checkedId = null;

document.getElementById('joinId')?.addEventListener('input', () => {
  checkedId = null;
  const msg = document.getElementById('idCheckMsg');
  if (msg) {
    msg.innerText = '';
    msg.classList.add('hidden');
  }
});

document.getElementById('joinIdCheckBtn')?.addEventListener('click', async function() {
  const input = document.getElementById('joinId');
  const msg = document.getElementById('idCheckMsg');
  const button = document.getElementById('joinIdCheckBtn');
  if (!input || !msg) return;

  const value = input.value.trim();
  input.value = value;
  checkedId = null;
  
  if (!value) {
    msg.className = 'text-[11px] mt-1 text-red-500 font-medium block';
    msg.innerText = '아이디를 입력해 주세요.';
    input.focus();
    return;
  }

  button.disabled = true;
  msg.className = 'text-[11px] mt-1 text-stone-500 block';
  msg.innerText = '확인 중입니다.';

  const checkUrl = (window.DJANGO_CHECK_ID_URL && !window.DJANGO_CHECK_ID_URL.includes('{%'))
    ? window.DJANGO_CHECK_ID_URL
    : '/member/check_id/';

  try {
    const response = await fetch(`${checkUrl}?` + new URLSearchParams({ id: value }), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      cache: 'no-store'
    });

    if (!response.ok) throw new Error('check failed');
    const result = await response.json();

    if (input.value.trim() !== value) return;

    if (result.available) {
      checkedId = value;
      msg.className = 'text-[11px] mt-1 text-emerald-600 font-semibold block';
      msg.innerText = result.message || '이용가능한 아이디입니다.';
    } else {
      checkedId = null;
      msg.className = 'text-[11px] mt-1 text-red-500 font-medium block';
      msg.innerText = result.message || '중복이 되어 사용할 수 없습니다.';
    }
  } catch (error) {
    msg.className = 'text-[11px] mt-1 text-red-500 font-medium block';
    msg.innerText = '중복확인을 하지 못했습니다.';
  } finally {
    button.disabled = false;
  }
});

// 회원가입 제출 처리 (views.py join 연동)
async function handleDjangoJoin(event) {
  event.preventDefault();

  const inputId = document.getElementById('joinId');
  const msg = document.getElementById('idCheckMsg');
  const pw = document.getElementById('joinPw').value;
  const pw2 = document.getElementById('joinPw2').value;
  const submitBtn = document.getElementById('joinSubmitBtn');

  if (checkedId === null || inputId.value.trim() !== checkedId) {
    msg.className = 'text-[11px] mt-1 text-red-500 font-medium block';
    msg.innerText = '아이디 중복확인을 먼저 진행해 주세요.';
    inputId.focus();
    return;
  }

  if (pw !== pw2) {
    showToast('비밀번호가 서로 일치하지 않습니다.');
    document.getElementById('joinPw2').focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerText = '가입 처리 중...';

  const joinForm = document.getElementById('joinForm');
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

    // views.py의 join은 성공 시 /member/login/?joined=1 로 리다이렉트함
    if (response.redirected || response.ok) {
      showToast('회원가입이 완료되었습니다! 로그인해 주세요.');
      toggleAuthView('login');
      document.getElementById('loginId').value = checkedId;
      document.getElementById('loginPw').focus();
    } else {
      showToast('회원가입에 실패했습니다.');
    }
  } catch (error) {
    joinForm.submit();
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = '가입하기';
  }
}

function getCsrfToken() {
  const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenInput ? tokenInput.value : '';
}

// 기존 views.py의 login 함수와 완벽 호환되는 로그인 폼 제출 처리
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('loginSubmitBtn');
    const errMsg = document.getElementById('loginErrMsg');
    if (errMsg) errMsg.classList.add('hidden');

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = '로그인 중...';
    }

    const formData = new FormData(loginForm);
    const targetUrl = pendingUrl || document.getElementById('loginNextUrl')?.value || '/tour/';

    try {
      const response = await fetch(loginForm.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrfToken()
        },
        body: formData
      });

      const htmlText = await response.text();
      let isLoginSuccess = false;

      // views.py의 login 실패 시 'msg': '아이디 또는 비밀번호가 맞지 않습니다.'를 render(login.html)함
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
        // views.py가 redirect('main') 등을 호출해 이동한 경우 성공
        const redirectedPath = new URL(response.url, window.location.origin).pathname;
        isLoginSuccess = !redirectedPath.includes('login');
      } else {
        // 응답 HTML 안에 로그인 폼(name="pw")이 다시 나타나지 않았다면 성공으로 판정
        const hasLoginForm = htmlText.includes('name="pw"') || htmlText.includes("name='pw'");
        isLoginSuccess = !hasLoginForm;
      }

      if (isLoginSuccess) {
        isLoggedIn = true;
        sessionStorage.setItem('tm_logged_in', 'true');
        closeAuthModal();
        
        // ✅ views.py에서 /admin/ 으로 리다이렉트되었거나 관리자 계정인 경우 /admin/으로 이동
        let finalRedirectUrl = targetUrl;
        if (response.url && response.url.includes('/admin/')) {
          finalRedirectUrl = '/admin/';
        }
        
        window.location.href = finalRedirectUrl;
      } else {
        if (errMsg) {
          errMsg.innerText = '아이디 또는 비밀번호가 맞지 않습니다.';
          errMsg.classList.remove('hidden');
        }
      }
    } catch (error) {
      if (errMsg) {
        errMsg.innerText = '로그인 서버와 통신할 수 없습니다.';
        errMsg.classList.remove('hidden');
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = '로그인';
      }
    }
  });
}

// 6. 카드 클릭 및 하단 다이나믹 버튼 클릭 시 URL 이동 로직
const destCards = document.querySelectorAll('.dest-card');

destCards.forEach(card => {
  card.addEventListener('click', () => {
    const region = card.getAttribute('data-region') || '';
    
    destCards.forEach(c => {
      c.classList.remove('active', 'border-brand-800', 'bg-[#FBF9F6]');
      c.classList.add('border-transparent', 'bg-white', 'shadow-sm');
    });
    card.classList.add('active', 'border-brand-800', 'bg-[#FBF9F6]');
    card.classList.remove('border-transparent', 'bg-white', 'shadow-sm');

    const tourUrl = `/tour/?region=${encodeURIComponent(region)}`;
    
    requireAuth(() => {
      window.location.href = tourUrl;
    }, tourUrl);
  });
});

document.getElementById('backBtn')?.addEventListener('click', () => {
  const step1 = document.getElementById('step1Content');
  const step2 = document.getElementById('step2Content');
  
  step2.classList.remove('opacity-100', 'flex');
  step2.classList.add('opacity-0', 'hidden');

  syncLeftPanel(1);

  step1.classList.remove('hidden');
  void step1.offsetHeight;
  step1.classList.remove('opacity-0');
  step1.classList.add('opacity-100');
});

function getFirstRegion() {
  const firstCard = document.querySelector('.dest-card');
  return firstCard ? firstCard.getAttribute('data-region') || '강원 강릉시' : '강원 강릉시';
}

// 1) 📊 1위 이유 보기 -> /tour/graph_v1/
document.getElementById('btnStats')?.addEventListener('click', () => {
  const region = getFirstRegion();
  const url = `/tour/graph_v1/?region=${encodeURIComponent(region)}`;
  requireAuth(() => {
    window.location.href = url;
  }, url);
});

// 2) 🏆 1위 핫플 TOP10 -> /tour/
document.getElementById('btnTop10')?.addEventListener('click', () => {
  const region = getFirstRegion();
  const url = `/tour/`;
  /*const url = `/tour/?region=${encodeURIComponent(region)}`;*/
  
  requireAuth(() => {
    window.location.href = url;
  }, url);
});

// 3) 🎫 1위 예약하기 -> /tour/resv/
document.getElementById('btnBook')?.addEventListener('click', () => {
  const region = getFirstRegion();
  const url = `/tour/resv/?region=${encodeURIComponent(region)}`;
  requireAuth(() => {
    window.location.href = url;
  }, url);
});

function showToast(message) {
  const existingToast = document.getElementById('toast');
  const existingToastMsg = document.getElementById('toastMsg');
  if (existingToast && existingToastMsg) {
    existingToastMsg.innerText = message;
    existingToast.classList.remove('opacity-0', 'pointer-events-none');
    setTimeout(() => {
      existingToast.classList.add('opacity-0', 'pointer-events-none');
    }, 2500);
  }
}