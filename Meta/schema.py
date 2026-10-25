from drf_yasg import openapi


level_parameter = openapi.Parameter(
    'level', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, minimum=1, maximum=10,
    description='선택한 레벨의 배치를 반환합니다. 생략하거나 자료가 없으면 대표 레벨 배치를 반환합니다.',
    required=False,
)

image_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'img_src': openapi.Schema(type=openapi.TYPE_STRING),
})
item_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'name': openapi.Schema(type=openapi.TYPE_STRING),
    'item1': openapi.Schema(type=openapi.TYPE_STRING),
    'item2': openapi.Schema(type=openapi.TYPE_STRING),
    'effect': openapi.Schema(type=openapi.TYPE_STRING),
    'img': image_schema,
})
placement_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'champion': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'price': openapi.Schema(type=openapi.TYPE_INTEGER),
        'synergy': openapi.Schema(type=openapi.TYPE_ARRAY,
                                  items=openapi.Schema(type=openapi.TYPE_STRING)),
        'img': image_schema,
    }),
    'star': openapi.Schema(type=openapi.TYPE_INTEGER),
    'location': openapi.Schema(type=openapi.TYPE_INTEGER),
    'item': openapi.Schema(type=openapi.TYPE_ARRAY, items=item_schema),
})
placements_schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=placement_schema)
synergy_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'number': openapi.Schema(type=openapi.TYPE_INTEGER),
    'effect': openapi.Schema(type=openapi.TYPE_STRING),
    'img_src': openapi.Schema(type=openapi.TYPE_STRING),
    'sequence': openapi.Schema(type=openapi.TYPE_ARRAY,
                              items=openapi.Schema(type=openapi.TYPE_STRING)),
})
synergies_schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
    type=openapi.TYPE_OBJECT, additional_properties=synergy_schema))
meta_result_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'meta': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'title': openapi.Schema(type=openapi.TYPE_STRING),
        'like_count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'dislike_count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'reroll_lv': openapi.Schema(type=openapi.TYPE_INTEGER),
        'default_level': openapi.Schema(type=openapi.TYPE_INTEGER, description='대표 배치의 레벨'),
        'champions': placements_schema,
    }),
    'synergys': synergies_schema,
    'detail_info': openapi.Schema(type=openapi.TYPE_STRING, description='줄바꿈이 포함된 덱 설명'),
    'selected_level': openapi.Schema(type=openapi.TYPE_INTEGER, description='실제로 반환한 레벨'),
})
lol_meta_schema = openapi.Schema(type=openapi.TYPE_OBJECT, properties={
    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
    'previous_page_url': openapi.Schema(type=openapi.TYPE_STRING, x_nullable=True),
    'next_page_url': openapi.Schema(type=openapi.TYPE_STRING, x_nullable=True),
    'page': openapi.Schema(type=openapi.TYPE_INTEGER),
    'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
    'resultcode': openapi.Schema(type=openapi.TYPE_STRING),
    'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=meta_result_schema),
})

champion_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'data': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_STRING,
                example="바이올렛"
            )
        )
    },
    example={
        "data": [
            "바이올렛",
            "다리우스",
            "밴더",
            "드레이븐",
            "파우더",
            "블라디미르",
            "엘리스",
            "스웨인",
            "사이온"
        ]
    }
)
