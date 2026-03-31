/**
 * 공고 검색 및 매칭 API (Phase 2)
 * 사용자의 소득분위에 맞는 청약홈 공고를 찾습니다.
 *
 * 사용 예:
 * GET /api/search?incomePercent=135&areaCode=11000
 * 응답: 소득 135% 기준으로 신청 가능한 공고 목록
 */

/**
 * 소득분위에 따른 청약 자격 판정
 * @param {number} incomePercent - 사용자의 소득분위 (%)
 * @returns {object} 가능한 청약 자격
 */
function getQualifications(incomePercent) {
  return {
    newlywed: incomePercent <= 160,        // 신혼부부 특공
    firstHome: incomePercent <= 160,        // 생애최초
    publicRent: incomePercent <= 100,       // 공공분양
    newbornException: incomePercent <= 200, // 신생아 특례
    percentile: incomePercent
  };
}

/**
 * 공고 필터링
 * @param {array} announcements - 청약홈 공고 목록
 * @param {object} qualifications - 사용자의 자격
 * @returns {array} 필터링된 공고
 */
function filterAnnouncements(announcements, qualifications) {
  if (!Array.isArray(announcements)) {
    return [];
  }

  return announcements.filter(announcement => {
    // 공고의 소득 요건 해석 (임시 로직)
    const incomeRequirement = parseIncomeRequirement(announcement.incomeText);

    return (
      qualifications.newlywed && incomeRequirement <= 160 ||
      qualifications.firstHome && incomeRequirement <= 160 ||
      qualifications.publicRent && incomeRequirement <= 100 ||
      qualifications.newbornException && incomeRequirement <= 200
    );
  });
}

/**
 * 공고 텍스트에서 소득 요건 추출 (임시)
 * 실제 구현: OCR 또는 PDF 파싱 필요
 * @param {string} incomeText - 공고 소득 요건 텍스트
 * @returns {number} 소득분위 (%)
 */
function parseIncomeRequirement(incomeText) {
  if (!incomeText) return 100;

  // 예: "140%", "160%" 형식 추출
  const match = incomeText.match(/(\d+)%/);
  return match ? parseInt(match[1]) : 100;
}

/**
 * 공고 검색 API
 * @param {object} req - Express 요청 객체
 * @param {object} res - Express 응답 객체
 */
module.exports = async (req, res) => {
  // CORS 헤더
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { incomePercent, areaCode = '11000' } = req.query;

    // 입력값 검증
    if (!incomePercent || isNaN(incomePercent)) {
      return res.status(400).json({
        error: 'Invalid input',
        message: 'incomePercent 파라미터는 숫자여야 합니다.',
        example: '/api/search?incomePercent=135&areaCode=11000'
      });
    }

    const incomePercent_num = parseInt(incomePercent);

    // 사용자의 자격 판정
    const qualifications = getQualifications(incomePercent_num);

    // TODO: 실제 공고 데이터는 proxy.js를 통해 청약홈 API에서 조회
    // 여기서는 구조만 준비
    const mockAnnouncements = [
      {
        id: 1,
        name: 'OO자이 아파트 신혼부부 특공',
        incomeText: '160%',
        areaCode: '11000',
        applicableQualifications: ['newlywed'],
        link: 'https://www.apartmentdb.co.kr'
      }
    ];

    const filteredAnnouncements = filterAnnouncements(
      mockAnnouncements,
      qualifications
    );

    // 응답
    res.status(200).json({
      success: true,
      userIncome: {
        percent: incomePercent_num,
        qualifications
      },
      applicableAnnouncements: filteredAnnouncements,
      totalCount: filteredAnnouncements.length,
      message: incomePercent_num <= 160
        ? `축하합니다! ${incomePercent_num}%로 다양한 청약에 신청 가능합니다.`
        : `현재 소득분위는 ${incomePercent_num}%입니다. 신청 가능한 청약을 확인하세요.`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search Error:', error.message);

    res.status(500).json({
      error: 'Search failed',
      message: error.message
    });
  }
};
