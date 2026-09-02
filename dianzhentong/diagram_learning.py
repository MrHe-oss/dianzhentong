"""安全的抽象控制逻辑识读案例与纯规则训练引擎。"""
from __future__ import annotations
import secrets
from dataclasses import dataclass, field
from typing import Any

SAFETY_NOTICE = "仅用于抽象控制逻辑学习，不包含端子号、电压、真实导线、接线或带电操作指导。"

def _step(step_id: str, prompt: str, options: tuple[str, ...], answer: str, explanation: str) -> dict[str, Any]:
    return {"id": step_id, "prompt": prompt, "options": options, "answer": answer, "explanation": explanation}

DIAGRAM_CASES: dict[str, dict[str, Any]] = {
    "plc_hardware_roles": {"chapter_id":"p2_unit_1","title":"PLC硬件：识别系统角色","phenomenon":"一个抽象控制任务需要读取状态、执行逻辑并交换信息。","nodes":("输入信息","CPU处理","输出结果","扩展能力"),"card_ids":("plc_system_role","plc_cpu","plc_modules"),"steps":(
        _step("plc_hw_input","现场状态在信息链中属于什么？",("输入信息","CPU处理","通信结果"),"输入信息","现场状态先作为输入信息进入控制系统。"),
        _step("plc_hw_core","哪个角色负责执行用户程序？",("CPU","信号模块","外部按钮"),"CPU","CPU承担核心程序执行和系统协调。"),
        _step("plc_hw_expand","需要增加信号处理能力时关注什么？",("信号扩展模块","项目标题","程序注释"),"信号扩展模块","模块按任务需求补充系统能力。"))},
    "plc_scan_cycle": {"chapter_id":"p2_unit_2","title":"PLC程序：排列扫描逻辑","phenomenon":"模拟输入已经变化，需要判断程序循环中信息如何形成新结果。","nodes":("读取输入","执行程序","更新结果","下一循环"),"card_ids":("plc_program_cycle","plc_variables","plc_logic_structure"),"steps":(
        _step("plc_cycle_read","程序处理前先取得什么？",("当前输入信息","下一轮结果","真实端子位置"),"当前输入信息","当前输入是本轮逻辑处理的基础。"),
        _step("plc_cycle_process","取得输入后进入哪个环节？",("执行用户程序","直接结束循环","修改真实设备"),"执行用户程序","程序根据输入和内部状态计算逻辑结果。"),
        _step("plc_cycle_update","程序执行后应形成什么？",("本轮输出结果","新的设备型号","接线步骤"),"本轮输出结果","处理结果更新后进入下一次循环。"))},
    "plc_tia_objects": {"chapter_id":"p2_unit_3","title":"TIA博途：匹配工程对象","phenomenon":"离线教学工程包含控制器描述、控制逻辑和命名变量。","nodes":("工程项目","设备组态","程序块","变量表"),"card_ids":("tia_project","tia_device_config","tia_program_blocks"),"steps":(
        _step("plc_tia_container","统一组织全部工程对象的是？",("工程项目","程序块","变量表"),"工程项目","项目提供设备与程序信息的组织边界。"),
        _step("plc_tia_device","控制器和模块构成归入什么对象？",("设备组态","变量表","项目标题"),"设备组态","组态用于描述工程中的控制器和模块构成。"),
        _step("plc_tia_logic","控制逻辑主要由什么承载？",("程序块","设备外观","学习记录"),"程序块","程序块承载控制逻辑，变量表集中管理变量定义。"))},
    "plc_project_check": {"chapter_id":"p2_unit_4","title":"PLC项目：建立检查闭环","phenomenon":"一个离线项目已经写出逻辑，但变量含义不清，也尚未检查工程信息。","nodes":("需求分析","变量与工程","编译检查","模拟复盘"),"card_ids":("plc_project_flow","plc_compile_check","plc_monitoring_boundary"),"steps":(
        _step("plc_project_start","首先应回到哪个环节？",("需求与控制目标","真实设备送电","随机增加指令"),"需求与控制目标","需求决定变量、逻辑和验证目标。"),
        _step("plc_project_compile","定义清楚后应完成什么检查？",("工程一致性与编译检查","真实跨接验证","只检查窗口颜色"),"工程一致性与编译检查","先处理结构、引用、类型和警告等工程信息。"),
        _step("plc_project_validate","编译通过后还需要什么？",("离线模拟逻辑复盘","直接证明现场安全","强制真实变量"),"离线模拟逻辑复盘","编译通过不等于需求正确，仍需离线验证与安全复盘。"))},
    "dol_roles": {"chapter_id":"diagram_symbols_roles","title":"直接启动：识别元件角色","phenomenon":"按下启动按钮后，模拟执行元件没有形成动作条件。","nodes":("保护条件","停止条件","启动请求","执行元件"),"card_ids":("diagram_symbols","button_contacts","contactor_coil"),"steps":(
        _step("dol_roles_scope","第一步应先识别哪类上游角色？",("保护条件","执行元件","无关分支"),"保护条件","保护条件位于公共路径上游。"),
        _step("dol_roles_signal","保护条件正常后，哪个角色表达启动意图？",("启动请求","停止条件","执行元件"),"启动请求","启动按钮的抽象角色是提供启动请求。"),
        _step("dol_roles_end","逻辑链末端应关注哪个角色？",("执行元件","保护条件","启动请求"),"执行元件","前序条件满足后才判断执行元件。"))},
    "jog_roles": {"chapter_id":"diagram_symbols_roles","title":"点动与连续：区分共享角色","phenomenon":"点动和连续运行两种方式均不能形成模拟动作条件。","nodes":("公共条件","方式选择","保持分支","执行元件"),"card_ids":("diagram_symbols","jog_control"),"steps":(
        _step("jog_roles_scope","两种方式共同异常时先看哪一类？",("公共条件","只看点动分支","只看保持分支"),"公共条件","共同异常优先指向共享的上游条件。"),
        _step("jog_roles_branch","公共条件正常后，区分运行方式需要观察什么？",("方式选择","真实导线长度","设备安装位置"),"方式选择","点动与连续使用不同的请求或保持逻辑。"),
        _step("jog_roles_end","两个方式最后共同到达哪类角色？",("执行元件","保持分支","方式按钮"),"执行元件","不同方式最终共享同一抽象执行角色。"))},
    "dol_series": {"chapter_id":"series_parallel_logic","title":"直接启动：追踪串联中断","phenomenon":"模拟资料显示公共电源正常，但保护触点条件未满足。","nodes":("控制电源","保护触点","停止条件","启动请求","执行元件"),"card_ids":("series_logic","thermal_relay"),"steps":(
        _step("dol_series_start","控制电源正常后沿串联路径检查哪里？",("保护触点","直接跳到执行元件","并联保持分支"),"保护触点","串联路径应按上游到下游逐项确认。"),
        _step("dol_series_state","保护触点条件未满足时，路径状态是？",("在此中断","仍然完整","自动转入其他分支"),"在此中断","串联条件任一不满足都会阻断后续逻辑。"),
        _step("dol_series_result","此时是否应继续确定启动按钮故障？",("不应，当前证据已定位上游中断","应直接确定","应真实送电验证"),"不应，当前证据已定位上游中断","无需越过已确认的上游中断猜测下游故障。"))},
    "hold_parallel": {"chapter_id":"series_parallel_logic","title":"连续运行：理解保持分支","phenomenon":"启动请求能够短暂形成，但请求消失后模拟运行条件不能维持。","nodes":("公共条件","启动请求","保持分支","执行元件"),"card_ids":("parallel_logic","self_hold"),"steps":(
        _step("hold_parallel_scope","短暂启动说明哪部分曾经满足？",("公共条件与启动请求","保持分支一定正常","执行元件一定损坏"),"公共条件与启动请求","能够短暂形成说明初始启动路径曾有效。"),
        _step("hold_parallel_branch","请求消失后应由哪条可选路径维持？",("保持分支","停止条件","无关方式分支"),"保持分支","连续运行依靠并联的保持条件延续逻辑。"),
        _step("hold_parallel_break","不能维持时最相关的逻辑中断点是？",("保持分支","公共电源必然缺失","点动按钮"),"保持分支","现象直接对应保持路径不能形成。"))},
    "reverse_common": {"chapter_id":"control_path_tracing","title":"正反转：追踪公共路径","phenomenon":"正转和反转两个方向均不能形成模拟启动条件。","nodes":("公共条件","方向选择","互锁条件","方向执行元件"),"card_ids":("logic_tracing","forward_reverse"),"steps":(
        _step("reverse_common_scope","两个方向共同异常，先选择哪条范围？",("公共路径","只选正转分支","只选反转分支"),"公共路径","两个方向共享公共条件。"),
        _step("reverse_common_order","公共路径中应采用什么顺序？",("从上游条件逐项向下游","从结果随机猜测","先检查无关方向"),"从上游条件逐项向下游","顺序追踪能减少无依据结论。"),
        _step("reverse_common_break","公共条件已显示异常，下一步结论应是？",("公共路径在该条件中断","两个方向线圈都损坏","继续检查方向按钮"),"公共路径在该条件中断","当前证据已解释两个方向共同异常。"))},
    "reverse_branch": {"chapter_id":"control_path_tracing","title":"正反转：进入相关方向分支","phenomenon":"公共条件正常，反转可以形成条件，但正转不能形成启动条件。","nodes":("公共条件","正转分支","正转互锁","正转执行元件"),"card_ids":("logic_tracing","electrical_interlock"),"steps":(
        _step("reverse_branch_scope","根据现象应进入哪个局部分支？",("正转分支","反转分支","所有公共条件"),"正转分支","单一方向异常应进入对应方向分支。"),
        _step("reverse_branch_order","正转请求正常后应检查哪个逻辑条件？",("正转互锁条件","反转执行元件","云端记录"),"正转互锁条件","方向请求后应沿对应互锁条件继续追踪。"),
        _step("reverse_branch_break","互锁条件模拟状态异常时，中断点在哪里？",("正转互锁条件","公共电源","反转按钮"),"正转互锁条件","模拟证据把中断点限定在正转分支的互锁条件。"))},
    "sd_purpose": {"chapter_id":"star_delta_principles","title":"星—三角：理解降压启动目的","phenomenon":"题设要求减小启动阶段对供电条件和机械负载的影响。","nodes":("启动请求","星形启动阶段","降低启动影响","三角运行阶段"),"card_ids":("star_delta_principle",),"steps":(
        _step("sd_purpose_scope","应先判断题设关注哪个阶段？",("启动阶段","稳定运行阶段","停止阶段"),"启动阶段","星—三角方式首先解决启动阶段的影响。"),
        _step("sd_purpose_effect","星形启动阶段的抽象作用是？",("降低启动电流与启动转矩","提高启动转矩且不改变电流","让两个阶段同时有效"),"降低启动电流与启动转矩","降压启动会同时降低启动电流与启动转矩。"),
        _step("sd_purpose_end","启动阶段结束后进入哪个角色阶段？",("三角运行阶段","继续保持星形阶段","跳过运行阶段"),"三角运行阶段","满足转换条件后进入三角运行阶段。"))},
    "sd_suitability": {"chapter_id":"star_delta_principles","title":"星—三角：判断适用边界","phenomenon":"题设中的负载允许较低启动转矩，电动机也满足三角运行前提。","nodes":("题设条件","启动负载特征","星形启动阶段","三角运行阶段"),"card_ids":("star_delta_principle",),"steps":(
        _step("sd_suitability_common","判断适用性时先确认什么？",("题设给出的运行前提","接触器外观","元件摆放顺序"),"题设给出的运行前提","适用性必须由题设条件支持，不能仅凭名称判断。"),
        _step("sd_suitability_load","哪种抽象负载条件更符合本课程情境？",("允许较低启动转矩","必须获得最大启动转矩","负载条件未知也直接采用"),"允许较低启动转矩","星形阶段的启动转矩较低，需要题设允许。"),
        _step("sd_suitability_result","条件满足时，正确的阶段关系是？",("先星形启动再三角运行","全程只用星形阶段","两个阶段同时有效"),"先星形启动再三角运行","课程中的标准路径是先启动阶段后运行阶段。"))},
    "sd_roles": {"chapter_id":"star_delta_components","title":"星—三角：区分三个接触器角色","phenomenon":"模拟逻辑需要识别公共、启动和运行三个角色。","nodes":("公共条件","主接触器","星形接触器","三角接触器"),"card_ids":("star_delta_components",),"steps":(
        _step("sd_roles_common","哪个角色服务于两个阶段的公共路径？",("主接触器","星形接触器","三角接触器"),"主接触器","主接触器表达星形与三角阶段共享的公共运行条件。"),
        _step("sd_roles_start","启动阶段对应哪个角色？",("星形接触器","三角接触器","停止条件"),"星形接触器","星形接触器只服务于启动阶段。"),
        _step("sd_roles_run","转换完成后的运行阶段对应哪个角色？",("三角接触器","星形接触器","时间控制"),"三角接触器","三角接触器服务于转换后的稳定运行阶段。"))},
    "sd_timer": {"chapter_id":"star_delta_components","title":"星—三角：理解时间控制","phenomenon":"星形启动阶段已经形成，模拟时间条件随后到达转换状态。","nodes":("启动请求","星形阶段","时间条件","三角阶段"),"card_ids":("star_delta_timing","star_delta_components"),"steps":(
        _step("sd_timer_stage","时间条件到达前，当前有效阶段是？",("星形启动阶段","三角运行阶段","两个阶段"),"星形启动阶段","转换前保持星形启动角色。"),
        _step("sd_timer_action","时间条件在抽象逻辑中的作用是？",("触发阶段转换","替代保护条件","保持两个阶段同时有效"),"触发阶段转换","时间条件用于触发星形退出并准备三角阶段。"),
        _step("sd_timer_result","转换后应形成哪个阶段？",("三角运行阶段","继续星形启动阶段","停止所有公共条件"),"三角运行阶段","标准顺序在转换后进入三角运行阶段。"))},
    "sd_sequence": {"chapter_id":"star_delta_sequence","title":"星—三角：追踪完整转换顺序","phenomenon":"启动请求有效，模拟逻辑需要按阶段完成从启动到运行的转换。","nodes":("启动请求","主与星形角色","星形退出","主与三角角色"),"card_ids":("star_delta_timing","star_delta_interlock"),"steps":(
        _step("sd_sequence_start","启动请求后首先形成哪组抽象角色？",("主接触器与星形接触器","主接触器与三角接触器","星形与三角接触器"),"主接触器与星形接触器","启动阶段由公共主角色和星形角色共同形成。"),
        _step("sd_sequence_transition","转换时首先需要怎样处理星形角色？",("先退出星形角色","保持星形并加入三角","跳过转换条件"),"先退出星形角色","阶段转换必须先结束星形角色，避免相互冲突。"),
        _step("sd_sequence_run","随后进入哪组运行角色？",("主接触器与三角接触器","主接触器与星形接触器","仅时间控制"),"主接触器与三角接触器","运行阶段保留公共主角色并启用三角角色。"))},
    "sd_interlock": {"chapter_id":"star_delta_sequence","title":"星—三角：排除阶段同时动作","phenomenon":"模拟资料要求星形与三角两个阶段不能同时形成动作条件。","nodes":("公共条件","当前阶段","互锁约束","允许角色"),"card_ids":("star_delta_interlock","star_delta_components"),"steps":(
        _step("sd_interlock_scope","互锁约束主要作用于哪两个角色？",("星形与三角接触器","主接触器与启动请求","保护条件与时间条件"),"星形与三角接触器","阶段互锁防止星形和三角角色同时有效。"),
        _step("sd_interlock_state","星形阶段仍有效时，三角角色应处于什么逻辑状态？",("被互锁阻止","同时有效","不受限制"),"被互锁阻止","星形有效时必须阻止三角角色形成。"),
        _step("sd_interlock_result","准备进入三角阶段前，哪项条件必须先满足？",("星形角色已经退出","星形角色继续保持","两个角色同时收到请求"),"星形角色已经退出","先退出星形角色，再允许三角角色进入。"))},
    "timer_role_path": {"chapter_id":"timer_functions","title":"时间继电器：识别输入、等待与输出","phenomenon":"模拟输入条件已经形成，输出角色需要等待后再改变。","nodes":("输入条件","计时开始","等待阶段","输出改变"),"card_ids":("timer_role","on_delay"),"steps":(
        _step("timer_role_input","时间继电器首先响应哪类信息？",("输入条件","输出结果","无关分支"),"输入条件","输入条件触发计时逻辑。"),
        _step("timer_role_wait","输入形成后、输出改变前处于什么阶段？",("等待阶段","输出已经改变","计时已复位"),"等待阶段","时间继电器用等待阶段区分输入与输出动作时点。"),
        _step("timer_role_output","等待条件到达后应关注什么？",("输出角色改变","输入自动消失","两个输出同时动作"),"输出角色改变","达到设定的抽象时间条件后，输出状态才改变。"))},
    "timer_reset_path": {"chapter_id":"timer_functions","title":"时间继电器：输入提前消失","phenomenon":"模拟输入在等待完成前消失，输出条件尚未形成。","nodes":("输入形成","等待进行","输入提前消失","计时复位"),"card_ids":("timer_role","on_delay"),"steps":(
        _step("timer_reset_start","输入形成后首先发生什么？",("开始等待","立即确定输出故障","跳过计时"),"开始等待","通电延时逻辑先进入等待。"),
        _step("timer_reset_break","等待完成前输入消失，当前过程怎样变化？",("计时复位","输出仍必然动作","进入断电延时"),"计时复位","输入未持续到等待条件完成，通电延时过程复位。"),
        _step("timer_reset_result","此时输出角色的合理状态是？",("保持原状态","已经完成延时动作","状态无法由题设判断"),"保持原状态","等待尚未完成，输出不应被判为已改变。"))},
    "on_delay_trace": {"chapter_id":"on_off_delay","title":"通电延时：追踪动作时点","phenomenon":"模拟输入形成后进入等待，条件到达时输出才改变。","nodes":("输入形成","开始计时","等待完成","输出改变"),"card_ids":("on_delay","timer_role"),"steps":(
        _step("on_delay_trigger","通电延时的计时由什么触发？",("输入条件形成","输入条件消失","输出先改变"),"输入条件形成","通电延时从输入形成开始计时。"),
        _step("on_delay_wait","等待期间输出应怎样理解？",("尚未发生延时改变","已经完成动作","与输入无关"),"尚未发生延时改变","输出需要等到延时条件满足。"),
        _step("on_delay_finish","等待完成后发生什么？",("输出状态改变","计时回到初始且输出不变","输入必然消失"),"输出状态改变","延时条件到达后输出执行预期改变。"))},
    "off_delay_trace": {"chapter_id":"on_off_delay","title":"断电延时：追踪退出时点","phenomenon":"模拟输入消失后，输出暂时保持，等待完成后才退出。","nodes":("输入消失","输出保持","延时等待","输出退出"),"card_ids":("off_delay","timer_role"),"steps":(
        _step("off_delay_trigger","断电延时的等待从何时开始？",("输入条件消失","输入条件形成","输出退出之后"),"输入条件消失","断电延时由输入撤除触发。"),
        _step("off_delay_hold","等待期间输出处于什么抽象状态？",("暂时保持原有效状态","立即退出","随机变化"),"暂时保持原有效状态","断电延时的特点是输入消失后输出延后退出。"),
        _step("off_delay_finish","等待完成后输出怎样变化？",("退出原有效状态","重新触发输入","继续永久保持"),"退出原有效状态","延时完成后输出结束保持。"))},
    "sequence_start_path": {"chapter_id":"sequence_control","title":"顺序控制：后续阶段进入","phenomenon":"公共条件与第一阶段已形成，后续阶段需等待顺序条件。","nodes":("公共条件","第一阶段","顺序条件","后续阶段"),"card_ids":("sequence_control","on_delay"),"steps":(
        _step("sequence_start_common","顺序分析应先确认什么？",("公共条件","最后阶段","无关外观"),"公共条件","共享的前置条件应最先确认。"),
        _step("sequence_start_first","公共条件正常后哪个阶段先形成？",("第一阶段","所有阶段同时","后续阶段"),"第一阶段","顺序逻辑要求先建立前一阶段。"),
        _step("sequence_start_next","后续阶段何时允许进入？",("顺序条件满足后","第一阶段之前","任意时刻"),"顺序条件满足后","只有前序和等待条件满足，后续阶段才被允许。"))},
    "sequence_stop_path": {"chapter_id":"sequence_control","title":"顺序控制：按条件退出","phenomenon":"模拟停止请求形成，各阶段需要按给定逻辑有序退出。","nodes":("公共条件","停止请求","退出条件","阶段结束"),"card_ids":("sequence_control","off_delay"),"steps":(
        _step("sequence_stop_request","停止分析首先识别什么？",("停止请求","新启动请求","无关分支"),"停止请求","题设的状态变化由停止请求开始。"),
        _step("sequence_stop_order","多个阶段退出时应依据什么？",("题设给出的顺序条件","随意选择","让所有阶段永久保持"),"题设给出的顺序条件","退出顺序必须由已有逻辑条件确定。"),
        _step("sequence_stop_finish","退出条件到达后应得到什么结论？",("对应阶段结束","后续阶段自动重新启动","所有输入都异常"),"对应阶段结束","达到退出条件后，相关阶段结束其有效状态。"))},
}

@dataclass
class DiagramTrainingSession:
    case_id: str
    training_id: str = field(default_factory=lambda: secrets.token_hex(12))
    index: int = 0
    first_answers: dict[str, str] = field(default_factory=dict)
    wrong_steps: list[str] = field(default_factory=list)
    step_solved: bool = False
    @property
    def case(self) -> dict[str, Any]: return DIAGRAM_CASES[self.case_id]
    @property
    def is_complete(self) -> bool: return self.index >= len(self.case["steps"])
    @property
    def current_step(self) -> dict[str, Any] | None: return None if self.is_complete else self.case["steps"][self.index]
    @property
    def correct_steps(self) -> int: return len(self.case["steps"]) - len(self.wrong_steps)
    def answer(self, selected: str) -> bool:
        step = self.current_step
        if step is None: raise ValueError("识图训练已经完成")
        if selected not in step["options"]: raise ValueError("答案不属于当前步骤选项")
        if step["id"] not in self.first_answers:
            self.first_answers[step["id"]] = selected
            if selected != step["answer"]: self.wrong_steps.append(step["id"])
        self.step_solved = selected == step["answer"]
        return self.step_solved
    def next_step(self) -> None:
        if not self.step_solved: raise ValueError("请先完成当前步骤")
        self.index += 1; self.step_solved = False
    def to_dict(self) -> dict[str, Any]:
        return {"case_id":self.case_id,"training_id":self.training_id,"index":self.index,"first_answers":dict(self.first_answers),"wrong_steps":list(self.wrong_steps),"step_solved":self.step_solved}
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagramTrainingSession":
        if data.get("case_id") not in DIAGRAM_CASES: raise ValueError("未知识图案例")
        return cls(data["case_id"],str(data["training_id"]),int(data["index"]),dict(data.get("first_answers",{})),list(data.get("wrong_steps",[])),bool(data.get("step_solved",False)))

def cases_for_chapter(chapter_id: str) -> tuple[dict[str, Any], ...]:
    return tuple({"id":case_id,**case} for case_id,case in DIAGRAM_CASES.items() if case["chapter_id"] == chapter_id)

def diagram_lesson_for_chapter(chapter_id: str) -> dict[str, object] | None:
    cases = cases_for_chapter(chapter_id)
    return None if not cases else {"title":"从功能角色到完整控制路径","flows":tuple(case["nodes"] for case in cases)}

def validate_diagram_cases() -> None:
    for case_id,case in DIAGRAM_CASES.items():
        ids=[step["id"] for step in case["steps"]]
        if not ids or len(ids)!=len(set(ids)): raise ValueError(f"识图案例步骤无效：{case_id}")
        for step in case["steps"]:
            if step["answer"] not in step["options"] or len(step["options"]) not in {2,3}: raise ValueError(f"识图案例选项无效：{case_id}")
validate_diagram_cases()
