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

# 배포 서버에서는 이미지 파일을 내려받거나 업로드하지 않습니다.
# 이미 올려둔 Cloudinary 자산의 public ID로 Admin API에서 실제 secure_url을 조회해 저장합니다.
# CLOUDNARY_NAME, CLOUDNARY_KEY, CLOUDNARY_SECRET이 필요합니다.
python manage.py data_crawl

# lolchess.gg 시즌18 추천 메타 덱을 DB 참조와 대조한 뒤 저장합니다.
# 메타 덱의 소환 유닛 이미지는 tft/챔피언에 내려받아 Cloudinary에 올리고,
# 가격 0 챔피언 및 배치 정보도 함께 저장합니다.
python manage.py lolchess_meta_crawl --season 18

# DB를 변경하지 않고 참조 검증만 실행할 수 있습니다.
python manage.py lolchess_meta_crawl --season 18 --dry-run

# 세 사이트(lolchess.gg, OP.GG, tactics.tools)를 한 번에 수집합니다.
# 기존 DB 및 사이트 간 Jaccard 0.85 이상인 덱을 제외합니다.
# 챔피언 한 명 교체 및 4코스트 이상 챔피언 추가·교체는 별도 덱으로 유지합니다.
# 서로 다른 덱의 제목이 같으면 제목 2, 제목 3처럼 번호를 붙입니다.
# 실제 배치를 확인할 수 없는 덱은 위치를 추정하지 않고 저장에서 제외합니다.
python manage.py meta_crawl

# 세 사이트 수집·중복 판정만 확인하고 DB는 변경하지 않습니다.
python manage.py meta_crawl --dry-run

# 기존 메타 덱에 연결할 설명을 확인합니다. DB 댓글은 변경하지 않습니다.
python manage.py meta_comment_crawl --dry-run

# 롤체지지의 일반 덱 설명만 슈퍼관리자 댓글로 저장합니다.
python manage.py meta_comment_crawl --source lolchess

# 세 사이트의 설명·팁을 확인해 연결 가능한 댓글만 저장합니다.
# 슈퍼관리자가 여러 명이고 닉네임 admin이 없다면 --writer-id <ID>를 지정합니다.
python manage.py meta_comment_crawl

# DB가 필요 없는 회귀 테스트
python -m unittest Crawling.tests -v
```

Windows 로컬 실행에는 Chrome 및 호환되는 ChromeDriver가 필요합니다. 이름·설명·이미지는 가이드에서,
활성 인원별 등급은 통계 페이지에서 수집합니다. 통계에 없는 특성은 경고를 내고
빈 sequence로 보존합니다. `data_crawl`은 시너지·챔피언·아이템·증강체를
차례대로 수집하고 각 단계에서 Cloudinary에 업로드된 실제 이미지 URL을 조회해
저장합니다. 없는 자산은 URL을 만들어 넣지 않고 해당 단계의 저장을 중단합니다.
개별 수집 명령의 `--save`는 원본 URL을 저장하므로 CDN 업로드 작업을 할 때만
사용하세요.
재수집 저장은 이름 기준으로 갱신하며, 과거 시즌 데이터 삭제는 수행하지 않습니다.

시즌18 기초 데이터는 시너지 → 챔피언 → 아이템 → 증강체 순서로 수집합니다.

Linux 배포에서는 기존 설정인 `/usr/bin/firefox`와
`/usr/local/bin/geckodriver`를 사용해 헤드리스로 실행합니다. 다른 위치에
설치했다면 `FIREFOX_BIN`, `GECKODRIVER_PATH`로 지정하세요. OP.GG에는 기존
Firefox User-Agent 설정을 적용합니다. Linux 이외 환경은 Chrome을 사용합니다.
`meta_crawl`은 세 사이트를 모두 수집한 뒤 저장하며, tactics.tools는 배치를
확인할 수 없는 덱을 저장하지 않고 목록과 중복 판정에 사용합니다.

`meta_comment_crawl`은 먼저 저장된 메타 덱이 있어야 합니다. 롤체지지에서는
덱 제목과 일치하는 일반 설명만 읽고 레벨별 탭과 추천 증강체 탭은 제외합니다.
출처별 슈퍼관리자 댓글을 재실행 시 갱신하며 일반 사용자 댓글은 건드리지
않습니다. OP.GG는 현재 덱별 설명이 없어 저장을 건너뛰고, tactics.tools의
짧은 전략 태그는 제목과 챔피언 구성이 일치하는 기존 메타에만 연결합니다.
이 명령은 이미지 업로드나 로컬 파일 저장을 하지 않습니다.
