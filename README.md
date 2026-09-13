# WebApplicationServer
FLC 장고 웹 애플리케이션 서버

## 시즌18 데이터 수집

```sh
# 기본은 DB에 저장하지 않습니다.
python manage.py synergy_crawl --season 18 --output synergies.json

# 수집 결과를 검토한 뒤 명시적으로 저장할 때만 사용합니다.
python manage.py synergy_crawl --season 18 --save

# DB에 저장된 원본 URL에서 시너지 SVG를 tft/시너지에 저장합니다.
python manage.py synergy_images

# 시즌18 아이템을 수집·저장하고 원본 이미지를 내려받습니다.
python manage.py item_crawl --season 18 --save
python manage.py item_images

# 시즌18 증강체를 수집·저장하고 등급별 원본 이미지를 내려받습니다.
python manage.py augment_crawl --season 18 --save
python manage.py augment_images

# 시즌18 챔피언을 수집·저장하고 원본 초상화를 내려받습니다.
python manage.py champion_crawl --season 18 --save
python manage.py champion_images

# 로컬 이미지 전체를 Cloudinary CDN에 올리고 DB 이미지 URL을 갱신합니다.
# tft/시너지/<이름>.svg, tft/아이템/<이름>.png 등 한글 경로를 사용합니다.
python manage.py upload_media_cdn

# lolchess.gg 시즌18 추천 메타 덱을 DB 참조와 대조한 뒤 저장합니다.
# 메타 덱의 소환 유닛 이미지는 tft/챔피언에 내려받아 Cloudinary에 올리고,
# 가격 0 챔피언 및 배치 정보도 함께 저장합니다.
python manage.py lolchess_meta_crawl --season 18

# DB를 변경하지 않고 참조 검증만 실행할 수 있습니다.
python manage.py lolchess_meta_crawl --season 18 --dry-run

# 세 사이트(lolchess.gg, OP.GG, tactics.tools)를 한 번에 수집합니다.
# 기존 DB 및 사이트 간 Jaccard 0.8 또는 저코스트 한 명 교체 덱을 제외합니다.
# 4코스트 이상 챔피언 교체는 별도 덱으로 유지합니다.
# 서로 다른 덱의 제목이 같으면 제목 2, 제목 3처럼 번호를 붙입니다.
# 실제 배치를 확인할 수 없는 덱은 위치를 추정하지 않고 저장에서 제외합니다.
python manage.py meta_crawl

# 세 사이트 수집·중복 판정만 확인하고 DB는 변경하지 않습니다.
python manage.py meta_crawl --dry-run

# DB가 필요 없는 회귀 테스트
python -m unittest Crawling.tests -v
```

Chrome 및 호환되는 ChromeDriver가 필요합니다. 이름·설명·이미지는 가이드에서,
활성 인원별 등급은 통계 페이지에서 수집합니다. 통계에 없는 특성은 경고를 내고
빈 sequence로 보존합니다. 크롤링 직후에는 이미지에 원본 CDN URL을 사용하며,
`upload_media_cdn` 실행 후 Cloudinary URL로 바뀝니다. 재수집하면 원본 URL로
갱신되므로 로컬 이미지 다운로드와 CDN 업로드 명령을 다시 실행해야 합니다.
재수집 저장은 이름 기준으로 갱신하며, 과거 시즌 데이터 삭제는 수행하지 않습니다.

시즌18 기초 데이터는 시너지 → 아이템 → 증강체 → 챔피언 순서로 수집합니다.

Linux 배포 환경에서는 Chrome/Chromium과 ChromeDriver가 있으면 이를 사용하고,
없으면 Firefox와 GeckoDriver로 헤드리스 실행합니다. 실행 파일을 PATH에 두거나
`CHROME_BIN`, `CHROMEDRIVER_PATH`, `FIREFOX_BIN`, `GECKODRIVER_PATH`로 경로를
지정하세요. Chrome 크롤러는 `--headless=new`와 독립 프로필을 사용하며,
Chrome이 표시하는 `HeadlessChrome` User-Agent 토큰을 설치된 버전의 일반
`Chrome` 토큰으로 바꿔 OP.GG 페이지를 요청합니다. 컨테이너에서 root로 실행할
때만 Chrome의 `--no-sandbox` 옵션을 사용하므로, 가능하면 비권한 사용자로
실행하세요. 수집 페이지에 접근하지 못하면 명령이 오류를 내고 DB는 변경하지
않습니다. tactics.tools는 배치를 확인할 수 없는 덱을 저장하지 않고 목록과
중복 판정에 사용합니다.
