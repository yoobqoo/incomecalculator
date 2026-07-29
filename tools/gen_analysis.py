# -*- coding: utf-8 -*-
"""
청약 분석 페이지 생성기 (하이브리드 1단계: 정적 수동 발행)

사용법:
  python tools/gen_analysis.py <HOUSE_MANAGE_NO> <slug>
  예) python tools/gen_analysis.py 2026000355 wolgye-junghung

동작:
  1. 청약홈 API에서 해당 공고의 상세 + 평형별 특공 물량을 가져옴
  2. /analysis/<slug>.html 정적 분석 페이지 생성 (E-E-A-T·JSON-LD 포함)
  3. 생성 후 사람이 검토 → git commit → 배포 (런타임 API 의존 없음)

주의: 경쟁률은 '예측'하지 않는다. 공고문에 있는 확정 물량·소득기준·일정만 팩트로 제시.
"""
import urllib.request, json, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

K = os.environ.get('APARTMENT_API_KEY',
    "17c1015e63414c5f5f8ae48f2bda5b47079578dde490f420775cfd325449ce15")
BASE = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/"

def api(op, extra=""):
    url = BASE+op+"?serviceKey=%s&page=1&perPage=50&returnType=JSON%s" % (K, extra)
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(req, timeout=30)).get('data', [])

def fmt_won(man):
    """만원 단위 정수 → '1억 2,635만원'"""
    try: n = int(man)
    except: return "-"
    if n <= 0: return "-"
    eok, rest = divmod(n, 10000)
    if eok and rest: return "%d억 %s만원" % (eok, format(rest, ','))
    if eok: return "%d억원" % eok
    return "%s만원" % format(rest, ',')

def fmt_date(s):
    if not s or len(s) < 10: return s or "미정"
    return s.replace('-', '.')

def pyeong(area):
    try: return round(float(area)/3.3058)
    except: return None

def clean_ty(house_ty):
    """'059.9667A' → '59A'"""
    m = re.match(r'0*(\d+)\.\d+([A-Z]?)', house_ty or '')
    if m: return m.group(1) + (m.group(2) or '')
    return house_ty or '?'

def build(hmn, slug):
    det = api("getAPTLttotPblancDetail", "&cond[HOUSE_MANAGE_NO::EQ]=%s" % hmn)
    if not det:
        print("공고를 찾을 수 없습니다:", hmn); return
    d = det[0]
    rows = api("getAPTLttotPblancMdl", "&cond[HOUSE_MANAGE_NO::EQ]=%s" % hmn)
    rows = [r for r in rows if r.get('SUPLY_HSHLDCO')]

    name = d.get('HOUSE_NM','').strip()
    region = d.get('SUBSCRPT_AREA_CODE_NM','')
    addr = d.get('HSSPLY_ADRES','')
    builder = d.get('CNSTRCT_ENTRPS_NM','')
    is_public = d.get('PUBLIC_HOUSE_EARTH_AT') == 'Y'
    ptype = "공공분양" if is_public else "민간분양"
    hmpg = d.get('HMPG_ADRES','')
    link = hmpg or ("https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do?houseManageNo=%s&pblancNo=%s" % (hmn, d.get('PBLANC_NO')))

    tot = d.get('TOT_SUPLY_HSHLDCO','')
    dates = [
        ("특별공급 접수", "%s ~ %s" % (fmt_date(d.get('SPSPLY_RCEPT_BGNDE')), fmt_date(d.get('SPSPLY_RCEPT_ENDDE')))),
        ("1순위 접수", "%s ~ %s" % (fmt_date(d.get('RCEPT_BGNDE')), fmt_date(d.get('RCEPT_ENDDE')))),
        ("당첨자 발표", fmt_date(d.get('PRZWNER_PRESNATN_DE'))),
        ("계약", "%s ~" % fmt_date(d.get('CNTRCT_CNCLS_BGNDE'))),
        ("입주 예정", (str(d.get('MVN_PREARNGE_YM') or '')[:4] + "." + str(d.get('MVN_PREARNGE_YM') or '')[4:6]) if d.get('MVN_PREARNGE_YM') else "미정"),
    ]

    # 평형 테이블 행
    trs = []
    for r in rows:
        ty = clean_ty(r.get('HOUSE_TY'))
        ar = r.get('SUPLY_AR')
        py = pyeong(ar)
        trs.append(dict(
            ty=ty, ar=ar, py=py, price=r.get('LTTOT_TOP_AMOUNT'),
            total=r.get('SUPLY_HSHLDCO',0) or 0, sp=r.get('SPSPLY_HSHLDCO',0) or 0,
            gen=r.get('ETC_HSHLDCO',0) or 0,
            nwbb=r.get('NWBB_HSHLDCO',0) or 0, lfe=r.get('LFE_FRST_HSHLDCO',0) or 0,
            nwds=r.get('NWWDS_HSHLDCO',0) or 0, mch=r.get('MNYCH_HSHLDCO',0) or 0,
            old=r.get('OLD_PARNTS_SUPORT_HSHLDCO',0) or 0, inst=r.get('INSTT_RECOMEND_HSHLDCO',0) or 0,
        ))

    # 신혼부부 물량 최다 타입 (분석 코멘트용)
    supplied = [t for t in trs if t['total']>0]
    best_nwbb = max(supplied, key=lambda t:t['nwbb']) if supplied else None
    best_nwds = max(supplied, key=lambda t:t['nwds']) if supplied else None

    def unit_table():
        head = "<tr><th>타입</th><th>면적</th><th>분양가</th><th>총</th><th>일반</th><th>특공</th><th>신혼</th><th>생최</th><th>신생아</th></tr>"
        body = ""
        for t in trs:
            body += ("<tr><td><b>%s</b></td><td>%s㎡<br><small>(약 %s평)</small></td><td>%s</td>"
                     "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>") % (
                t['ty'], t['ar'], t['py'] or '-', fmt_won(t['price']),
                t['total'], t['gen'], t['sp'], t['nwbb'], t['lfe'], t['nwds'])
        return "<table class='u'><thead>%s</thead><tbody>%s</tbody></table>" % (head, body)

    # 특공 유형별 분석 코멘트 (팩트 기반)
    analysis = ""
    if best_nwbb and best_nwbb['nwbb']>0:
        analysis += "<li><b>신혼부부</b>는 <b>%s 타입</b>에 %d세대로 물량이 가장 많습니다. 물량이 많은 타입은 그만큼 신청도 몰릴 수 있으니, 소형 타입의 적은 물량과 경쟁 강도를 함께 저울질하세요.</li>" % (best_nwbb['ty'], best_nwbb['nwbb'])
    if best_nwds and best_nwds['nwds']>0:
        analysis += "<li><b>신생아</b> 특공은 <b>%s 타입</b>에 %d세대로 가장 많이 배정됐습니다. 2년 이내 자녀가 있다면 신생아 트랙이 유리한 경우가 많습니다.</li>" % (best_nwds['ty'], best_nwds['nwds'])
    # 일반공급 유무
    if all(t['gen']==0 for t in trs):
        analysis += "<li>이 단지는 <b>전 타입이 특별공급 중심</b>으로 배정돼 일반공급 물량이 적거나 없습니다. 특공 자격이 되면 특공으로 노리는 것이 유리합니다.</li>"

    desc = "%s %s 청약 정보 총정리 — 평형별(타입별) 세대수, 특별공급 물량(신혼부부·생애최초·신생아), 분양가, 접수 일정과 소득기준까지 청약홈 공식 데이터 기반 분석." % (region, name)

    page_url = "https://homecut.kr/analysis/%s.html" % slug
    article = {
        "@type": "Article",
        "headline": ("%s 청약 분석 — 평형별 특별공급 물량" % name)[:110],
        "description": desc, "inLanguage": "ko",
        "datePublished": "2026-07-22", "dateModified": "2026-07-22",
        "author": {"@type": "Organization", "name": "내집컷 편집팀"},
        "publisher": {"@type": "Organization", "name": "내집컷",
                      "logo": {"@type": "ImageObject", "url": "https://homecut.kr/logo.svg"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
        "image": "https://homecut.kr/og.png", "isBasedOn": "한국부동산원 청약홈 공급정보",
    }
    crumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": "https://homecut.kr/"},
        {"@type": "ListItem", "position": 2, "name": "청약 분석", "item": "https://homecut.kr/analysis/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": page_url},
    ]}
    JSONLD = json.dumps({"@context": "https://schema.org", "@graph": [article, crumbs]},
                        ensure_ascii=False, indent=2)

    html = TEMPLATE
    reps = {
      '__TITLE__': "%s 청약 분석 — 평형별 특공 물량·소득기준 | 내집컷" % name,
      '__DESC__': desc, '__SLUG__': slug, '__OGT__': "%s 청약 분석" % name,
      '__NAME__': name, '__REGION__': region, '__PTYPE__': ptype,
      '__ADDR__': addr, '__BUILDER__': builder, '__TOT__': str(tot), '__LINK__': link,
      '__DATES__': "".join("<tr><td>%s</td><td><b>%s</b></td></tr>"%(k,v) for k,v in dates),
      '__UNITTABLE__': unit_table(),
      '__ANALYSIS__': analysis or "<li>평형별 특공 물량은 위 표를 참고하세요.</li>",
      '__NTYPES__': str(len(trs)),
      '__JSONLD__': '<script type="application/ld+json">\n%s\n</script>' % JSONLD,
    }
    for k,v in reps.items(): html = html.replace(k, v)
    os.makedirs('analysis', exist_ok=True)
    path = 'analysis/%s.html' % slug
    open(path,'w',encoding='utf-8').write(html)
    print("생성:", path, "(%d bytes, 평형 %d개)" % (len(html), len(trs)))
    print("   신혼 최다:", best_nwbb['ty'] if best_nwbb else '-', "/ 신생아 최다:", best_nwds['ty'] if best_nwds else '-')


TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5180948563619303" crossorigin="anonymous"></script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-8D1NXGBRTR"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-8D1NXGBRTR');</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <meta name="description" content="__DESC__">
    <link rel="icon" type="image/svg+xml" href="/logo.svg">
    <meta property="og:type" content="article">
    <meta property="og:title" content="__OGT__">
    <meta property="og:description" content="__DESC__">
    <meta property="og:url" content="https://homecut.kr/analysis/__SLUG__.html">
    <meta property="og:image" content="https://homecut.kr/og.png">
    <link rel="canonical" href="https://homecut.kr/analysis/__SLUG__.html">
    <style>
        @font-face { font-family: 'Pretendard'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/pretendard@1.0/Pretendard-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }
        @font-face { font-family: 'Pretendard'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/pretendard@1.0/Pretendard-Bold.woff2') format('woff2'); font-weight: 700; font-display: swap; }
        :root { --bg:#FAFAFA; --surface:#FFFFFF; --surface-2:#F5F5F7; --text:#111113; --text-2:#6E6E73; --text-3:#AEAEB2; --accent:#007AFF; --warn:#FF9500; --border:#F0F0F2; }
        * { box-sizing: border-box; font-family: 'Pretendard', -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg); margin: 0; padding: 20px 16px 48px; color: var(--text); display: flex; justify-content: center; }
        .container { width: 100%; max-width: 720px; }
        .brand { display: flex; align-items: center; gap: 10px; padding: 4px 4px 14px; text-decoration: none; }
        .brand-logo { width: 56px; height: 56px; }
        .brand-name { font-size: 14px; font-weight: 600; color: var(--text-2); line-height: 1.25; }
        .crumbs { font-size: 13px; color: var(--text-3); margin-bottom: 8px; }
        .crumbs a { color: var(--text-3); text-decoration: none; }
        article { background: var(--surface); border-radius: 20px; padding: 28px 24px; border: 1px solid var(--border); }
        h1 { font-size: 24px; line-height: 1.4; letter-spacing: -0.5px; margin: 0 0 8px; }
        .subt { font-size: 14px; color: var(--text-2); margin-bottom: 8px; }
        .byline { display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: center; padding: 11px 14px; background: var(--surface-2); border-radius: 10px; font-size: 12px; color: var(--text-2); margin: 0 0 20px; }
        .byline b { color: var(--text); }
        .byline .sep { color: var(--text-3); }
        h2 { font-size: 18px; margin: 30px 0 12px; letter-spacing: -0.3px; padding-top: 8px; border-top: 1px solid var(--border); }
        h2:first-of-type { border-top: none; padding-top: 0; }
        p, li { font-size: 15px; line-height: 1.75; color: var(--text); letter-spacing: -0.2px; }
        ul { padding-left: 20px; }
        li { margin-bottom: 8px; }
        b { font-weight: 600; }
        a { color: var(--accent); }
        table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
        table.info td { padding: 9px 10px; border-bottom: 1px solid var(--border); }
        table.info td:first-child { color: var(--text-2); width: 38%; }
        table.u { text-align: center; }
        table.u th { background: var(--accent); color: #fff; padding: 8px 4px; font-size: 12px; font-weight: 600; }
        table.u td { padding: 9px 4px; border-bottom: 1px solid var(--border); font-variant-numeric: tabular-nums; }
        table.u td small { color: var(--text-3); font-size: 11px; }
        table.u tbody tr:nth-child(even) { background: var(--surface-2); }
        .cta { display: block; text-align: center; background: var(--accent); color: white; padding: 16px; border-radius: 14px; text-decoration: none; font-weight: 600; margin: 24px 0 8px; font-size: 15px; }
        .official-links { display: flex; gap: 8px; margin: 8px 0; flex-wrap: wrap; }
        .official-links a { display: inline-flex; padding: 8px 14px; background: var(--surface-2); border-radius: 8px; font-size: 13px; font-weight: 600; color: var(--accent); text-decoration: none; }
        .warn-box { background: #FFF8EC; border: 1px solid #FFE4B8; padding: 14px 16px; border-radius: 10px; margin: 20px 0; font-size: 13px; color: var(--text-2); line-height: 1.7; }
        .warn-box b { color: #BF5700; }
        .sources { margin-top: 24px; padding: 14px 16px; background: var(--surface-2); border-radius: 12px; font-size: 13px; color: var(--text-2); line-height: 1.7; }
        .sources a { color: var(--accent); text-decoration: none; }
        footer { margin-top: 24px; text-align: center; font-size: 13px; color: var(--text-3); }
        footer a { color: var(--text-3); margin: 0 6px; text-decoration: none; }
    </style>
</head>
<body>
<div class="container">
    <a href="/" class="brand">
        <img src="/logo.svg" alt="내집컷 로고" class="brand-logo">
        <span class="brand-name">내집컷<br/>청약 소득, 쉽게 확인</span>
    </a>
    <div class="crumbs"><a href="/">홈</a> &rsaquo; <a href="/analysis/">청약 분석</a> &rsaquo; __NAME__</div>
    <article>
        <h1>__NAME__ 청약 분석<br/><span class="subt">평형별 특별공급 물량·소득기준 총정리</span></h1>
        <div class="byline">
            <span><b>__REGION__</b> · __PTYPE__</span><span class="sep">·</span>
            <span>데이터 <b>청약홈 공식</b></span><span class="sep">·</span>
            <span>정리 <b>2026.07.22</b></span>
        </div>

        <h2>기본 정보</h2>
        <table class="info">
            <tr><td>단지명</td><td><b>__NAME__</b></td></tr>
            <tr><td>위치</td><td>__ADDR__</td></tr>
            <tr><td>시공</td><td>__BUILDER__</td></tr>
            <tr><td>구분</td><td>__PTYPE__</td></tr>
            <tr><td>총 공급</td><td><b>__TOT__세대</b> (__NTYPES__개 타입)</td></tr>
        </table>

        <h2>📅 청약 일정</h2>
        <table class="info">__DATES__</table>

        <h2>🏠 평형별 세대수 · 특별공급 물량</h2>
        <p>같은 59㎡라도 <b>타입(A/B)별로 특공 물량이 다릅니다.</b> 아래 표에서 내가 노릴 타입의 특공 세대수를 확인하세요. (단위: 세대)</p>
        __UNITTABLE__
        <p style="font-size:12px;color:var(--text-3);">※ 신혼=신혼부부, 생최=생애최초, 신생아=신생아 특별공급. 다자녀·노부모·기관추천 물량은 공고문 원문 참고.</p>

        <h2>📊 어떤 특공·타입을 노릴까?</h2>
        <ul>__ANALYSIS__</ul>
        <div class="warn-box"><b>⚠️ 경쟁률은 예측이 아닙니다.</b> 위 물량은 청약홈 공식 <b>확정 데이터</b>입니다. 실제 경쟁률은 접수 마감·당첨자 발표 후 청약홈에 공개되며, 인근 단지 과거 경쟁률과 본인 가점·소득을 함께 고려해 판단하세요.</div>

        <h2>💰 내 소득이 기준에 맞을까?</h2>
        <p>특별공급은 소득 기준(도시근로자 월평균소득 대비 %)을 충족해야 신청할 수 있습니다. 신혼부부·생애최초·신생아별 기준이 다르니, 계산기로 내 가구 소득분위부터 확인하세요.</p>
        <a href="/#calculator" class="cta">🧮 내 소득분위 1초 계산 →</a>

        <h2>🔗 공식 청약 페이지</h2>
        <div class="official-links">
            <a href="__LINK__" target="_blank" rel="noopener">모집공고 상세 ↗</a>
            <a href="https://www.applyhome.co.kr" target="_blank" rel="noopener">청약홈 ↗</a>
        </div>

        <div class="sources">
            <b>📚 출처</b><br/>
            평형·물량·일정 데이터: <a href="https://www.applyhome.co.kr" target="_blank" rel="noopener">한국부동산원 청약홈</a> 공급정보 (공공데이터포털 ApplyhomeInfoDetailSvc)<br/>
            소득·자격 기준: <a href="https://www.data.go.kr/data/15035942/fileData.do" target="_blank" rel="noopener">국토교통부 주택청약 FAQ(2024.05)</a>
        </div>
    </article>
    <footer>
        <a href="/">홈</a>·<a href="/analysis/">청약 분석</a>·<a href="/guide/">가이드</a>·<a href="/about.html">소개</a>
    </footer>
</div>
__JSONLD__
</body>
</html>'''

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("사용법: python tools/gen_analysis.py <HOUSE_MANAGE_NO> <slug>")
        sys.exit(1)
    build(sys.argv[1], sys.argv[2])
