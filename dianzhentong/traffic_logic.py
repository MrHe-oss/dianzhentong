"""原创交通信号教学状态机；不用于实际道路控制。"""
TOPICS = ('traffic_stages', 'traffic_transition', 'traffic_exclusion')
STAGES = {
    'stopped': ('停止', '红', '红'),
    'a_green': ('A绿', '绿', '红'),
    'a_yellow': ('A黄', '黄', '红'),
    'all_red_ab': ('全红过渡（A→B）', '红', '红'),
    'b_green': ('B绿', '红', '绿'),
    'b_yellow': ('B黄', '红', '黄'),
    'all_red_ba': ('全红过渡（B→A）', '红', '红'),
}
CYCLE = tuple(STAGES)[1:]


def traffic_next(stage, allow, start, stop, stage_end):
    if stage not in STAGES:
        raise ValueError('未知教学阶段')
    if any(type(v) is not bool for v in (allow, start, stop, stage_end)):
        raise ValueError('教学条件必须为布尔量')
    if stop or not allow:
        target, reason = 'stopped', '停止或失去允许优先，返回停止；显示全红仅是本题约定。'
    elif stage == 'stopped':
        target = 'a_green' if start else stage
        reason = '有启动请求，仅进入A绿，不跳阶段。' if start else '没有启动请求，保持停止。'
    elif stage_end:
        target = CYCLE[(CYCLE.index(stage) + 1) % len(CYCLE)]
        reason = '本阶段结束条件成立，只前进一个阶段；不在同一次计算继续判断新阶段。'
    else:
        target, reason = stage, '本阶段结束条件不成立，继续等待；撤回启动不等于停止。'
    return {'stage': target, 'reason': reason, 'a': STAGES[target][1], 'b': STAGES[target][2]}


def _q(qid, stem, stage, inputs, topic, wrong):
    result = traffic_next(stage, *inputs)
    answer = STAGES[result['stage']][0]
    return dict(id=qid, chapter_id='p3_unit_5', stem=stem, options=(answer, *wrong), answer=answer,
                explanation=result['reason'], knowledge_point=('阶段与输出', '阶段转换与等待', '冲突约束与停止优先')[TOPICS.index(topic)],
                card=topic, wrong=wrong)


QUESTION_SPECS = (
    _q('traffic_example', '本题从A黄出发，允许真、启动假、停止假、阶段结束真；一次计算后是什么阶段？', 'a_yellow', (True, False, False, True), TOPICS[1],
       {'B绿': '必须先进入全红过渡，不能跳阶段。', 'A黄': '结束条件已成立，不再停留A黄。'}),
    _q('traffic_start', '停止时允许、启动、阶段结束都真，停止假；计算一次后是什么阶段？', 'stopped', (True, True, False, True), TOPICS[0],
       {'A黄': '本次只能启动进入A绿，不能继续使用结束条件。', 'B绿': '不能跳过A组和过渡阶段。'}),
    _q('traffic_wait', '全红过渡（A→B），允许真、启动假、停止假、阶段结束假；下一阶段是什么？', 'all_red_ab', (True, False, False, False), TOPICS[1],
       {'B绿': '当前阶段结束条件未成立，需要等待。', '停止': '全红过渡不是停止阶段，不能仅凭颜色判断。'}),
    _q('traffic_cycle', '全红过渡（B→A），允许真、启动假、停止假、阶段结束真；下一阶段是什么？', 'all_red_ba', (True, False, False, True), TOPICS[1],
       {'B绿': '这一过渡方向是B到A，不是A到B。', '停止': '模型按循环回到A绿，没有收到停止。'}),
    _q('traffic_release', 'B绿中撤回启动，允许真、停止假、阶段结束假；下一阶段是什么？', 'b_green', (True, False, False, False), TOPICS[1],
       {'停止': '启动仅用于离开停止，运行中撤回它不会停机。', 'B黄': '阶段结束条件未成立，不能前进。'}),
    _q('traffic_stop', 'A绿中允许、启动、停止和阶段结束都真；下一阶段是什么？', 'a_green', (True, True, True, True), TOPICS[2],
       {'A黄': '停止优先于阶段结束。', 'A绿': '启动不能覆盖停止请求。'}),
    _q('traffic_allow', 'B黄中允许假、启动真、停止假、阶段结束真；下一阶段是什么？', 'b_yellow', (False, True, False, True), TOPICS[2],
       {'全红过渡（B→A）': '失去允许时回到停止，不是继续循环。', 'B黄': '不允许继续保持运行阶段。'}),
    dict(id='traffic_outputs', chapter_id='p3_unit_5', stem='本模型处于A绿阶段，哪组显示符合阶段定义？',
         options=('A绿、B红', 'A绿、B绿', 'A红、B绿'), answer='A绿、B红',
         explanation='一个阶段只对应一组固定显示；A绿时B为红，不允许两组绿灯同时有效。',
         knowledge_point='阶段与输出', card=TOPICS[0], wrong={'A绿、B绿': '违反本题两组绿灯互斥的约束。', 'A红、B绿': '这是B绿阶段，不是当前A绿阶段。'}),
)
OPTION_FEEDBACK = {q['id']: q['wrong'] for q in QUESTION_SPECS}
