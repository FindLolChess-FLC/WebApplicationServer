# 작성한 메타 설명을 배포 DB에 반영하기

이번 전달 파일은 `Crawling/data/meta_guides.json`이며 48개 설명을 포함한다. DB 접속 정보·계정·로컬 DB ID는 포함하지 않는다. 기존 MetaGuide 모델을 사용하므로 이 기능 때문에 새 마이그레이션을 만들 필요는 없다. 배포 DB에는 기존 MetaGuide 마이그레이션이 이미 적용돼 있어야 한다.

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

서버 체크아웃이 deploy 브랜치인지 먼저 확인한다. 다른 브랜치라면 작업 내용을 확인한 뒤 deploy로 전환한다. Git pull이 충돌·로컬 변경 때문에 실패하면 이후 명령을 진행하기 전에 해당 상태를 해결한다.

`--dry-run`은 저장하지 않고 적용 예정 항목과 건너뛸 이유를 출력한다. 실제 실행에서도 다음 조건을 모두 만족하는 기존 덱의 빈 설명만 채운다.

- 공백을 제외한 제목이 정확히 일치하며 대상이 하나뿐임
- 대표 레벨이 같음
- 챔피언·성급·배치 위치·장착 아이템이 일치함. 이름의 공백과 아이템 나열 순서는 무시함
- 출처에 관계없이 level=0의 비어 있지 않은 설명이 아직 없음

조건이 다른 덱은 추정해 연결하지 않는다. 없는 덱을 새로 만들거나 챔피언·아이템·배치·댓글을 수정하지 않는다. 여러 번 실행해도 이미 설명이 있는 덱은 건너뛴다. 저장은 하나의 트랜잭션으로 처리한다.

반영 수는 서버 덱 구성과 기존 설명 상태에 따라 48개보다 적을 수 있다. `대표 레벨 또는 배치·성급·아이템 다름`이 나오면 최신 보드와 작성 내용을 검토해야 하며, 강제 덮어쓰기로 해결하지 않는다.

DB 설명만 추가하는 작업이므로 Nginx·uWSGI 재시작은 필요하지 않다. 크롤러를 실행하거나 브라우저를 설치할 필요도 없다. 해당 서버가 이미 detail_info를 응답하는 코드를 사용하고 있다는 전제다.

## 수행한 로컬 검증

- Django 시스템 검사 통과
- 파일 48개 항목의 형식 및 로컬 대표 보드 일치 확인
- dry-run 및 실제 재실행에서 이미 저장된 48개를 모두 건너뛰고 기존 가이드 전체를 보존함을 확인
- 빈 설명에 최초 저장하는 배포 DB 경로와 Ubuntu 서버 실행은 아직 직접 검증하지 않음

새 테스트 파일은 작성하지 않았다. Linux에서 동일한 관리 명령을 사용하는 구조이며 Firefox·Chromium 설정은 변경하지 않았다.
