/**
 * 청약홈 API 프록시 (Phase 2)
 * 공공데이터포털 API를 통해 청약홈 분양공고를 조회합니다.
 *
 * 설정 필요:
 * 1. 공공데이터포털(data.go.kr)에서 API 키 발급
 * 2. Vercel 환경변수에 APARTMENT_API_KEY 설정
 * 3. API 엔드포인트: GET /api/proxy?query=...
 */

const axios = require('axios');

// 환경 변수 확인
const API_KEY = process.env.APARTMENT_API_KEY;
const BASE_URL = 'http://apis.data.go.kr/B552496/ApartmentListService/getPubPrevuSearch';

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
    const { pageNo = 1, numOfRows = 10, searchCondition = 'rent' } = req.query;

    // 공공데이터포털 API 호출
    const response = await axios.get(BASE_URL, {
      params: {
        serviceKey: decodeURIComponent(API_KEY),
        pageNo,
        numOfRows,
        searchCondition,
        returnType: 'json'
      },
      timeout: 5000
    });

    // 응답 반환
    res.status(200).json({
      success: true,
      data: response.data,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('API Proxy Error:', error.message);

    res.status(500).json({
      error: 'API request failed',
      message: error.message,
      tips: [
        '1. API 키가 올바른지 확인하세요',
        '2. 공공데이터포털에서 서비스 신청 여부 확인',
        '3. 분당 요청 제한(예: 100회)을 초과했을 수 있습니다'
      ]
    });
  }
};
