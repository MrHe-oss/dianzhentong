from pathlib import Path

from dianzhentong.textbook_examples import LOGIC_FORMULAS, UNIT_EXAMPLES, example_for_unit, formulas_for_topic


def test_formulas_have_symbols_and_are_only_added_where_meaningful():
    assert 3 <= len(LOGIC_FORMULAS) < 18
    for topic_id, formulas in LOGIC_FORMULAS.items():
        assert formulas_for_topic(topic_id) == formulas
        for formula in formulas:
            assert formula["expression"] and formula["symbols"] and formula["meaning"]


def test_each_unit_has_original_worked_example_and_variant():
    assert set(UNIT_EXAMPLES) == set(range(7))
    for index in range(7):
        example = example_for_unit(index)
        assert len(example["steps"]) >= 3
        assert example["practice_answer"] in example["options"]


def test_v37_ui_labels_original_material_and_formula_boundaries():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.5"' in config and 'UI_STATE_VERSION = "4.5"' in app
    for phrase in ("抽象逻辑公式", "原创例题与分步解析", "变式练习", "不是教材原题或官方答案"):
        assert phrase in app
    assert "公式表达控制逻辑关系，不代表真实接线方式" in app
