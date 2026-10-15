# Infolumi Reference Search

DOCX의 참고문헌을 언어모델로 구조화하고 PubMed에서 조회해 정리된 참고문헌을
돌려주는 Discord 봇입니다. 범용 대화 봇과 달리 문헌 처리에 집중합니다.

```mermaid
flowchart LR
    D[DOCX attachment] --> P[Parse reference batches]
    P --> S[PubMed search]
    S --> I[Match articles by PMID]
    I --> O[DOCX or TXT reply]
```

`infolumi_reference_search`의 스레드 응답·DOCX 출력 흐름을 기준으로 삼고,
`Infolumi_bot`의 TXT 출력은 `output_format=txt` 옵션으로 통합했습니다.
동일했던 모델·메모리·유틸리티 파일은 한 벌만 남겼습니다. 서버 변형의 사용되지
않는 범용 대화 메서드는 이 문헌검색 봇에 이식하지 않았습니다.

통합 과정에서 다음을 수정했습니다.

- 첫 번째 묶음 뒤의 `break`를 제거하여 모든 참고문헌을 처리합니다.
- 잘못된 모델 JSON 응답은 원래 순서를 유지한 누락 항목으로 처리합니다.
- PubMed 응답 순서를 가정하지 않고 PMID로 원래 문헌과 연결합니다.
- 빈 응답·단일 저자·단체 저자·일부 누락 메타데이터를 처리합니다.
- 입력과 출력은 임시 디렉터리에 두고 응답 후 정리합니다.
- 외부 HTTP 요청에 timeout을 둡니다.

`llmbot.py`는 Discord/모델 연결, `reference_processing.py`는 네트워크 호출이
없는 파싱·정렬·서식 처리입니다. DOCX가 기본 출력이며 외부 Hydra 설정에서
`output_format`을 `txt`로 지정하면 TXT로 반환합니다.

```bash
python -m unittest discover -s tests -v
```

위 테스트는 합성 문헌만 사용하며 Discord·PubMed·모델을 호출하지 않습니다.
실제 서비스 연동은 별도 검증이 필요합니다. 실행에는 discord.py, LangChain,
Hydra/OmegaConf, python-docx, requests, xmltodict와 비공개 설정이 필요합니다.
토큰·채널 ID·개인 문헌·프롬프트 설정은 포함하지 않았습니다.
