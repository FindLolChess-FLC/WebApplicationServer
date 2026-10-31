# 작성한 메타 설명을 배포 DB에 반영하기

이번 전달 파일은 `Crawling/data/meta_guides.json`이며 62개 설명을 포함한다. DB 접속 정보·계정·로컬 DB ID는 포함하지 않는다. 기존 MetaGuide 모델을 사용하므로 이 기능 때문에 새 마이그레이션을 만들 필요는 없다. 배포 DB에는 기존 MetaGuide 마이그레이션이 이미 적용돼 있어야 한다.

## 2026-10-31 갱신 적용

신규 메타까지 가져오려면 설명 가져오기 전에 기존 메타 수집 명령을 실행한다. 로컬 DB는 신규 메타 14개를 포함한 96개이며 작성 설명 파일은 62개다. 서버 데이터와 수집 시점이 다르면 적용 개수도 달라질 수 있다.

```bash
cd ~/srv/WebApplicationServer
source ~/venv/bin/activate
git pull --ff-only origin deploy
python manage.py meta_crawl
python manage.py import_meta_guides --update --dry-run
python manage.py import_meta_guides --update
```

메타와 설명 DB만 변경하므로 재시작이나 새 마이그레이션은 필요하지 않다. Linux Firefox·GeckoDriver 설정은 기존 그대로 사용한다. 수집 시 필요한 기초 챔피언·아이템이 없으면 해당 덱은 제외되므로 로그의 참조 누락을 확인한다. 이번 로컬에서는 깊은숲 수호자 참조가 없어 롤체지지 나무정령 이즈리얼 한 구성을 제외했고, OP.GG에서 배치가 확인된 별도 변형은 저장했다.

## 전달

다음 파일을 deploy 브랜치에 커밋하고 푸시한 뒤 서버에서 받는다.

- `Crawling/crawl/authored_guides.py`
- `Crawling/management/commands/export_meta_guides.py`
- `Crawling/management/commands/import_meta_guides.py`
- `Crawling/data/meta_guides.json`

추후 로컬에서 작성 설명을 추가하면 다음 명령으로 전달 파일을 다시 만든다.

```powershell
.\venv\Scripts\python.exe manage.py export_meta_guides Crawling/data/meta_guides.json
```

## 서버에서 실행

```bash
cd ~/srv/WebApplicationServer
source ~/venv/bin/activate
git pull --ff-only origin deploy
python manage.py import_meta_guides --dry-run
python manage.py import_meta_guides
```

이미 저장한 자체 작성 설명도 갱신하려면 다음 명령을 사용한다. 다른 출처의 설명은 수정하지 않는다. 대응하는 원본이 없으면 기존 문구의 아이템 라벨만 정리한다. 출력은 적용·건너뜀 합계 한 줄이다.

```bash
python manage.py import_meta_guides --update --dry-run
python manage.py import_meta_guides --update
```

`저장된 아이템 예시:`·`저장된 아이템:`은 `아이템:`으로 정리한다. 새로 작성하는 아이템 예시에도 같은 라벨을 사용한다. 기본 실행은 기존 설명을 계속 보존한다.

서버 체크아웃이 deploy 브랜치인지 먼저 확인한다. 다른 브랜치라면 작업 내용을 확인한 뒤 deploy로 전환한다. Git pull이 충돌·로컬 변경 때문에 실패하면 이후 명령을 진행하기 전에 해당 상태를 해결한다.

출력은 `적용 N개 / 건너뜀 N개` 한 줄만 표시한다. `--dry-run`은 DB에 저장하지 않고 `적용 예정 N개 / 건너뜀 N개`만 표시한다. 기본적으로 DB의 빈 설명 전체에 대해 62개 원본 중 적합한 설명을 찾는다. 하나의 원본을 여러 호환 덱에 사용할 수 있으므로 적용 수는 원본 수와 다를 수 있다. 매칭 기준은 변경하지 않았다.

- 공백·문자 정규화와 수집 시 붙은 끝 번호를 고려한다. `Rush 9`처럼 운영을 뜻하는 숫자는 제거하지 않는다.
- 배치 좌표와 일반 대체 아이템 차이는 허용한다. 대표 레벨 차이는 1 이내만 허용한다.
- 소환수를 제외한 챔피언 Jaccard 비율은 같은 제목 계열이면 0.75 이상, 다른 제목이면 0.9 이상이어야 한다.
- 제목에 나온 장착 유닛을 우선 주력으로 식별한다. 없으면 공격 관련 아이템을 2개 이상 장착한 유닛을 기준으로 삼는다. 주력 유닛이 서로 유지돼야 한다.
- 주력의 3성 리롤 여부, 상징 종류와 장착 유닛, 제목에 명시된 특수 증강 조건이 다르면 건너뛴다. 아이템 운영 문단에 필요한 유닛이 빠져도 건너뛴다.
- 유물·상징 요약표는 예외로 같은 제목 계열과 완전 일치한 대표 배치만 허용한다.
- 여러 후보의 점수 차이가 0.04 미만이면 완전 일치 배치나 유일한 정확한 제목을 우선하며, 그래도 구별되지 않으면 건너뛴다.
- 점수는 챔피언 겹침 80%, 공통 유닛 성급 일치 10%, 장착 아이템 겹침 10%다. 전투 승률이나 설명 정확도의 확률이 아니다.
- 아이템 예시 문단은 대상 DB의 현재 배치에 맞춰 재작성한다. 자체 작성한 운영 설명의 추천 후보는 그대로 유지한다.
- 출처에 관계없이 level=0의 비어 있지 않은 설명은 그대로 보존한다.

없는 덱을 새로 만들거나 챔피언·아이템·배치·댓글을 수정하지 않는다. 여러 번 실행해도 이미 설명이 있는 덱은 건너뛴다. 저장은 하나의 트랜잭션으로 처리한다. 상세 설명 연결만 변경하며 메타 크롤링의 중복 제거 기준은 변경하지 않았다.

이전의 제목·대표 배치 완전 일치 방식도 사용할 수 있다.

```bash
python manage.py import_meta_guides --strict --dry-run
```

원본에 없는 덱이나 주력·상징·증강 조건이 다른 덱은 남을 수 있다. 무조건 모든 덱을 연결하는 기능은 아니다.

## 서버에 남은 빈 설명 작성하기

서버의 실제 구성이 로컬과 다르거나 원본 설명에 없는 덱이면 분석 자료를 내보낸다.

```bash
python manage.py export_meta_guides /tmp/flc-missing-meta-context.json --missing
```

출력 파일에는 빈 설명 덱의 제목·대표 레벨·리롤 값·배치·성급·아이템과 해당 챔피언·아이템·특성의 수집 정보만 포함한다. 관련 특수 증강은 DB에 있을 때만 포함하며 최신 게임 수치와 같은 시점이라는 보장은 없다. 계정·댓글·DB 접속 정보·로컬 DB ID는 포함하지 않는다. DB를 변경하지 않는다.

이 파일을 로컬로 전달해 실제 구성에 맞는 설명을 작성한 후 배포용 설명 파일에 추가한다. 분석용 형식은 `flc-meta-context-v1`이므로 설명을 작성하기 전에 가져오기 명령에 직접 넣을 수 없다. 새로 저장되는 설명은 source_id에 원본 설명 제목을 남겨 어떤 설명에서 연결됐는지 확인할 수 있다.

DB 설명만 추가하는 작업이므로 Nginx·uWSGI 재시작은 필요하지 않다. 크롤러를 실행하거나 브라우저를 설치할 필요도 없다. 해당 서버가 이미 detail_info를 응답하는 코드를 사용하고 있다는 전제다.

## 수행한 로컬 검증

- Django 시스템 검사 통과
- 초기 파일 48개 항목의 형식 및 로컬 대표 보드 일치 확인
- dry-run 및 실제 재실행에서 초기 저장된 48개를 모두 건너뛰고 기존 가이드 전체를 보존함을 확인
- 변경된 매칭은 로컬 원본과 위치·아이템·레벨·상징·주력 성급을 바꾼 메모리 내 시나리오로 검증한다. Ubuntu 서버 DB는 직접 접근하지 않음

새 테스트 파일은 작성하지 않았다. Linux에서 동일한 관리 명령을 사용하는 구조이며 Firefox·Chromium 설정은 변경하지 않았다.
