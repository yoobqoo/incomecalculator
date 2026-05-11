/**
 * 청약홈 API 프록시
 * 한국부동산원_청약홈 분양정보 조회 서비스 (15098547) 실시간 API
 *
 * 설정:
 * 1. Vercel 환경변수에 APARTMENT_API_KEY 설정
 * 2. API 엔드포인트: GET /api/proxy?page=1&perPage=200
 */

const axios = require('axios');

// API 설정 (한국부동산원_청약홈 분양정보 조회 서비스 15098547)
const API_KEY = process.env.APARTMENT_API_KEY || '17c1015e63414c5f5f8ae48f2bda5b47079578dde490f420775cfd325449ce15';
const BASE_URL = 'https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail';

/**
 * 날짜 문자열 반환 (YYYY-MM-DD 포맷)
 * @param {number} offsetDays - 오늘 기준 오프셋 (음수: 과거)
 */
function getDateStr(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10); // YYYY-MM-DD
}

/**
 * 청약홈 공고 조회
 * @param {object} req - Express 요청 객체
 * @param {object} res - Express 응답 객체
 */
module.exports = async (req, res) => {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // OPTIONS 요청 처리
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    // API 키 확인
    if (!API_KEY) {
      return res.status(400).json({
        error: 'API_KEY not configured',
        message: 'Vercel 환경변수에 APARTMENT_API_KEY를 설정하세요.'
      });
    }

    // 쿼리 파라미터
    const page    = req.query.page    || 1;
    const perPage = req.query.perPage || 200;

    // URLSearchParams로 직접 URL 구성 (cond 파라미터 인코딩 보장)
    const qs = new URLSearchParams();
    qs.set('serviceKey',          API_KEY);
    qs.set('page',                String(page));
    qs.set('perPage',             String(perPage));
    qs.set('returnType',          'JSON');
    qs.set('cond[RCEPT_ENDDE::GTE]', getDateStr(-60));  // 60일 이내 마감 공고만
    qs.set('sortFields[0]',       'RCRIT_PBLANC_DE');
    qs.set('sortDirections[0]',   'DESC');              // 최신 공고 우선

    const url = `${BASE_URL}?${qs.toString()}`;

    // 실시간 청약홈 API 호출
    const response = await axios.get(url, {
      timeout: 8000,
      headers: { 'Accept': 'application/json' }
    });

    // 응답 데이터 파싱
    const data = response.data;

    // 필드 매핑 (신 API 영문 코드 → 프론트 구조체)
    const announcements = (data.data || []).map(item => {
      const houseManageNo = item.HOUSE_MANAGE_NO;
      const pblancNo      = item.PBLANC_NO;

      // 청약홈 공고 상세 딥링크
      const link = item.HMPG_ADRES
        || `https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do?houseManageNo=${houseManageNo}&pblancNo=${pblancNo}`;

      return {
        id:                    houseManageNo,
        name:                  item.HOUSE_NM,
        announcement:          pblancNo,
        region:                item.SUBSCRPT_AREA_CODE_NM,
        divisionName:          item.HOUSE_SECD_NM,
        recruitDate:           item.RCRIT_PBLANC_DE,
        applicationStart:      item.RCEPT_BGNDE,
        applicationEnd:        item.RCEPT_ENDDE,
        specialApplicationStart: item.SPSPLY_RCEPT_BGNDE,
        specialApplicationEnd:   item.SPSPLY_RCEPT_ENDDE,
        totalUnits:            item.TOT_SUPLY_HSHLDCO  || null,
        isPublic:              item.PUBLIC_HOUSE_EARTH_AT === 'Y',
        link,
      };
    });

    res.status(200).json({
      success:      true,
      totalCount:   data.totalCount   || 0,
      page:         page,
      perPage:      perPage,
      currentCount: data.currentCount || 0,
      announcements,
      timestamp:    new Date().toISOString()
    });

  } catch (error) {
    console.error('API Proxy Error:', error.message);

    res.status(500).json({
      error:   'API request failed',
      message: error.message,
      tips: [
        '1. API 키를 확인하세요',
        '2. 네트워크 연결을 확인하세요',
        '3. API 분당 요청 제한을 확인하세요'
      ]
    });
  }
};
