# WebApplicationServer
FLC 장고 웹 애플리케이션 서버

## 시즌18 데이터 수집

배포 서버는 기초 데이터를 수집할 때 이미 업로드된 Cloudinary 자산의 실제 URL을
조회해 저장합니다. 이미지 파일을 서버에 내려받거나 업로드하지 않습니다.
`CLOUDNARY_NAME`, `CLOUDNARY_KEY`, `CLOUDNARY_SECRET`이 필요합니다.

```sh
python manage.py migrate
python manage.py data_crawl
python manage.py meta_crawl
```


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
# 챔피언·아이템 기초 데이터는 먼저 DB에 있어야 합니다.
# 메타 수집 명령은 이미지를 다운로드하거나 업로드하지 않습니다.
python manage.py lolchess_meta_crawl --season 18

# DB를 변경하지 않고 참조 검증만 실행할 수 있습니다.
python manage.py lolchess_meta_crawl --season 18 --dry-run

# 세 사이트(lolchess.gg, OP.GG, tactics.tools)를 한 번에 수집합니다.
# 기존 DB 및 사이트 간 Jaccard 0.85 이상인 덱을 제외합니다.
# 4코스트 이상 챔피언 교체는 별도 덱으로 유지합니다.
# 서로 다른 덱의 제목이 같으면 제목 2, 제목 3처럼 번호를 붙입니다.
# 실제 배치를 확인할 수 없는 덱은 위치를 추정하지 않고 저장에서 제외합니다.
python manage.py meta_crawl

# 세 사이트 수집·중복 판정만 확인하고 DB는 변경하지 않습니다.
python manage.py meta_crawl --dry-run

# 상세 설명과 기본 레벨 저장을 위한 마이그레이션을 먼저 적용합니다.
python manage.py migrate

# meta_crawl은 덱 설명과 레벨별 배치도 함께 갱신합니다.
# 기존 덱의 설명·레벨 배치만 갱신하려면 아래 명령을 사용합니다.
python manage.py meta_detail_crawl
python manage.py meta_detail_crawl --source lolchess --dry-run

# DB가 필요 없는 회귀 테스트
python -m unittest Crawling.tests -v
```

메타 검색 POST 본문은 `{"data": "메타 ID 또는 검색어", "level": 5}`처럼
선택적인 `level` 항목을 사용합니다. 생략하면 검색 결과 각각의 대표 배치를 반환합니다.
GET 목록 조회는 `/meta/metasearch/?level=5`처럼 쿼리스트링을 사용합니다.
`meta.champions`와 `synergys`는 실제 선택한 레벨의 배치입니다.
`detail_info`는 줄바꿈이 포함된 덱 설명입니다. `meta.default_level`은 대표 레벨,
`selected_level`은 실제 반환한 레벨입니다. 선택한 배치의 챔피언·아이템·위치는
`meta.champions`, 시너지는 `synergys`에 들어갑니다.
`available_levels`는 배치가 저장된 레벨과 대표 레벨을 중복 없이 오름차순으로
반환합니다. 프론트는 이 목록의 레벨만 선택 버튼으로 표시하면 됩니다.
대표 배치만 있는 메타는 대표 레벨 하나만 반환하며, `level_data`는 반환하지 않습니다.
`level`을 생략하거나 해당 레벨 자료가 없으면 대표 배치를 반환합니다.
유효하지 않은 `level`(정수가 아니거나 1~10 범위 밖)은 HTTP 400을 반환합니다.

롤체지지는 가이드 API의 5~10레벨 배치, OP.GG는 초중반 배치표의 4~10레벨 배치를
수집합니다. 출처에 연결된 배치가 없는 레벨은 추가하지 않습니다. tactics.tools에는
레벨별 통계·9레벨 조합 목록이 있지만 위치가 포함된 레벨별 배치가 없어 대표 배치를
사용합니다. DB 참조가 없는 유닛·아이템이 포함된 레벨은 로그를 남기고 건너뜁니다.
기초 데이터를 갱신한 뒤 다시 수집하면 반영됩니다.

덱 설명은 관리자 댓글을 새로 작성하지 않고 `MetaGuide`에 저장합니다. 마이그레이션은
기존 출처 태그 또는 크롤러 추적 정보로 식별되는 슈퍼관리자 댓글을 상세 설명으로
복사하며, 원본 댓글은 보존합니다. 기존 `meta_comment_crawl` 명령은
`meta_detail_crawl`의 호환 명령으로 동작합니다.

Chrome 및 호환되는 ChromeDriver가 필요합니다. 이름·설명·이미지는 가이드에서,
활성 인원별 등급은 통계 페이지에서 수집합니다. 통계에 없는 특성은 경고를 내고
빈 sequence로 보존합니다. 크롤링 직후에는 이미지에 원본 CDN URL을 사용하며,
`upload_media_cdn` 실행 후 Cloudinary URL로 바뀝니다. 재수집하면 원본 URL로
갱신되므로 로컬 이미지 다운로드와 CDN 업로드 명령을 다시 실행해야 합니다.
재수집 저장은 이름 기준으로 갱신하며, 과거 시즌 데이터 삭제는 수행하지 않습니다.

시즌18 기초 데이터는 시너지 → 아이템 → 증강체 → 챔피언 순서로 수집합니다.

Linux 배포 환경의 메타 크롤러는 기존 Firefox/GeckoDriver 설정을 사용합니다.
기본 경로는 `/usr/bin/firefox`, `/usr/local/bin/geckodriver`이며, 다르면
`FIREFOX_BIN`, `GECKODRIVER_PATH`로 지정하세요. Firefox는 headless/eager 설정을
사용하고 각 수집 대상의 데이터가 나타날 때까지 명시적으로 기다립니다.
로컬 Chrome 경로는 `CHROME_BIN`, `CHROMEDRIVER_PATH`로 지정할 수 있습니다.
롤체지지는 브라우저 대신 공개 프런트엔드가 사용하는 데이터 API로 수집합니다.
가이드 배치 ID를 중복 요청하지 않으며 호출 간격과 429/일시 오류 재시도를 적용합니다.
