/**
 * Vercel Serverless Function Entry Point
 * 프론트엔드와 API 라우팅을 처리합니다.
 */

module.exports = (req, res) => {
  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // 라우팅
  if (req.url.startsWith('/api/proxy')) {
    const proxy = require('./proxy');
    return proxy(req, res);
  }

  if (req.url.startsWith('/api/search')) {
    const search = require('./search');
    return search(req, res);
  }

  // 정의되지 않은 경로
  res.status(404).json({
    error: 'Not Found',
    availableEndpoints: [
      'GET /api/proxy - 청약홈 공고 조회',
      'GET /api/search - 소득분위별 공고 검색'
    ]
  });
};
