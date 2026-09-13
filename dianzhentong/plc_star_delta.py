"""原创阶段计算与题库，共用既有课程阶段定义。"""
from .star_delta_stages import STAR_DELTA_STAGES, stage_by_id

TOPICS = ("plc_sd_stages", "plc_sd_transition", "plc_sd_interlock")
STAGE_IDS = tuple(s['id'] for s in STAR_DELTA_STAGES)


def star_delta_next(stage, allow, start, stop, stage_end, transition_allowed):
    if stage not in STAGE_IDS:
        raise ValueError("未知教学阶段")
    if any(type(v) is not bool for v in (allow, start, stop, stage_end, transition_allowed)):
        raise ValueError("教学条件必须为布尔量")
    next_stage = stage
    if stop or not allow:
        next_stage, reason = 'stopped', '停止成立或公共允许失效，返回停止。'
    elif stage == 'stopped':
        next_stage = 'star_start' if start else stage
        reason = '启动成立，仅进入星形启动，不跳过阶段。' if start else '没有启动请求，保持停止。'
    elif stage == 'star_start':
        next_stage = 'transition' if stage_end else stage
        reason = '星形结束条件成立，进入转换等待，尚不进入三角。' if stage_end else '星形结束条件未成立，继续星形阶段。'
    elif stage == 'transition':
        next_stage = 'delta_run' if transition_allowed else stage
        reason = '转换允许成立，从等待进入三角运行。' if transition_allowed else '转换允许未成立，继续等待；不能只凭前序结束条件进入三角。'
    else:
        reason = '保持三角运行；前序转换输入不再决定本阶段，停止与公共允许仍有效。'
    return {'stage': next_stage, 'reason': reason}


def _q(qid, stem, stage, inputs, topic, alternatives):
    result = star_delta_next(stage, *inputs)
    answer = str(stage_by_id(result['stage'])['title'])
    return dict(id=qid, chapter_id='p3_unit_4', stem=stem, options=(answer, *alternatives), answer=answer,
                explanation=result['reason'], knowledge_point=('阶段与角色', '转换条件与等待', '互锁与停止优先')[TOPICS.index(topic)],
                card=topic, wrong=alternatives)


QUESTION_SPECS = (
    _q('plc_sd_example', '本模型处于星形启动，公共允许真、启动假、停止假、星形结束真、转换允许真；一次计算后在哪个阶段？', 'star_start', (True, False, False, True, True), TOPICS[1],
       {'三角运行':'一次只转换一个阶段，必须先进入等待，不能直接跨越。', '星形启动':'结束条件已成立，应退出星形阶段。'}),
    _q('plc_sd_begin', '停止阶段，公共允许、启动、星形结束、转换允许都真，停止请求假；一次计算后是什么阶段？', 'stopped', (True, True, False, True, True), TOPICS[0],
       {'三角运行':'输入同时成立也不能跳过星形与等待阶段。', '转换等待':'从停止只能响应启动进入星形，不跳阶段。'}),
    _q('plc_sd_wait_star', '星形启动中，公共允许真、启动假、停止假、星形结束假、转换允许真；结果是什么？', 'star_start', (True, False, False, False, True), TOPICS[1],
       {'转换等待':'退出星形需要星形结束条件，而不是后续转换允许。', '停止':'撤回启动不等于停止；本阶段仍被允许。'}),
    _q('plc_sd_wait', '转换等待中，公共允许真、启动假、停止假、星形结束真、转换允许假；结果是什么？', 'transition', (True, False, False, True, False), TOPICS[1],
       {'三角运行':'等待阶段还需要转换允许，前序结束不能代替它。', '星形启动':'没有返回星形的规则，条件不足时原地等待。'}),
    _q('plc_sd_enter_delta', '转换等待中，公共允许真、启动假、停止假、星形结束假、转换允许真；结果是什么？', 'transition', (True, False, False, False, True), TOPICS[1],
       {'星形启动':'星形已经退出，不因前序条件变假回退。', '转换等待':'本阶段的转换允许已成立，可以进入三角。'}),
    _q('plc_sd_stop', '三角运行中，公共允许、启动、停止、星形结束和转换允许都真；结果是什么？', 'delta_run', (True, True, True, True, True), TOPICS[2],
       {'三角运行':'停止优先于保持及全部转换条件。', '星形启动':'停止与启动同时成立时，不重新启动。'}),
    _q('plc_sd_permission', '转换等待中，公共允许假、启动真、停止假、星形结束真、转换允许真；结果是什么？', 'transition', (False, True, False, True, True), TOPICS[2],
       {'三角运行':'转换允许不能绕过公共允许。', '转换等待':'公共允许失效要求返回停止，而不只是等待。'}),
    dict(id='plc_sd_roles', chapter_id='p3_unit_4', stem='本教学模型的转换等待阶段，哪组角色关系正确？',
         options=('主角色保持，星形和三角角色均未有效', '主与星形角色有效', '星形与三角角色同时有效'),
         answer='主角色保持，星形和三角角色均未有效', explanation='共用阶段定义中星形已退出，三角仍等待允许；互斥不允许两个阶段重叠。',
         knowledge_point='阶段与角色', card=TOPICS[0], wrong={'主与星形角色有效':'这是星形启动阶段，不是转换等待。', '星形与三角角色同时有效':'违反星形与三角互斥要求。'}),
)
OPTION_FEEDBACK = {q['id']: q['wrong'] for q in QUESTION_SPECS}
