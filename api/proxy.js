/**
 * 청약홈 API 프록시
 * 국부동산원 odcloud.kr API를 통해 분양공고를 조회합니다.
 *
 * 설정:
 * 1. Vercel 환경변수에 APARTMENT_API_KEY 설정
 * 2. API 엔드포인트: GET /api/proxy?pageNo=1&numOfRows=20
 */

const axios = require('axios');

// API 설정 (한국부동산원_청약홈_APT 분양정보)
const API_KEY = process.env.APARTMENT_API_KEY || '17c1015e63414c5f5f8ae48f2bda5b47079578dde490f420775cfd325449ce15';
const BASE_URL = 'https://api.odcloud.kr/api/15101046/v1/uddi:14a46595-03dd-47d3-a418-d64e52820598';

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
    const { page = 1, perPage = 20 } = req.query;

    // odcloud.kr API 호출
    const response = await axios.get(BASE_URL, {
      params: {
        serviceKey: API_KEY,
        page,
        perPage,
        returnType: 'JSON'
      },
      timeout: 8000,
      headers: {
        'Accept': 'application/json'
      }
    });

    // 응답 데이터 파싱
    const data = response.data;

    // odcloud.kr API 응답 구조 처리
    const announcements = (data.data || []).map(item => ({
      id: item.주택관리번호,
      name: item.주택명,
      announcement: item.공고번호,
      region: item.공급지역명,
      divisionName: item.분양구분코드명,
      recruitDate: item.모집공고일,
      applicationStart: item.청약접수시작일,
      applicationEnd: item.청약접수종료일,
      specialApplicationStart: item.특별공급접수시작일,
      specialApplicationEnd: item.특별공급접수종료일,
      // incomePercent는 프론트에서 data/criteria.json 매칭 결과로 분기 처리 (공고별 실제 기준)
      link: item.모집공고홈페이지주소 || 'https://www.apartmentdb.co.kr'
    }));

    res.status(200).json({
      success: true,
      totalCount: data.totalCount || 0,
      page: page,
      perPage: perPage,
      currentCount: data.currentCount || 0,
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

