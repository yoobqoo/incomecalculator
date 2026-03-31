# 소득분위 계산기 🏘️

청약 자격 판독을 위한 소득분위 계산기입니다. 2024년 최신 청약 소득 기준에 따라 신혼부부, 생애최초, 공공분양 등 다양한 특공 자격을 한눈에 확인할 수 있습니다.

## 기능

- **다양한 가구원 수 지원**: 1인~5인 가구 소득 계산
- **맞벌이/외벌이 구분**: 근무자 수에 따른 신혼부부 특공 커트라인 자동 조정
- **성과급 자동 계산**: 연 성과급을 월 평균으로 자동 변환
- **청약 자격 판독**:
  - 신혼부부 특별공급 (140~160%)
  - 생애최초 특별공급 (160%)
  - 공공분양 일반공급 (100%)
  - 신생아 특례 (200%)

## 배포 상태

![Vercel](https://img.shields.io/badge/Vercel-deployed-blue)

**라이브 URL**: [https://your-domain.vercel.app](https://your-domain.vercel.app)

## 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/your-username/income-calculator.git
cd income-calculator

# 로컬 서버 실행 (선택사항)
# Python 3
python -m http.server 8000

# Node.js
npx http-server
```

이후 `http://localhost:8000` 또는 `http://localhost:8080`에서 확인하세요.

## 파일 구조

```
income-calculator/
├── index.html          # 계산기 프론트엔드 (HTML + CSS + JS)
├── vercel.json         # Vercel 배포 설정
├── README.md           # 이 파일
└── api/                # Phase 2: 청약홈 API 연동 (향후 추가)
    ├── proxy.js        # 공공데이터포털 API 프록시
    └── search.js       # 공고 검색 및 매칭
```

## 사용 방법

1. **가구원 수 선택**: 드롭다운에서 1~5인 가구 중 선택
2. **소득 입력**: 각 구성원의 세전 월급과 연 성과급 입력
3. **판독 버튼 클릭**: "내 소득분위 판독하기" 버튼 클릭
4. **결과 확인**: 소득분위(%)와 청약 자격 여부 확인

## 소득 기준 (2024년 기준)

| 가구원 수 | 평균 소득 |
|----------|----------|
| 1인      | 3,350,847원 |
| 2인      | 5,959,606원 |
| 3인      | 7,003,509원 |
| 4인      | 8,248,467원 |
| 5인      | 8,775,071원 |

## Phase 2: 청약홈 API 연동 (계획)

향후 다음 기능들이 추가될 예정입니다:

- ✅ 사용자의 소득분위 자동 계산
- ⏳ 청약홈 API를 통한 실시간 공고 정보 수집
- ⏳ 사용자의 소득분위에 맞는 공고 자동 추천
- ⏳ 공고별 상세 자격 요건 링크 제공

### 구현 기술 스택 (Phase 2)
- 백엔드: Node.js + Express
- 배포: Vercel Serverless Functions
- API: 공공데이터포털 '한국부동산원_청약홈 분양공고 조회 서비스'

## 주의사항

- 이 계산기는 **기본적인 소득 판독용**이며, 실제 청약 신청 시 청약홈 공식 기준을 반드시 확인하세요.
- 성과급은 지난 3년 평균을 사용하는 것이 일반적입니다.
- 세대주 여부, 무주택 여부 등 다른 자격 요건도 확인이 필요합니다.
- 신생아 특례는 출산 예정일 2년 이내에 해당합니다.

## 라이선스

MIT License

## 피드백 및 개선 제안

버그 리포트나 기능 제안은 [GitHub Issues](https://github.com/your-username/income-calculator/issues)에서 받습니다.

---

**마지막 업데이트**: 2026년 3월 31일
