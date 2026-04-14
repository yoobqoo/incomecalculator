/**
 * 청약홈 API 프록시
 * 국부동산원 odcloud.kr API를 통해 분양공고를 조회합니다.
 *
 * 설정:
 * 1. Vercel 환경변수에 APARTMENT_API_KEY 설정
 * 2. API 엔드포인트: GET /api/proxy?pageNo=1&numOfRows=20
 */

const axios = require('axios');

// API 설정
const API_KEY = process.env.APARTMENT_API_KEY || '17c1015e63414c5f5f8ae48f2bda5b47079578dde490f420775cfd325449ce15';
const BASE_URL = 'https://api.odcloud.kr/api/15101046/v1/uddi:cde19cd2-eff1-41f4-a57d-8fb85f0b0e19';

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
    const { pageNo = 1, numOfRows = 20 } = req.query;

    // odcloud.kr API 호출
    const response = await axios.get(BASE_URL, {
      params: {
        serviceKey: API_KEY,
        pageNo,
        numOfRows
      },
      timeout: 8000,
      headers: {
        'Accept': 'application/json'
      }
    });

    // 응답 데이터 파싱
    const data = response.data;

    // odcloud.kr API 응답 구조 처리
    const announcements = (data.response?.[0]?.body?.items || []).map(item => ({
      id: item.bsnsMgtSn,
      name: item.bsnsMgtNm,
      regionCode: item.sgguCd,
      incomePercent: parseIncomePercent(item),
      link: `https://www.apartmentdb.co.kr`
    }));

    res.status(200).json({
      success: true,
      totalCount: data.response?.[0]?.body?.totalCount || 0,
      pageNo: pageNo,
      numOfRows: numOfRows,
      announcements: announcements,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API Proxy Error:', error.message);

    res.status(500).json({
      error: 'API request failed',
      message: error.message,
      tips: [
        '1. API 키를 확인하세요',
        '2. 네트워크 연결을 확인하세요',
        '3. API 분당 요청 제한을 확인하세요'
      ]
    });
  }
};

/**
 * 공고에서 소득분위 추출
 */
function parseIncomePercent(item) {
  // 공고 데이터에서 소득 정보 추출 로직
  // 기본값: 160% (신혼부부/생애최초 기준)
  return 160;
}
