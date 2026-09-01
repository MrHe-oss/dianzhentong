"""章节测验题库与纯规则评分。"""

from __future__ import annotations

import random
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Sequence

from .storage import beijing_now


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    chapter_id: str
    stem: str
    options: tuple[str, ...]
    answer: str
    explanation: str
    knowledge_point: str


@dataclass(frozen=True)
class QuizAnswer:
    question_id: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    uncertain: bool


@dataclass(frozen=True)
class QuizRecord:
    quiz_id: str
    chapter_id: str
    completed_at: str
    correct_count: int
    total_count: int
    passed: bool
    mode: str
    answers: tuple[QuizAnswer, ...]


def _q(number: int, chapter: str, stem: str, options: tuple[str, ...], answer: str,
       explanation: str, point: str) -> QuizQuestion:
    return QuizQuestion(f"q{number:02d}", chapter, stem, options, answer, explanation, point)


QUESTIONS = (
    _q(1,"safety_and_circuits","本平台中的状态卡主要用于什么？",("教学模拟判断","替代现场验电","指导真实送电"),"教学模拟判断","状态卡只承载教学模拟信息，不能替代现场安全措施。","教学边界"),
    _q(2,"safety_and_circuits","主回路的主要作用是什么？",("向负载传递主要电能","保存学习成绩","生成控制命令文本"),"向负载传递主要电能","主回路承担负载主要电能的传递。","主回路"),
    _q(3,"safety_and_circuits","控制回路主要表达什么？",("启停与保护逻辑","机械安装尺寸","云端数据保存"),"启停与保护逻辑","按钮、保护触点和线圈共同表达控制逻辑。","控制回路"),
    _q(4,"safety_and_circuits","模拟资料不足时最合适的选择是？",("不确定","强行判断正常","尝试真实测量"),"不确定","资料不足应保留不确定，不猜测也不进行真实操作。","证据意识"),
    _q(5,"safety_and_circuits","网页诊断结论可以替代哪一项？",("都不能替代","设备说明书","持证人员判断"),"都不能替代","本产品仅用于教学模拟。","安全边界"),
    _q(6,"safety_and_circuits","判断模拟状态前应先做什么？",("明确检查对象和预期状态","直接选择异常","拆开真实线路"),"明确检查对象和预期状态","先明确对象与预期，再比较状态卡。","判断方法"),
    _q(7,"components","常开触点在未动作基准状态通常是？",("断开","闭合","无法定义"),"断开","常开触点在基准状态断开，动作后闭合。","常开触点"),
    _q(8,"components","常闭触点在未动作基准状态通常是？",("闭合","断开","随机变化"),"闭合","常闭触点在基准状态闭合，动作后断开。","常闭触点"),
    _q(9,"components","熔断器在控制逻辑中的典型作用是？",("限制故障影响","维持自锁","改变转向"),"限制故障影响","熔断器属于保护元件，不承担自锁或换向。","熔断器"),
    _q(10,"components","热继电器保护触点动作后可能造成什么现象？",("控制条件中断","接触器永久自锁","两个方向同时启动"),"控制条件中断","保护触点动作会使控制链路不再满足。","热继电器"),
    _q(11,"components","接触器线圈的作用是？",("产生电磁动作带动触点","直接保存电能","判断用户答案"),"产生电磁动作带动触点","线圈得电形成电磁动作并带动触点状态变化。","接触器线圈"),
    _q(12,"components","判断停止按钮常闭触点时，还需要关注什么？",("按钮是否按下","电动机颜色","网页窗口宽度"),"按钮是否按下","触点状态必须结合元件是否动作来理解。","按钮触点"),
    _q(13,"components","短路保护与过载保护是否完全相同？",("不同","完全相同","只看按钮决定"),"不同","两者针对的异常特征与保护元件作用不同。","保护元件"),
    _q(14,"components","启动按钮常用哪类触点表达启动请求？",("常开触点","常闭触点","热继电器触点"),"常开触点","教学控制逻辑中启动按钮通常使用常开触点。","启动按钮"),
    _q(15,"components","停止按钮常用哪类触点串入控制条件？",("常闭触点","常开触点","主触点"),"常闭触点","教学逻辑中停止按钮通常使用常闭触点。","停止按钮"),
    _q(16,"components","元件名称相同就能断定故障相同吗？",("不能，还需结合现象和状态","能","只需看最后一步"),"不能，还需结合现象和状态","故障判断必须结合检查顺序、现象和模拟证据。","证据链"),
    _q(17,"direct_start","直接启动不启动时，推荐先检查哪类条件？",("上游公共条件","直接更换接触器","真实主回路接线"),"上游公共条件","规则树按控制电源、保护和按钮等上游到下游排查。","排查顺序"),
    _q(18,"direct_start","自锁逻辑的主要作用是？",("启动信号消失后维持控制条件","改变旋转方向","提供短路保护"),"启动信号消失后维持控制条件","自锁由辅助触点维持已建立的控制条件。","自锁"),
    _q(19,"direct_start","仅凭“电动机不启动”能否直接判定线圈断路？",("不能","能","只要按过启动按钮就能"),"不能","同一现象可能来自多个控制条件，需要逐步排除。","故障树"),
    _q(20,"direct_start","控制电源模拟状态异常时，应如何理解后续结果？",("上游条件已不满足","后续元件必然全部损坏","应进行带电测量"),"上游条件已不满足","上游控制条件异常已经能够解释不能启动。","控制电源"),
    _q(21,"direct_start","热继电器未复位可能导致？",("启动控制条件中断","电气互锁失效","电源自动升高"),"启动控制条件中断","热继电器保护触点未恢复会中断控制链路。","热继电器"),
    _q(22,"direct_start","启动按钮状态异常而前序正常，最可能指向？",("启动请求未形成","停止按钮一定正常","主回路一定完好"),"启动请求未形成","前序条件正常时，异常启动按钮不能形成启动请求。","启动按钮"),
    _q(23,"direct_start","标准排查记录的重要价值是？",("保留判断依据和顺序","替代安全规程","自动维修真实设备"),"保留判断依据和顺序","记录用于复盘证据链，而不是执行真实维修。","诊断记录"),
    _q(24,"forward_reverse","两个方向均不能启动时应优先考虑？",("公共控制条件","只检查正转按钮","只检查反转线圈"),"公共控制条件","两个方向共同异常时先检查共享的电源、保护和停止条件。","公共回路"),
    _q(25,"forward_reverse","只有正转不能启动时，应重点进入哪一分支？",("正转支路","反转支路","云端存储支路"),"正转支路","公共条件正常后，单方向现象应进入对应方向支路。","现象分支"),
    _q(26,"forward_reverse","电气互锁的教学作用是？",("阻止两个方向同时形成动作条件","保持两个线圈同时动作","替代过载保护"),"阻止两个方向同时形成动作条件","互锁利用另一方向的常闭辅助触点限制同时动作。","电气互锁"),
    _q(27,"forward_reverse","反转按钮异常通常首先影响？",("反转启动请求","正转线圈一定断路","公共电源一定缺失"),"反转启动请求","方向按钮属于对应方向支路。","反转按钮"),
    _q(28,"forward_reverse","正转接触器线圈异常而公共条件正常，可能表现为？",("正转不能启动","两个方向必然都不能启动","反转按钮自动闭合"),"正转不能启动","方向线圈异常主要影响对应方向。","正转线圈"),
    _q(29,"forward_reverse","排查单方向故障前为什么仍要确认公共条件？",("避免把公共异常误判为方向故障","为了真实送电","为了跳过现象判断"),"避免把公共异常误判为方向故障","公共条件同时服务两个方向，是分支判断的前提。","排查顺序"),
    _q(30,"forward_reverse","互锁触点状态异常时，判断依据应来自？",("题目给出的模拟状态和预期逻辑","真实设备试运行","猜测另一接触器状态"),"题目给出的模拟状态和预期逻辑","本平台只能依据模拟资料形成教学结论。","模拟证据"),
    _q(31,"jog_continuous_basics","点动运行的典型教学特征是？",("按住按钮时建立条件，释放后结束","释放按钮后依靠自锁保持","两个接触器同时动作"),"按住按钮时建立条件，释放后结束","点动不依靠自锁维持，按钮释放后运行条件结束。","点动控制"),
    _q(32,"jog_continuous_basics","连续运行与点动相比增加了哪类逻辑？",("保持条件","换向条件","云端同步"),"保持条件","连续运行通过自锁辅助触点维持控制条件。","连续运行"),
    _q(33,"jog_continuous_basics","点动与连续运行均不能启动时，应先检查？",("共享的公共控制条件","只检查点动按钮","只检查自锁触点"),"共享的公共控制条件","两个方式共同异常时，先检查共享的上游条件。","公共条件"),
    _q(34,"jog_continuous_basics","只有点动不能启动时，优先进入哪类分支？",("点动请求支路","连续保持支路","公共云端支路"),"点动请求支路","单一方式异常应进入对应方式支路。","现象分支"),
    _q(35,"jog_continuous_basics","点动和连续运行共享的元件可能包括？",("停止按钮与接触器线圈","只有点动按钮","只有自锁辅助触点"),"停止按钮与接触器线圈","公共停止条件和最终动作线圈可被两种方式共享。","共享元件"),
    _q(36,"jog_continuous_training","连续运行能短暂启动但不能保持，首先提示哪类逻辑？",("自锁保持逻辑","点动按钮一定异常","公共电源一定缺失"),"自锁保持逻辑","启动请求曾形成而无法维持，重点是保持条件。","自锁"),
    _q(37,"jog_continuous_training","自锁辅助触点的作用是？",("启动按钮释放后维持控制条件","提供短路保护","改变旋转方向"),"启动按钮释放后维持控制条件","自锁触点用于维持连续运行的控制条件。","自锁触点"),
    _q(38,"jog_continuous_training","公共条件正常、连续按钮异常时可能出现？",("连续启动请求不能形成","点动必然不能启动","线圈一定断路"),"连续启动请求不能形成","连续按钮属于对应运行方式的启动支路。","连续按钮"),
    _q(39,"jog_continuous_training","检查顺序为什么要先公共条件后方式支路？",("减少把共享异常误判为单支路故障","为了进行真实送电","为了跳过模拟证据"),"减少把共享异常误判为单支路故障","从共享到局部能形成更清晰的教学证据链。","排查顺序"),
    _q(40,"jog_continuous_training","网页中的自锁异常结论能否直接指导真实跨接操作？",("不能","可以","只要设备停止就可以"),"不能","严禁据教学模拟进行真实跨接、拆线或送电。","安全边界"),
    _q(41,"diagram_symbols_roles","识读抽象控制图时，建议先判断什么？",("元件的功能角色","真实端子位置","导线实际长度"),"元件的功能角色","先辨认保护、操作、辅助和执行角色，才能理解逻辑关系。","功能角色"),
    _q(42,"diagram_symbols_roles","常闭触点的基准状态通常是？",("闭合","断开","随意变化"),"闭合","常闭触点在元件未动作的基准状态下通常闭合。","基准状态"),
    _q(43,"diagram_symbols_roles","执行元件在抽象控制链中通常位于？",("逻辑条件的下游","安全声明之外","所有保护条件之前"),"逻辑条件的下游","保护和操作条件满足后，逻辑才到达执行元件。","执行元件"),
    _q(44,"diagram_symbols_roles","本课程的抽象图可以直接作为真实接线图吗？",("不可以","可以","记住形状后可以"),"不可以","抽象图不含真实端子、电压和安装信息，仅用于逻辑学习。","安全边界"),
    _q(45,"diagram_symbols_roles","只记图形外观、不理解功能角色的主要问题是？",("难以迁移到不同控制任务","会自动提高准确率","可以替代设备说明书"),"难以迁移到不同控制任务","理解功能角色比孤立记忆外观更有助于识读不同教学图。","识图方法"),
    _q(46,"series_parallel_logic","多个条件串联在同一路径通常表示？",("需要同时满足","任选一个满足","全部可以忽略"),"需要同时满足","串联条件在教学逻辑中相当于逻辑与。","串联条件"),
    _q(47,"series_parallel_logic","并联分支通常表示？",("存在可选路径","所有路径必须同时中断","真实导线必须交叉"),"存在可选路径","并联分支在教学逻辑中常表示逻辑或。","并联分支"),
    _q(48,"series_parallel_logic","公共条件位于并联分支之前，公共条件异常会怎样？",("后续分支都不能形成完整路径","只影响一个随机分支","自动形成保持条件"),"后续分支都不能形成完整路径","分支共享上游条件，因此公共异常会影响所有后续支路。","公共条件"),
    _q(49,"series_parallel_logic","一条并联分支异常时应如何判断？",("结合当前状态检查相关分支","直接断定所有元件异常","进行真实跨接验证"),"结合当前状态检查相关分支","分支判断需要结合题设状态和模拟证据。","分支判断"),
    _q(50,"series_parallel_logic","串并联逻辑示意中的位置代表真实安装距离吗？",("不代表","完全代表","只在手机上代表"),"不代表","逻辑示意只表达条件关系，不表示真实布线与安装位置。","安全边界"),
    _q(51,"control_path_tracing","控制路径追踪的推荐起点是？",("故障现象与公共条件","直接猜测末端元件","无关方向支路"),"故障现象与公共条件","先确认现象范围和共享的上游条件，再进入相关分支。","路径起点"),
    _q(52,"control_path_tracing","只有一个方向异常且公共条件正常，下一步应检查？",("对应方向分支","另一个正常方向分支","所有真实导线"),"对应方向分支","单一方向异常应沿现象对应的局部分支追踪。","现象分支"),
    _q(53,"control_path_tracing","完整教学证据链应包含？",("对象、预期、模拟证据与判断","只有最终结论","真实送电结果"),"对象、预期、模拟证据与判断","逐步记录才能让路径和结论可复盘。","证据链"),
    _q(54,"control_path_tracing","模拟证据不足时应如何处理？",("保留不确定并复核资料","强行确定故障","拆开真实设备"),"保留不确定并复核资料","证据不足不能形成确定结论，更不能扩大到真实操作。","证据意识"),
    _q(55,"control_path_tracing","路径追踪为什么先公共后局部？",("减少无关检查并缩小范围","为了跳过安全确认","为了替代专业规程"),"减少无关检查并缩小范围","先排除共享条件，再按现象进入局部分支可形成清晰逻辑链。","排查顺序"),
    _q(56,"jog_continuous_basics","点动正常而连续运行不能启动，公共条件最可能处于什么状态？",("可能正常，应检查连续支路","必然异常","无法使用模拟资料判断"),"可能正常，应检查连续支路","点动正常说明共享公共条件具备，应进入连续运行相关支路。","现象分支"),
    _q(57,"jog_continuous_basics","区分点动与连续运行的关键依据是？",("按钮释放后是否保持","电动机外壳颜色","真实导线长度"),"按钮释放后是否保持","连续运行具有保持逻辑，点动通常随按钮释放结束。","运行特征"),
    _q(58,"jog_continuous_training","连续启动请求和自锁保持条件在抽象逻辑中常构成？",("可选的并联路径","完全无关的回路","真实跨接点"),"可选的并联路径","启动请求建立初始条件，保持分支在之后维持条件。","保持分支"),
    _q(59,"jog_continuous_training","点动异常、连续运行正常时，应优先关注？",("点动请求支路","公共停止条件","接触器线圈必然断路"),"点动请求支路","连续运行正常已说明共享条件和执行元件能够形成逻辑。","局部分支"),
    _q(60,"jog_continuous_training","模拟资料与预期状态矛盾时应如何处理？",("记录不一致并重新检查模拟资料","强行选择正常","进行真实拆线"),"记录不一致并重新检查模拟资料","教学判断也必须保持证据一致，不能猜测或扩大到真实操作。","证据意识"),
    _q(61,"star_delta_principles","星—三角启动的主要教学目的是什么？",("降低启动阶段的电流与转矩影响","提高所有负载的启动转矩","替代全部保护元件"),"降低启动阶段的电流与转矩影响","星形启动阶段会降低启动电流，同时启动转矩也会降低。","降压启动目的"),
    _q(62,"star_delta_principles","哪类启动条件更适合考虑星—三角方式？",("启动负载较轻且电动机条件符合","任何重载启动","不确认电动机条件也可以"),"启动负载较轻且电动机条件符合","启动转矩会降低，因此必须考虑负载与电动机适用条件。","适用条件"),
    _q(63,"star_delta_principles","星形阶段结束后，典型逻辑进入什么状态？",("三角运行阶段","再次回到启动请求","三个接触器同时动作"),"三角运行阶段","星形用于启动阶段，之后转换到三角运行阶段。","阶段转换"),
    _q(64,"star_delta_principles","只看到启动电流降低，能否直接断定适用？",("不能，还要考虑启动转矩和题设条件","能，适用于所有电动机","只需检查网页颜色"),"不能，还要考虑启动转矩和题设条件","电流与转矩都会变化，不能脱离负载和电动机条件判断。","适用边界"),
    _q(65,"star_delta_principles","本课程能否用于确定真实电机的接线方式？",("不能","可以直接照做","完成测验后可以"),"不能","课程只表达抽象逻辑，不提供真实端子、参数和接线条件。","安全边界"),
    _q(66,"star_delta_components","典型星—三角逻辑包含几个接触器功能角色？",("主、星形、三角三个","只有主接触器","正转与反转两个"),"主、星形、三角三个","三个角色分别承担公共、启动阶段和运行阶段功能。","元件角色"),
    _q(67,"star_delta_components","主接触器在抽象逻辑中属于什么角色？",("两个阶段共享的公共角色","只属于星形阶段","只负责时间判断"),"两个阶段共享的公共角色","主接触器作为公共角色服务于启动和运行过程。","主接触器"),
    _q(68,"star_delta_components","星形接触器主要对应哪个阶段？",("启动阶段","稳定三角运行阶段","停止后的云端阶段"),"启动阶段","星形角色用于降低启动阶段的影响。","星形接触器"),
    _q(69,"star_delta_components","三角接触器主要对应哪个阶段？",("转换后的运行阶段","最初启动阶段","保护动作阶段"),"转换后的运行阶段","三角角色在星形阶段退出后进入运行状态。","三角接触器"),
    _q(70,"star_delta_components","时间控制在本课程中的作用是？",("触发星形向三角阶段转换","替代过载保护","让两个阶段同时有效"),"触发星形向三角阶段转换","时间控制表达阶段转换条件，不承担过载保护。","时间控制"),
    _q(71,"star_delta_sequence","推荐的抽象阶段顺序是？",("启动请求→星形阶段→转换→三角阶段","三角阶段→星形阶段→启动请求","星形与三角同时开始"),"启动请求→星形阶段→转换→三角阶段","阶段追踪应保持明确的先后关系。","转换顺序"),
    _q(72,"star_delta_sequence","星形与三角互锁的核心作用是？",("阻止两个阶段同时形成动作条件","维持两个接触器同时动作","替代时间控制"),"阻止两个阶段同时形成动作条件","互锁用于约束两个阶段不能同时有效。","阶段互锁"),
    _q(73,"star_delta_sequence","转换条件满足后，首先应如何理解星形角色？",("应退出有效状态","继续与三角同时有效","自动成为保护元件"),"应退出有效状态","先退出星形阶段，之后才能进入三角运行阶段。","转换过程"),
    _q(74,"star_delta_sequence","模拟资料显示星形与三角角色同时有效时，应判断为？",("逻辑状态不符合互锁要求","正常转换状态","可以用于真实送电"),"逻辑状态不符合互锁要求","两个阶段同时有效违背互锁与阶段顺序。","互锁判断"),
    _q(75,"star_delta_sequence","学习星—三角抽象路径时，哪项做法符合安全边界？",("只依据网页模拟角色与状态判断","按抽象图连接真实端子","尝试短接互锁"),"只依据网页模拟角色与状态判断","抽象路径不能转换为真实接线或带电操作指导。","安全边界"),
    _q(76,"timer_functions","时间继电器在抽象控制逻辑中的主要角色是？",("根据输入与等待过程改变输出状态","替代全部保护元件","直接决定机械安装"),"根据输入与等待过程改变输出状态","时间继电器把时间关系加入控制条件。","时间角色"),
    _q(77,"timer_functions","计时刚开始时能否直接判断延时输出已改变？",("不能，还处于等待阶段","能，计时等于输出改变","任何情况都能"),"不能，还处于等待阶段","等待结束前，延时输出尚未达到题设状态。","等待阶段"),
    _q(78,"timer_functions","分析时间逻辑的推荐顺序是？",("输入条件→等待阶段→输出状态","输出外观→随机猜测→输入","只看最终结果"),"输入条件→等待阶段→输出状态","先后顺序是理解时间逻辑的核心。","状态顺序"),
    _q(79,"timer_functions","时间条件能否替代停止和保护条件？",("不能","可以全部替代","只有答题时可以"),"不能","时间条件与安全、保护条件承担不同角色。","角色边界"),
    _q(80,"timer_functions","本课程是否提供具体时间整定方法？",("不提供","提供现场整定值","完成测验后提供"),"不提供","课程只训练抽象状态与先后关系。","安全边界"),
    _q(81,"on_off_delay","通电延时从哪个时点开始等待？",("输入条件形成后","输入条件撤销后","输出退出后"),"输入条件形成后","通电延时在输入形成后开始延时过程。","通电延时"),
    _q(82,"on_off_delay","通电延时等待结束前，输出应如何理解？",("尚未达到延时后的状态","已经必然改变","与输入无关"),"尚未达到延时后的状态","等待阶段与输出改变必须区分。","通电延时状态"),
    _q(83,"on_off_delay","断电延时从哪个时点开始等待？",("输入条件撤销后","输入条件刚形成时","保护条件形成前"),"输入条件撤销后","断电延时的关键触发点是输入撤销。","断电延时"),
    _q(84,"on_off_delay","断电延时等待期间，输出通常如何理解？",("暂时保持原有效状态","立即退出","随机改变"),"暂时保持原有效状态","等待结束后输出才退出。","保持等待"),
    _q(85,"on_off_delay","区分两类延时最关键的依据是？",("等待由输入形成还是撤销触发","元件颜色","真实位置"),"等待由输入形成还是撤销触发","动作触发时点决定延时类型。","功能区分"),
    _q(86,"sequence_control","顺序启动的核心含义是？",("多个阶段按条件先后形成","所有角色同时形成","取消公共条件"),"多个阶段按条件先后形成","顺序控制强调前后依赖关系。","顺序启动"),
    _q(87,"sequence_control","后续阶段开始前首先应确认什么？",("公共条件与前序条件","设备外观","无关分支"),"公共条件与前序条件","后续阶段依赖共享条件和前序状态。","阶段条件"),
    _q(88,"sequence_control","公共条件异常时，多个阶段可能怎样？",("都无法形成","后续阶段自动正常","只影响外观"),"都无法形成","共享条件中断会影响依赖它的阶段。","公共条件"),
    _q(89,"sequence_control","顺序停止是否必然与启动顺序相同？",("不一定，应依据题设逻辑","必然完全相同","无需判断"),"不一定，应依据题设逻辑","停止顺序由具体教学条件决定，不能凭启动顺序猜测。","顺序停止"),
    _q(90,"sequence_control","学习顺序控制时符合安全边界的是？",("只判断网页抽象状态","据此操作真实设备","自行设定现场时间"),"只判断网页抽象状态","课程不提供真实整定、接线或操作依据。","安全边界"),
)

QUESTION_MAP = {item.id: item for item in QUESTIONS}

QUESTION_CARD_MAP = {
    **{f"q{number:02d}": "control_power" for number in range(1, 7)},
    "q07": "button_contacts", "q08": "button_contacts", "q09": "fuse",
    "q10": "thermal_relay", "q11": "contactor_coil", "q12": "button_contacts",
    "q13": "thermal_relay", "q14": "button_contacts", "q15": "button_contacts",
    "q16": "button_contacts", "q17": "control_power", "q18": "self_hold",
    "q19": "contactor_coil", "q20": "control_power", "q21": "thermal_relay",
    "q22": "button_contacts", "q23": "control_power", "q24": "forward_reverse",
    "q25": "forward_reverse", "q26": "electrical_interlock", "q27": "button_contacts",
    "q28": "contactor_coil", "q29": "forward_reverse", "q30": "electrical_interlock",
    **{f"q{number:02d}": "jog_control" for number in (31, 32, 33, 34, 35, 38, 39)},
    "q36": "self_hold", "q37": "self_hold", "q40": "self_hold",
    "q56": "jog_control", "q57": "jog_control", "q58": "self_hold",
    "q59": "jog_control", "q60": "logic_tracing",
    **{f"q{number:02d}": "diagram_symbols" for number in range(41, 46)},
    **{f"q{number:02d}": "series_logic" for number in (46, 48, 50)},
    **{f"q{number:02d}": "parallel_logic" for number in (47, 49)},
    **{f"q{number:02d}": "logic_tracing" for number in range(51, 56)},
    **{f"q{number:02d}": "star_delta_principle" for number in range(61, 66)},
    **{f"q{number:02d}": "star_delta_components" for number in range(66, 70)},
    "q70": "star_delta_timing", "q71": "star_delta_timing", "q72": "star_delta_interlock",
    "q73": "star_delta_timing", "q74": "star_delta_interlock", "q75": "star_delta_interlock",
    **{f"q{number:02d}": "timer_role" for number in range(76, 81)},
    **{f"q{number:02d}": "on_delay" for number in (81, 82)},
    **{f"q{number:02d}": "off_delay" for number in (83, 84)},
    "q85": "timer_role",
    **{f"q{number:02d}": "sequence_control" for number in range(86, 91)},
}


def card_id_for_question(question_id: str) -> str:
    return QUESTION_CARD_MAP[question_id]


def answer_feedback(question: QuizQuestion, selected_answer: str) -> str:
    if selected_answer == question.answer:
        return f"你的选择与本题考查的“{question.knowledge_point}”一致。"
    if selected_answer == "不确定":
        return f"本题已经给出足够的教学条件；对照“{question.knowledge_point}”后可以确定答案。"
    return (
        f"“{selected_answer}”没有满足题目中的关键条件。"
        f"本题应依据“{question.knowledge_point}”判断，而不是扩大到题目未提供的条件。"
    )


def similar_questions(question_id: str, limit: int = 2) -> tuple[QuizQuestion, ...]:
    question = QUESTION_MAP[question_id]
    candidates = [
        item for item in QUESTIONS
        if item.id != question_id and item.chapter_id == question.chapter_id
        and (item.knowledge_point == question.knowledge_point
             or card_id_for_question(item.id) == card_id_for_question(question_id))
    ]
    return tuple(candidates[: max(0, limit)])


def questions_for_chapter(chapter_id: str) -> tuple[QuizQuestion, ...]:
    return tuple(item for item in QUESTIONS if item.chapter_id == chapter_id)


def select_questions(chapter_id: str, count: int = 5, wrong_ids: Sequence[str] = (),
                     rng: random.Random | None = None) -> tuple[QuizQuestion, ...]:
    generator = rng or random.Random()
    available = list(questions_for_chapter(chapter_id))
    if not available:
        raise ValueError("章节没有测验题")
    preferred = [item for item in available if item.id in set(wrong_ids)]
    generator.shuffle(preferred)
    remaining = [item for item in available if item not in preferred]
    generator.shuffle(remaining)
    return tuple((preferred + remaining)[: min(count, len(available))])


def make_quiz_record(chapter_id: str, answers: Sequence[QuizAnswer], mode: str = "chapter_quiz",
                     quiz_id: str | None = None, completed_at: datetime | None = None,
                     pass_threshold: float | None = None) -> QuizRecord:
    frozen = tuple(answers)
    correct = sum(item.is_correct for item in frozen)
    total = len(frozen)
    threshold = 0.7 if mode in {"course_exam", "textbook_unit_assessment"} else (pass_threshold if pass_threshold is not None else 0.6)
    return QuizRecord(
        quiz_id=quiz_id or secrets.token_hex(12), chapter_id=chapter_id,
        completed_at=(completed_at or beijing_now()).isoformat(timespec="seconds"),
        correct_count=correct, total_count=total,
        passed=bool(total and correct / total >= threshold), mode=mode, answers=frozen,
    )


def record_to_dict(record: QuizRecord) -> dict[str, Any]:
    data = asdict(record)
    data["answers"] = [asdict(item) for item in record.answers]
    return data
