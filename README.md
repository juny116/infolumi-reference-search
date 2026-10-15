# Infolumi Reference Search

DOCX 문서의 참고문헌을 읽고 PubMed에서 서지 정보를 찾아 정리해 주는 Discord 봇입니다. 언어모델로 참고문헌을 구조화한 뒤 논문 메타데이터를 조회해 DOCX 또는 TXT 파일로 반환합니다.

## 처리 흐름

1. Discord에 첨부된 DOCX에서 참고문헌을 읽습니다.
2. 참고문헌을 묶음으로 나누어 모델에 구조화를 요청합니다.
3. PubMed에서 논문을 검색하고 PMID로 메타데이터를 연결합니다.
4. 저자·제목 등의 정보를 정리하고 원래 문헌 순서에 맞춰 출력합니다.
5. Discord 스레드에 완성된 파일을 보냅니다.

## 코드 구조

| 경로 | 역할 |
|---|---|
| `llmbot.py` | Discord 이벤트, 문서 처리와 PubMed 검색·조회 |
| `reference_processing.py` | 묶음 처리, 모델 JSON 파싱, PMID 매칭과 참고문헌 서식 |
| `models.py` | 언어모델 loader |
| `utils.py` | 메시지와 프롬프트 변환 |
| `tests/test_reference_processing.py` | 파싱·매칭·서식 처리 테스트 |

## 출력 형식

기본 출력은 DOCX입니다. Hydra 설정의 `output_format`을 `txt`로 지정하면 TXT를 반환합니다. 입력 문서와 생성 파일은 임시 디렉터리에서 처리합니다.

진입점은 `llmbot.py`이며 `conf/config`에서 Discord 연결 정보와 모델·프롬프트를 읽습니다. 주요 의존성은 discord.py, LangChain, Hydra/OmegaConf, python-docx, requests와 xmltodict입니다.

## 테스트

참고문헌 파싱, PMID 매칭과 서식 처리 테스트를 실행합니다.

```bash
python -m unittest discover -s tests -v
```
