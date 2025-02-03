import os
import streamlit as st
import yaml
import json
# from prompts import *
import os
from streamlit_scroll_to_top import scroll_to_here
import openai
import requests

os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]

scenario_instruction = '''**Task for Experts**

Your task is to review and evaluate each **scenario** generated using the provided prompt. For each scenario, you need to:

1. **Evaluate the Scenario’s Realism**:
   - Assess whether the scenario is realistic and plausible in an actual laboratory setting.
   - Ensure the scenario provides sufficient detail about the laboratory environment, equipment, substances, their storage conditions, and placement to align with the question.

2. **Ensure Accurate and Informed Judgments**:
   - Verify all details for accuracy and relevance.
   - For any uncertainties, consult reliable resources to provide a confident and well-informed judgment.
   - **If previous expert's Comment is provided, you MUST carefully review and incorporate that feedback into your evaluation.**

---

**For Each Scenario, Choose One of the Following Options**:

1. **Conform**:
   - Select this option if the scenario is realistic, meaningful, and aligns appropriately with the laboratory setting described in the question.

2. **Delete**:
   - Select this option if the scenario:
     - Is illogical or nonsensical
     - **Is overly similar to a previously presented scenario**
     - Lacks essential details or context to make it plausible
     - Contains inherent contradictions or inconsistencies
     - **If you remain uncertain after consulting relevant resources**

3. **Modify**:
   - Select this option if the scenario requires refinement. Specifically, you must:
     - Provide the revised **Scenario** in the input box
     - Ensure your language is formal and professional
     - **Explicitly address any issues raised in previous expert's Comment (if provided)**
     - Use GPT-4o API for linguistic refinement while maintaining professional accuracy
     - Never rely solely on GPT for specialized domain knowledge validation

### Critical Note: 
The "Comment" option has been removed. When encountering uncertainties even after consulting resources, you must choose "Delete" instead of providing open-ended comments. Any existing Comments from previous experts should be treated as binding feedback that must be resolved through either Modification or Deletion.'''


issues_instruction = '''**Task for Experts**

Your task is to review and evaluate the **lab-safety-related issues** identified for each scenario. For every issue, you need to:

1. **Assess Quality and Alignment**:
   - Determine if each issue is accurate and appropriately aligned with the described scenario.
   - Ensure issues are categorized correctly and belong only to the specified category.
   - **If previous expert's Comment exists, you MUST prioritize addressing the concerns raised in that feedback.**

2. **Avoid Duplication**:
   - Check for repeated or overly similar issues within the same category. If duplicates exist, remove the narrower or less comprehensive issue.

3. **Ensure Clarity and Specificity**:
   - Confirm that each issue is clear, specific, and directly related to the scenario.
   - Avoid vague or non-specific issues.

4. **Provide Comprehensive Feedback**:
   - For each scenario, evaluate if any significant lab-safety-related issues are missing within each category. If any points are missing, add them in the **Add Missing Points** section.

---

**For Each Identified Issue, Choose One of the Following Options**:

1. **Correct**:
   - Select this option if the identified lab-safety issue is accurate, relevant to the scenario, and correctly categorized.

2. **Delete**:
   - Select this option if the issue:
     - Is a duplicate or overly similar to another issue within the same category
     - Does not belong to the specified category
     - Is unrelated to the scenario
     - Is vague or non-specific
     - **If you remain uncertain after consulting relevant resources**

3. **Modify**:
   - Select this option if the issue requires refinement. Specifically, you must:
     - Provide the revised **Issue** in the input box
     - Ensure your language is formal and professional
     - **Explicitly resolve any concerns stated in previous expert's Comment (if provided)**
     - Use GPT-4o API for linguistic refinement while maintaining technical accuracy
     - Never rely solely on GPT for specialized lab-safety knowledge validation
     
 ---

**Additional Input Box: Add Missing Points**  
- For each category, assess if there are any significant lab-safety issues missing.  
- Add these missing points in the **Add Missing Points** input box. Use clear, concise, and professional language. You need to refine your inputs using the GPT-4o API.

### Critical Difference:
- The "Comment" option has been permanently removed
- All uncertainties after resource consultation must result in "Delete"
- Previous expert's Comments are binding and must be fully addressed through Modification or Deletion
- Missing points additions must align with unresolved issues from prior Comments (if applicable)
'''


decision_instruction = '''**Task for Experts**

Your task is to review and evaluate each **decision** and its corresponding **consequence** generated using the provided prompt. For each decision, you need to:

1. **Evaluate the Decision's and the Consequence's Validity**:
   - Assess whether the decision is meaningful and relevant within the context of laboratory safety.
   - Determine if the decision logically leads to the stated consequence. Ensure they are aligned and coherent.
   - **If previous expert's Comment exists, you MUST prioritize resolving the issues raised in that feedback.**

2. **Ensure Accurate and Informed Judgments**:
   - Consult relevant resources for any uncertainties to ensure your assessments are accurate and thorough.
   - Provide clear and confident conclusions.
   - **All unresolved uncertainties after consultation must result in deletion.**

---

**For Each Decision, Choose One of the Following Options**:

1. **Correct**:
   - Select this option if the decision is meaningful, relevant, and directly leads to the stated consequence as described.

2. **Delete**:
   - Choose this if the decision:
     - Is illogical, nonsensical, or irrelevant to the scenario
     - Is similar to or duplicates another decision
     - **If uncertainty persists after resource consultation**

3. **Modify**:
   - Use this option if you believe the decision or consequence requires refinement:
     - Provide revised **Decision** in the first input box
     - Provide revised **Consequence** in the second input box
     - **Explicitly address all concerns from previous expert's Comment (if provided)**
     - Maintain causal relationship between decision and consequence
     - Use GPT-4o API only for language polishing, not domain validation
     - Never leave partially modified content (clear empty boxes if only modifying one element)

### Critical Implementation Notes:
- The "Comment" option is permanently disabled
- All ambiguous cases after verification must be deleted
- Prior expert's Comments constitute binding directives that require full resolution
'''


class AnnotationApp:
    def __init__(self):
        self.config = self.load_config()
        self.session_state_initialization()

    ############## 新增的通用小函数 ##############
    def ensure_session_state_key(self, key: str, default_value):
        """
        确保 st.session_state[key] 存在，不存在则初始化为 default_value
        """
        if key not in st.session_state:
            st.session_state[key] = default_value

    def update_and_save(self, data: list, data_index: int, prop: str, value, filepath: str):
        """
        更新 data[data_index][prop] 的值并执行保存
        """
        data[data_index][prop] = value
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)
    ############################################

    def session_state_initialization(self):
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0
        if 'data' not in st.session_state:
            st.session_state.data = []
        # if 'selected_keys' not in st.session_state:
        #     st.session_state.selected_keys = []
        if 'annotation_filepath' not in st.session_state:
            st.session_state.annotation_filepath = ""
        if 'dataset_name' not in st.session_state:
            st.session_state.dataset_name = ""

    def load_css(self):
        css_path = "src/annotation/annotation.css"
        if os.path.exists(css_path):
            with open(css_path) as css_file:
                css_content = css_file.read()
                st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

    def load_config(self):
        with open("src/config/annotation_config_2.yaml", "r") as file:
            config = yaml.safe_load(file)
        return config

    def load_data_file(self, uploaded_file):
        dataset_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
        annotation_filename = f"{dataset_name}_annotation.json"
        annotation_filepath = os.path.join('data', dataset_name, annotation_filename)
        os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)

        if os.path.exists(annotation_filepath):
            with open(annotation_filepath, "r") as file:
                data = json.load(file)
                st.success(f"Loaded annotation file: {annotation_filename}")
        else:
            data = json.load(uploaded_file)
            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]
            with open(annotation_filepath, "w") as file:
                json.dump(data, file, indent=4)
            st.success(f"Created new annotation file: {annotation_filename}")

        return data, annotation_filepath, dataset_name

    def save_annotations(self, data, filepath):
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

    def on_index_change(self):
        st.session_state.current_index = st.session_state.item_index

    def go_previous(self):
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1

    def go_next(self):
        if st.session_state.current_index < len(st.session_state.data) - 1:
            st.session_state.current_index += 1

    # Create a downloadable version of the file
    def provide_download(self, data, filename="new_QA_annotation.json"):
        json_data = json.dumps(data, indent=4)  # Convert data to JSON string
        if st.sidebar.download_button(
            label="Download JSON File",
            data=json_data,
            file_name=filename,
            mime="application/json"
        ):
            local_path = st.session_state.annotation_filepath  # 假设这里是你保存的 JSON 文件路径
            remote_filename = 'LabSafety/' + os.path.basename(local_path)
            self.upload_to_jianguoyun(json_data, remote_filename)

    def upload_to_jianguoyun(self, json_data, remote_filename: str):
        username = st.secrets["nutcloud"]["username"]
        password = st.secrets["nutcloud"]["password"]


        url = f"https://dav.jianguoyun.com/dav/{remote_filename}"
        res = requests.put(url, data=json_data, auth=(username, password))
        if res.status_code in [200, 201, 204]:
            st.success(f"Successfully saved to Jianguoyun: {remote_filename}")
            st.sidebar.write("**Successfully saved!**")
        else:
            st.error(f"Failed Upload: {res.status_code}, {res.text}")

    def call_gpt_api(self, user_input: str, system_prompt='Refine the content:') -> str:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model='gpt-4o-2024-11-20',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        ).choices[0].message.content
        return response

    def gpt_input(self, key, system_prompt='Refine the sentences. Please only output the refined content.'):
        st.markdown("---")


        if system_prompt == 'Refine the sentences. Please only output the refined content.':
            st.markdown('**GPT-4o API (Sentence Refiner)**')
            user_input = st.text_area(f"Please enter the content you need to refine. (System Prompt: {system_prompt})",
                                      key=key,
                                      )

        else:
            st.markdown('**GPT-4o API (Any Requests Here!)**')
            user_input = st.text_area(f"Please enter any task you want GPT to complete. (System Prompt: {system_prompt})",
                                      key=key,
                                      )


        if st.button("Submit", key=key+'_botton'):  # 点击后执行以下操作
            if user_input:
                with st.spinner("GPT generating..."):
                    answer = self.call_gpt_api(user_input, system_prompt)
                st.markdown("**The response of GPT：**")
                st.write(answer)
            else:
                st.warning("To use GPT, please enter the content and then click Submit.")
        st.markdown("---")

    def display_annotation_interface(self, data, current_index, show_image=False):
        item = data[current_index]

        scenario_cfg = self.config.get('Scenario', {})
        q1_cfg = self.config.get('question1', {})
        q2_cfg = self.config.get('question2', {})
        edit_options = ['Modify']

        # -------------------- Scenario Reality --------------------
        st.markdown(f"### {scenario_cfg.get('label', 'Scenario')}")
        st.markdown(scenario_instruction)
        if st.session_state.scroll_to_header:
            scroll_to_here(0,
                           key='header')  # Scroll to the top of the page, 0 means instantly, but you can add a delay (im milliseconds)
            st.session_state.scroll_to_header = False  # Reset the state after scrolling
        st.markdown("---")
        st.markdown('#### Scenario')
        scenario_desc = item.get('Scenario', 'No scenario description available.')
        st.write(scenario_desc)
        scenario_options = scenario_cfg.get('options', [])

        scenario_key = f"Scenario_radio_{current_index}"
        scenario_mod_key = f"Scenario_mod_{current_index}"
        # scenario_comment_key = f"Scenario_comment_{current_index}"

        # session_state 初始化
        self.ensure_session_state_key(scenario_key, item.get('Scenario_judge', ""))
        self.ensure_session_state_key(scenario_mod_key, item.get('Scenario_modified', ""))
        # self.ensure_session_state_key(scenario_comment_key, item.get('Scenario_comment', ""))

        # 如果当前值不在可选项中，重置为第一项
        if st.session_state[scenario_key] not in scenario_options:
            st.session_state[scenario_key] = scenario_options[0] if scenario_options else ""

        if data[current_index].get('Scenario_comment', ""):
            st.write("**Comments**:", data[current_index].get('Scenario_comment', ""))

        def update_scenario_choice():
            chosen = st.session_state[scenario_key]
            self.update_and_save(data, current_index, 'Scenario_judge', chosen, st.session_state.annotation_filepath)
            # 如果选择不属于 edit_options，则清空 modify 字段
            if chosen not in edit_options:
                st.session_state[scenario_mod_key] = ""
                # st.session_state[scenario_comment_key] = ""
                self.update_and_save(data, current_index, 'Scenario_modified', "", st.session_state.annotation_filepath)

        st.radio(
            "Scenario Reality Options",
            scenario_options,
            index=scenario_options.index(st.session_state[scenario_key]) if st.session_state[scenario_key] in scenario_options else 0,
            key=scenario_key,
            on_change=update_scenario_choice
        )

        if st.session_state[scenario_key] in ['Modify']:
            def update_scenario_mod():
                modified_text = st.session_state[scenario_mod_key]
                self.update_and_save(data, current_index, 'Scenario_modified', modified_text, st.session_state.annotation_filepath)
            # def update_scenario_comment():
            #     comments = st.session_state[scenario_comment_key]
            #     self.update_and_save(data, current_index, 'Scenario_comment', comments, st.session_state.annotation_filepath)
            # if st.session_state[scenario_key] == 'Modify':
            st.text_area(
                "Revised Scenario:",
                value=st.session_state[scenario_mod_key],
                key=scenario_mod_key,
                on_change=update_scenario_mod
            )
            # st.session_state[scenario_comment_key] = ""
            # data[current_index]['Scenario_comment'] = ""
            # else:
            #     st.text_area(
            #         "Comments:",
            #         value=st.session_state[scenario_comment_key],
            #         key=scenario_comment_key,
            #         on_change=update_scenario_comment
            #     )
            #     st.session_state[scenario_mod_key] = ""
            #     data[current_index]['Scenario_modified'] = ""

        if data[current_index].get('Scenario_modified', ""):
            st.write("**Modified Scenario**:", data[current_index].get('Scenario_modified', ""))

        if st.session_state[scenario_key] in ['Modify']:
            self.gpt_input(key=f"scenario_{current_index}")

        st.markdown("**(If you choose to delete this scenario, you can directly jump to the next page.)**")
        st.markdown("---")

        # -------------------- Question 1 --------------------
        st.markdown(f"### {q1_cfg.get('label', 'Question 1')}")
        q1_options = q1_cfg.get('options', [])

        st.markdown(issues_instruction)
        st.markdown("---")

        lab_issues = item.get('LabSafety_Related_Issues', {})
        aspects_keys = [
            "Most_Common_Hazards",
            "Improper_Operation_Issues",
            "Negative_Lab_Environment_Impacts",
            "Most_Likely_Safety_Incidents"
        ]
        aspects_shown = [
            "Most Common Hazards",
            "Improper Operation Issues",
            "Negative Lab Environment Impacts",
            "Most Likely Safety Incidents"
        ]

        # 初始化 question1_aspects
        if 'question1_aspects' not in data[current_index]:
            data[current_index]['question1_aspects'] = []
            for a_idx, aspect_key in enumerate(aspects_keys):
                aspect_obj = {
                    "aspect_name": aspect_key,
                    "points": []
                }
                for p_text in lab_issues.get(aspect_key, []):
                    aspect_obj["points"].append({
                        "original_text": p_text,
                        "choice": "",
                        "modified_text": "",
                        "comment": ""
                    })
                data[current_index]['question1_aspects'].append(aspect_obj)
            self.save_annotations(data, st.session_state.annotation_filepath)

        # 准备 point_choice_keys, point_mod_keys 等
        point_choice_keys = []
        point_mod_keys = []
        # point_comment_keys = []
        missing_items_keys = []
        for a_idx, aspect_data in enumerate(data[current_index]['question1_aspects']):
            point_choice_keys.append([])
            point_mod_keys.append([])
            # point_comment_keys.append([])
            missing_items_keys.append(f"missing_items_text_{a_idx}_{current_index}")
            for p_idx, point_info in enumerate(aspect_data.get('points', [])):
                point_choice_keys[a_idx].append(f"point_choice_{a_idx}_{p_idx}_{current_index}")
                point_mod_keys[a_idx].append(f"point_mod_{a_idx}_{p_idx}_{current_index}")
                # point_comment_keys[a_idx].append(f"point_comment_{a_idx}_{p_idx}_{current_index}")

        for a_idx, aspect_data in enumerate(data[current_index]['question1_aspects']):
            st.subheader(aspects_shown[a_idx])
            points_data = aspect_data.get('points', [])

            # 遍历每个 point
            for p_idx, point_info in enumerate(points_data):
                point_text = point_info.get('original_text', '')

                # 初始化 session_state
                self.ensure_session_state_key(point_choice_keys[a_idx][p_idx], point_info.get('choice', ""))
                self.ensure_session_state_key(point_mod_keys[a_idx][p_idx], point_info.get('modified_text', ""))
                # self.ensure_session_state_key(point_comment_keys[a_idx][p_idx], point_info.get('comment', ""))

                st.write(point_text)

                if data[current_index]['question1_aspects'][a_idx]['points'][p_idx].get('comment', ""):
                    st.write("**Comments**:", data[current_index]['question1_aspects'][a_idx]['points'][p_idx]['comment'])

                # 如果当前 choice 不在可选项内，重置为第一个选项
                if st.session_state[point_choice_keys[a_idx][p_idx]] not in q1_options and len(q1_options) > 0:
                    st.session_state[point_choice_keys[a_idx][p_idx]] = q1_options[0]

                def make_update_point_choice(a_index, p_index):
                    def update_point_choice():
                        chosen = st.session_state[point_choice_keys[a_index][p_index]]
                        # 更新 data
                        data[current_index]['question1_aspects'][a_index]['points'][p_index]['choice'] = chosen
                        self.save_annotations(data, st.session_state.annotation_filepath)

                        # 如果 chosen 不等于可编辑选项，则清空改写字段
                        if chosen not in edit_options:
                            st.session_state[point_mod_keys[a_index][p_index]] = ""
                            # st.session_state[point_comment_keys[a_index][p_index]] = ""
                            data[current_index]['question1_aspects'][a_index]['points'][p_index]['modified_text'] = ""
                            self.save_annotations(data, st.session_state.annotation_filepath)

                    return update_point_choice

                st.radio(
                    f"{aspects_shown[a_idx]}, Point {p_idx + 1}",
                    q1_options,
                    index=q1_options.index(st.session_state[point_choice_keys[a_idx][p_idx]]) if st.session_state[point_choice_keys[a_idx][p_idx]] in q1_options else 0,
                    key=point_choice_keys[a_idx][p_idx],
                    on_change=make_update_point_choice(a_idx, p_idx),
                    label_visibility="collapsed"
                )

                if st.session_state[point_choice_keys[a_idx][p_idx]] in edit_options:
                    def make_update_point_mod(a_index, p_index, mod=True):
                        def update_point_mod():
                            modified_text = st.session_state[point_mod_keys[a_index][p_index]]
                            data[current_index]['question1_aspects'][a_index]['points'][p_index]['modified_text'] = modified_text
                            self.save_annotations(data, st.session_state.annotation_filepath)
                        # def update_point_comment():
                        #     comment = st.session_state[point_comment_keys[a_index][p_index]]
                        #     data[current_index]['question1_aspects'][a_index]['points'][p_index]['comment'] = comment
                        #     self.save_annotations(data, st.session_state.annotation_filepath)
                        if mod:
                            return update_point_mod
                        # else:
                        #     return update_point_comment

                    # if st.session_state[point_choice_keys[a_idx][p_idx]] == 'Modify':
                    st.text_area(
                        f"Revised text for {aspects_shown[a_idx]}, Point {p_idx+1}:",
                        value=st.session_state[point_mod_keys[a_idx][p_idx]],
                        key=point_mod_keys[a_idx][p_idx],
                        on_change=make_update_point_mod(a_idx, p_idx)
                    )
                    # st.session_state[point_comment_keys[a_idx][p_idx]] = ""
                    # data[current_index]['question1_aspects'][a_idx]['points'][p_idx]['comment'] = ""
                    # else:
                    #     st.text_area(
                    #         f"Comments for {aspects_shown[a_idx]}, Point {p_idx+1}:",
                    #         value=st.session_state[point_comment_keys[a_idx][p_idx]],
                    #         key=point_comment_keys[a_idx][p_idx],
                    #         on_change=make_update_point_mod(a_idx, p_idx, False)
                    #     )
                    #     st.session_state[point_mod_keys[a_idx][p_idx]] = ""
                    #     data[current_index]['question1_aspects'][a_idx]['points'][p_idx]['modified_text'] = ""

                if data[current_index]['question1_aspects'][a_idx]['points'][p_idx].get('modified_text', ""):
                    st.write("**Modified Point**:", data[current_index]['question1_aspects'][a_idx]['points'][p_idx]['modified_text'])


            # 显示添加缺失点的 text_area
            self.ensure_session_state_key(missing_items_keys[a_idx], "")
            st.markdown(f"**Missing Points for {aspects_shown[a_idx]} (Add new points line by line):**")
            st.text_area(
                "Add Missing Points:",
                value=st.session_state[missing_items_keys[a_idx]],
                key=missing_items_keys[a_idx]
            )


            def add_missing_points(a_index):
                lines = st.session_state[missing_items_keys[a_index]].strip().split('\n')
                added = False
                for line in lines:
                    line = line.strip()
                    if line:
                        data[current_index]['question1_aspects'][a_index]['points'].append({
                            "original_text": line,
                            "choice": "",
                            "modified_text": ""
                        })
                        added = True
                if added:
                    self.save_annotations(data, st.session_state.annotation_filepath)
                    # 如果希望添加后自动清空输入框，可自行解除下面注释
                    # st.session_state[missing_items_keys[a_index]] = ""
                    st.rerun()

            add_button_key = f"add_missing_points_button_{a_idx}_{current_index}"
            if st.button("Add Missing Points", key=add_button_key):
                add_missing_points(a_idx)

            self.gpt_input(key=f"aspect_{a_idx}_{current_index}")

        # st.markdown("---")

        # -------------------- Question 2 --------------------
        st.markdown(f"### {q2_cfg.get('label', 'Question 2')}")

        q2_options = q2_cfg.get('options', [])

        st.markdown(decision_instruction)
        st.markdown("---")

        st.write('**(Updated) Scenario**:')
        if data[current_index].get('Scenario_modified', ""):
            st.write(data[current_index].get('Scenario_modified', ""))
        else:
            st.write(scenario_desc)
        st.markdown('---')

        option_consequences = item.get('Decisions', {})
        if 'question2_situations' not in data[current_index]:
            data[current_index]['question2_situations'] = []
            for opt_key in range(4):
                desc = option_consequences[opt_key].get('Decision', '')
                cons = option_consequences[opt_key].get('Consequence', '')
                data[current_index]['question2_situations'].append({
                    "decision": desc,
                    "consequence": cons,
                    "choice": "",
                    "modified_decision": "",
                    "modified_consequence": "",
                    "comment": ""
                })
            self.save_annotations(data, st.session_state.annotation_filepath)

        situation_choice_keys = []
        situation_mod_deci_keys = []
        situation_mod_cons_keys = []
        # situation_comment_keys = []
        for s_idx, situation_info in enumerate(data[current_index]['question2_situations']):
            situation_choice_keys.append(f"q2_situation{s_idx}_radio_{current_index}")
            situation_mod_deci_keys.append(f"q2_situation{s_idx}_mod_{current_index}")
            situation_mod_cons_keys.append(f"q2_situation{s_idx}_mod_cons_{current_index}")
            # situation_comment_keys.append(f"q2_situation{s_idx}_comment_{current_index}")

        for s_idx, situation_info in enumerate(data[current_index]['question2_situations']):
            decision = situation_info.get('decision', '')
            consequence = situation_info.get('consequence', '')

            self.ensure_session_state_key(situation_choice_keys[s_idx], situation_info.get('choice', ""))
            self.ensure_session_state_key(situation_mod_deci_keys[s_idx], situation_info.get('modified_decision', ""))
            self.ensure_session_state_key(situation_mod_cons_keys[s_idx], situation_info.get('modified_consequence', ""))
            # self.ensure_session_state_key(situation_comment_keys[s_idx], situation_info.get('comment', ""))

            st.markdown('**Decision:**')
            st.write( decision)
            st.markdown('**Consequence:**')
            st.write(consequence)

            if data[current_index]['question2_situations'][s_idx].get('comment', ""):
                st.write("**Comments**:", data[current_index]['question2_situations'][s_idx]['comment'])

            # 如果当前 choice 不在可选项内，重置为第一个选项
            if st.session_state[situation_choice_keys[s_idx]] not in q2_options and len(q2_options) > 0:
                st.session_state[situation_choice_keys[s_idx]] = q2_options[0]

            def make_update_situation_choice(s_index):
                def update_situation_choice():
                    chosen = st.session_state[situation_choice_keys[s_index]]
                    data[current_index]['question2_situations'][s_index]['choice'] = chosen
                    self.save_annotations(data, st.session_state.annotation_filepath)

                    if chosen not in edit_options:
                        st.session_state[situation_mod_deci_keys[s_index]] = ""
                        st.session_state[situation_mod_cons_keys[s_index]] = ""
                        # st.session_state[situation_comment_keys[s_index]] = ""
                        data[current_index]['question2_situations'][s_index]['modified_decision'] = ""
                        data[current_index]['question2_situations'][s_index]['modified_consequence'] = ""
                        # data[current_index]['question2_situations'][s_index]['comment'] = ""
                        self.save_annotations(data, st.session_state.annotation_filepath)
                return update_situation_choice

            st.radio(
                f"Decision {s_idx+1}",
                q2_options,
                index=q2_options.index(st.session_state[situation_choice_keys[s_idx]]) if st.session_state[situation_choice_keys[s_idx]] in q2_options else 0,
                key=situation_choice_keys[s_idx],
                on_change=make_update_situation_choice(s_idx),
                label_visibility="collapsed"
            )

            if st.session_state[situation_choice_keys[s_idx]] in edit_options:
                def make_update_situation_mod(si_index, mod=True, mod_decision=True):
                    def update_situation_mod_deci():
                        modified_text = st.session_state[situation_mod_deci_keys[si_index]]
                        data[current_index]['question2_situations'][si_index]['modified_decision'] = modified_text
                        self.save_annotations(data, st.session_state.annotation_filepath)
                    def update_situation_mod_cons():
                        modified_text = st.session_state[situation_mod_cons_keys[si_index]]
                        data[current_index]['question2_situations'][si_index]['modified_consequence'] = modified_text
                        self.save_annotations(data, st.session_state.annotation_filepath)
                    # def update_situation_comment():
                    #     modified_text = st.session_state[situation_comment_keys[si_index]]
                    #     data[current_index]['question2_situations'][si_index]['comment'] = modified_text
                    #     self.save_annotations(data, st.session_state.annotation_filepath)
                    if mod:
                        if mod_decision:
                            return update_situation_mod_deci
                        return update_situation_mod_cons
                    # return update_situation_comment

                # if st.session_state[situation_choice_keys[s_idx]] == 'Modify':
                st.text_area(
                    f"Revised Decision {s_idx}:",
                    value=st.session_state[situation_mod_deci_keys[s_idx]],
                    key=situation_mod_deci_keys[s_idx],
                    on_change=make_update_situation_mod(s_idx),
                )
                st.text_area(
                    f"Revised Consequence of Decision {s_idx}:",
                    value=st.session_state[situation_mod_cons_keys[s_idx]],
                    key=situation_mod_cons_keys[s_idx],
                    on_change=make_update_situation_mod(s_idx, True, False),
                )
                # st.session_state[situation_comment_keys[s_idx]] = ""
                data[current_index]['question2_situations'][s_idx]['comment'] = ""
                # else:
                #     st.text_area(
                #         f"Comments:",
                #         value=st.session_state[situation_comment_keys[s_idx]],
                #         key=situation_comment_keys[s_idx],
                #         on_change=make_update_situation_mod(s_idx, False, False),
                #     )
                #     st.session_state[situation_mod_deci_keys[s_idx]] = ""
                #     st.session_state[situation_mod_cons_keys[s_idx]] = ""
                #     data[current_index]['question2_situations'][s_idx]['modified_decision'] = ""
                #     data[current_index]['question2_situations'][s_idx]['modified_consequence'] = ""


            if data[current_index]['question2_situations'][s_idx].get('modified_decision', ""):
                st.write("**Modified Decision**:", data[current_index]['question2_situations'][s_idx]['modified_decision'])
            if data[current_index]['question2_situations'][s_idx].get('modified_consequence', ""):
                st.write("**Modified Consequence**:", data[current_index]['question2_situations'][s_idx]['modified_consequence'])

            if st.session_state[situation_choice_keys[s_idx]] in edit_options:
                self.gpt_input(key=f"situation_{s_idx}_{current_index}")


        self.gpt_input(key=f"overall_{current_index}", system_prompt='You are a helpful assistant.')

        prev_col, next_col = st.columns([1, 1])
        with prev_col:
            if st.button("Previous"):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1

                st.session_state.scroll_to_header = True
                st.rerun()

        with next_col:
            if st.button("Next"):
                if st.session_state.current_index < len(st.session_state.data) - 1:
                    st.session_state.current_index += 1

                st.session_state.scroll_to_header = True
                st.rerun()




    def display_overall_status(self, data):
        st.sidebar.subheader("Overall Status of Annotations:")
        st.sidebar.markdown("---")
        total = len(data)
        conform_count = sum(1 for d in data if d.get('scenario') == 'Conform')
        st.sidebar.write(f"Scenario Conform Count: {conform_count}/{total}")

    def run(self):
        # Step 1: Initialize scroll state in session_state
        if 'scroll_to_top' not in st.session_state:
            st.session_state.scroll_to_top = False

        if 'scroll_to_header' not in st.session_state:
            st.session_state.scroll_to_header = False

        # Step 2: Handle the scroll-to-top action
        if st.session_state.scroll_to_top:
            scroll_to_here(0,
                           key='top')  # Scroll to the top of the page, 0 means instantly, but you can add a delay (im milliseconds)
            st.session_state.scroll_to_top = False  # Reset the state after scrolling

        # Step 3: Define a scroll function to trigger the state change
        def scroll():
            st.session_state.scroll_to_top = True

        def scrollheader():
            st.session_state.scroll_to_header = True

        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox("Go to", ["Configuration", "Lab Safety Data Review Platform"], label_visibility="collapsed")

        if page == "Configuration":
            st.title("Configuration Page")
            uploaded_file = st.file_uploader("Upload a JSON data file", type="json")
            if uploaded_file is not None:
                data, annotation_filepath, dataset_name = self.load_data_file(uploaded_file)
                st.session_state.annotation_filepath = annotation_filepath
                st.session_state.dataset_name = dataset_name
                st.write("JSON Data:", data)
                st.session_state.data = data
                st.session_state.current_index = 0
                st.success("All keys are considered selected. Proceed to the annotation platforms.")

        elif page == "Lab Safety Data Review Platform":
            st.title("Lab Safety Data Review Platform")
            if st.session_state.data:
                data = st.session_state.data
                st.sidebar.number_input(
                    "Select Item Index",
                    min_value=0,
                    max_value=len(data) - 1,
                    value=st.session_state.current_index,
                    step=1,
                    key="item_index",
                    on_change=self.on_index_change
                )
                st.sidebar.markdown(f'Total items: {len(data)}')
                current_index = st.session_state.current_index
                self.display_annotation_interface(data, current_index, show_image=False)

                if st.sidebar.button("Show Status"):
                    self.display_overall_status(data)

                # 下载按钮
                self.provide_download(data, filename=st.session_state.dataset_name + "_annotation.json")


if __name__ == "__main__":
    app = AnnotationApp()
    app.run()




