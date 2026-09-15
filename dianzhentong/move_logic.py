"""单次同类型整数复制教学模型；无地址、别名或其他写入。"""
TOPICS = ('move_source_target', 'move_execution', 'move_type_direction')
MIN_VALUE, MAX_VALUE = -999, 999
SOURCE_URL = 'https://docs.tia.siemens.cloud/r/en-us/v20/lad-s7-1200-s7-1500/move-operations-s7-1200-s7-1500/move-move-value-s7-1200-s7-1500'


def move_once(source, target, enabled):
    if type(enabled) is not bool:
        raise ValueError('执行条件必须为布尔量')
    if any(type(v) is not int or not MIN_VALUE <= v <= MAX_VALUE for v in (source, target)):
        raise ValueError('本教学模型仅接受-999至999的整数，不接受布尔量、小数或字符串')
    return {'source': source, 'target': source if enabled else target, 'executed': enabled,
            'reason': '执行条件真，将源值复制到目标，源保持不变；不是交换或相加。' if enabled else
                      '执行条件假，本次不复制；题设没有其他写入，目标保留本次执行前值，源不变。'}


def result_label(result):
    return f"A={result['source']}，B={result['target']}"


def _q(qid, stem, source, target, enabled, topic, wrong):
    result = move_once(source, target, enabled)
    answer = result_label(result)
    return dict(id=qid, chapter_id='p4_unit_1', stem=stem, options=(answer, *wrong), answer=answer,
                explanation=result['reason'], knowledge_point=('源与目标', '执行条件与更新', '类型与赋值方向')[TOPICS.index(topic)],
                card=topic, wrong=wrong)


QUESTION_SPECS = (
    _q('move_example', '本题A、B是独立同类型整数变量，无其他写入。A=12、B=3，执行条件真，复制A到B一次后结果是什么？',12,3,True,TOPICS[0],
       {'A=3，B=12':'复制不是交换，源A不被改成B原值。','A=0，B=12':'复制不会清空源A。'}),
    _q('move_negative', 'A、B是独立整数变量，无其他写入。A=-4、B=9，执行条件真，复制A到B后结果是什么？',-4,9,True,TOPICS[0],
       {'A=-4，B=5':'MOVE不是加法，不将源与目标相加。','A=9，B=-4':'复制不交换两个变量。'}),
    _q('move_disabled', '本题无其他写入。A=7、B=2，复制A到B的执行条件假，结果是什么？',7,2,False,TOPICS[1],
       {'A=7，B=7':'条件假不执行复制。','A=7，B=0':'不执行不等于将目标清零。'}),
    _q('move_zero', '独立整数变量A=0、B=8，执行条件真，复制A到B后结果是什么？',0,8,True,TOPICS[0],
       {'A=0，B=8':'源值为0不代表执行条件假，本题明确执行。','A=8，B=0':'源值不会变成旧目标值。'}),
    _q('move_second', '第一次复制后A=5、B=5；随后只把A改成9。第二次复制A到B时执行条件真，无其他写入，结果是什么？',9,5,True,TOPICS[1],
       {'A=9，B=5':'第二次执行读取当前源9，不再保留旧的5。','A=5，B=9':'源A不会被旧目标覆盖。'}),
    _q('move_no_link', '第一次复制后A=5、B=5；随后只把A改成9。第二次执行条件假，无其他写入，结果是什么？',9,5,False,TOPICS[1],
       {'A=9，B=9':'复制不是持续绑定，未执行时B不自动跟随。','A=9，B=0':'无其他写入时保留B原值，不自动清零。'}),
    dict(id='move_types', chapter_id='p4_unit_1', stem='本单元限定源与目标为同类型整数，下列哪项符合本轮学习边界？',
         options=('两个独立的同类型整数变量','把字符串直接当整数复制','把小数自动四舍五入后复制'), answer='两个独立的同类型整数变量',
         explanation='本轮只讨论同类型整数复制，不模拟转换；这不是MOVE全部支持类型的清单。', knowledge_point='类型与赋值方向', card=TOPICS[2],
         wrong={'把字符串直接当整数复制':'字符串转换不属于本单元同类型整数模型。','把小数自动四舍五入后复制':'不应把本轮复制理解成自动取整，类型转换需另行学习。'}),
    dict(id='move_direction', chapter_id='p4_unit_1', stem='要把独立整数变量A的当前值复制给B，应怎样分配源与目标？',
         options=('A是源，B是目标','B是源，A是目标','A和B都是源，没有目标'), answer='A是源，B是目标',
         explanation='先确定谁提供值、谁被更新；复制方向由源和目标角色决定。', knowledge_point='类型与赋值方向', card=TOPICS[2],
         wrong={'B是源，A是目标':'这会把B的值复制给A，方向相反。','A和B都是源，没有目标':'目标承担接收和更新的职责，不能省略。'}),
)
OPTION_FEEDBACK = {q['id']: q['wrong'] for q in QUESTION_SPECS}
