"""无题库依赖的共用星—三角教学阶段；不描述真实设备操作。"""
STAR_DELTA_STAGES: tuple[dict[str, object], ...] = (
    {
        "id": "stopped", "title": "停止",
        "description": "启动请求尚未形成，三个接触器角色均不应有效。",
        "roles": ("主接触器：未形成", "星形接触器：未形成", "三角接触器：未形成"),
        "next_condition": "收到教学情境中的启动请求",
    },
    {
        "id": "star_start", "title": "星形启动",
        "description": "公共主角色与星形角色有效，用较低启动电流和启动转矩完成启动阶段。",
        "roles": ("主接触器：有效", "星形接触器：有效", "三角接触器：被互锁阻止"),
        "next_condition": "题设中的时间转换条件到达",
    },
    {
        "id": "transition", "title": "转换等待",
        "description": "星形角色已经退出，三角角色尚未进入，避免两个阶段重叠。",
        "roles": ("主接触器：保持公共条件", "星形接触器：已退出", "三角接触器：等待允许"),
        "next_condition": "星形退出且互锁条件允许",
    },
    {
        "id": "delta_run", "title": "三角运行",
        "description": "公共主角色与三角角色有效，进入题设中的稳定运行阶段。",
        "roles": ("主接触器：有效", "星形接触器：被互锁阻止", "三角接触器：有效"),
        "next_condition": "停止请求或公共条件改变",
    },
)


def stage_by_id(stage_id: str) -> dict[str, object]:
    return next(item for item in STAR_DELTA_STAGES if item["id"] == stage_id)


def role_is_active(role: str) -> bool:
    """依据共用角色描述高亮，不新增控制规则。"""
    return role.endswith(('：有效', '：保持公共条件'))
