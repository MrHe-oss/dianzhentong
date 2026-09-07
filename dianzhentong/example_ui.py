"""Progressive example explanation; viewing an answer never records a grade."""
import streamlit as st


def render_example_reasoning(example, key):
    st.write(f"**题目：** {example['scenario']}")
    st.caption("先自己分析，再按需打开提示与解析；查看解析不会自动完成例题练习。")
    if st.checkbox("给我一个思考提示", key=key + "_hint"):
        st.info(example.get("thinking_hint", "先列出题目中的条件和目标，判断它们分别属于哪个知识点。"))
    if st.checkbox("查看分步解析与答案", key=key + "_solution"):
        for index, step in enumerate(example["steps"], 1):
            st.write(f"{index}. {step}")
        st.success(f"**结论：** {example['answer']}")
        for mistake in example.get("common_mistakes", []):
            st.write(f"易错提醒：{mistake}")
        if example.get("source_url"):
            st.link_button("原理参考：厂家资料", example["source_url"])

