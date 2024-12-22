from drf_yasg import openapi

lol_meta_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='메타 ID', example=2),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description='메타 제목', example="[상징] 섬뜩한힘 브라이어"),
        'augmenter': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description='증강체 목록',
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='증강체 이름', example="마법지팡이"),
                    'effect': openapi.Schema(type=openapi.TYPE_STRING, description='증강체 효과', example="쓸데없이 큰 지팡이를 획득합니다. 아군 유닛의 주문력이 18 증가합니다."),
                    'tier': openapi.Schema(type=openapi.TYPE_STRING, description='증강체 티어', example="Gold"),
                    'img': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'src': openapi.Schema(type=openapi.TYPE_STRING, description='증강체 이미지 URL', example="https://example.com/image.png")
                        }
                    ),
                }
            )
        ),
        'like_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='좋아요 수', example=0),
        'dislike_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='싫어요 수', example=0),
        'reroll_lv': openapi.Schema(type=openapi.TYPE_INTEGER, description='리롤 레벨', example=8),
        'champions': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description='챔피언 목록',
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'champion': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='챔피언 ID', example=1),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='챔피언 이름', example="브라이어"),
                            'synergy': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='챔피언 시너지', example="슬레이어"),
                                    'img': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'src': openapi.Schema(type=openapi.TYPE_STRING, description='시너지 이미지 URL', example="https://example.com/synergy_image.png")
                                        }
                                    ),
                                }
                            ),
                            'star': openapi.Schema(type=openapi.TYPE_INTEGER, description='챔피언 별 등급', example=3),
                            'items': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='챔피언 아이템 목록',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='아이템 이름', example="가고일 돌갑옷"),
                                        'img': openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'src': openapi.Schema(type=openapi.TYPE_STRING, description='아이템 이미지 URL', example="https://example.com/item_image.png")
                                            }
                                        ),
                                    }
                                )
                            )
                        }
                    )
                }
            )
        ),
        'synergys' : openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "시너지 이름": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "number": openapi.Schema(type=openapi.TYPE_INTEGER, description="시너지 개수", example=2),
                    "effect": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="시너지 효과 설명",
                        example="정복자의 처치 관여가 정복 중첩을 부여합니다. 정복 중첩을 충분히 얻으면 전리품이 든 군수품을 엽니다!"
                    ),
                    "img_src": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="시너지 이미지 URL",
                        example="https://example.com/item_image.png"
                    ),
                },
            )
        },
    ),
)
    }
)
