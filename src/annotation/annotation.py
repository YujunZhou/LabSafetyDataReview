import os
import streamlit as st
import yaml
import json
import base64

class AnnotationApp:
    def __init__(self):
        self.config = self.load_config()
        self.session_state_initialization()

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
        with open("src/config/annotation_config.yaml", "r") as file:
            config = yaml.safe_load(file)
        return config

    def initialize_annotation_state(self, index):
        if f"feedback_{index}" not in st.session_state:
            st.session_state[f"feedback_{index}"] = ""

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
            for item in (data if isinstance(data, list) else [data]):
                if 'feedback' not in item:
                    item['feedback'] = ""
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

    def display_annotation_interface(self, data, current_index, show_image=False):
        self.initialize_annotation_state(current_index)
        item = data[current_index]

        # Since we no longer use selected_keys, we display all keys except excluded ones.
        all_keys = set(item.keys())
        exclude_keys = {
            'feedback', 'Scenario', 'LabSafetyRelatedIssues', 'OptionConsequences',
            'scenario_reality', 'scenario_reality_modified', 'question1_aspects', 'question2_situations'
        }
        display_keys = [key for key in all_keys if key not in exclude_keys]

        # st.subheader("Item Data:")
        # st.write({key: item.get(key, None) for key in display_keys})

        # if show_image and 'image_urls' in item:
        #     image_urls = item['image_urls']
        #     if image_urls:
        #         cols = st.columns(len(image_urls))
        #         for i, image_url in enumerate(image_urls):
        #             image_path = os.path.join('data', st.session_state.dataset_name, image_url)
        #             if os.path.exists(image_path):
        #                 with cols[i]:
        #                     st.markdown(
        #                         f'<img src="data:image/jpeg;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" '
        #                         f'style="width:100%;" alt="{image_url}">',
        #                         unsafe_allow_html=True
        #                     )
        #             else:
        #                 st.warning(f"Image not found: {image_path}")

        scenario_cfg = self.config.get('scenario_reality', {})
        q1_cfg = self.config.get('question1', {})
        q2_cfg = self.config.get('question2', {})

        st.markdown(f"### Topic: {data[current_index]['Topic']}")
        # Scenario Reality
        st.markdown(f"### {scenario_cfg.get('label', 'Scenario Reality')}")
        scenario_desc = item.get('Scenario', 'No scenario description available.')
        st.write(scenario_desc)
        scenario_options = scenario_cfg.get('options', [])
        scenario_edit_option = scenario_cfg.get('editable_option', None)

        scenario_key = f"scenario_reality_radio_{current_index}"
        scenario_mod_key = f"scenario_reality_mod_{current_index}"

        if scenario_key not in st.session_state:
            st.session_state[scenario_key] = item.get('scenario_reality', "")
        if scenario_mod_key not in st.session_state:
            st.session_state[scenario_mod_key] = item.get('scenario_reality_modified', "")

        # If the stored choice is not in the list of available options, reset it
        if st.session_state[scenario_key] not in scenario_options:
            # Reset to the first available option or any default choice
            st.session_state[scenario_key] = scenario_options[0]

        def update_scenario_choice():
            chosen = st.session_state[scenario_key]
            data[current_index]['scenario_reality'] = chosen
            if chosen != scenario_edit_option:
                st.session_state[scenario_mod_key] = ""
                data[current_index]['scenario_reality_modified'] = ""
            self.save_annotations(data, st.session_state.annotation_filepath)

        st.radio(
            "Scenario Reality Options",
            scenario_options,
            index=None,
            key=scenario_key,
            on_change=update_scenario_choice
        )

        if st.session_state[scenario_key] == scenario_edit_option:
            def update_scenario_mod():
                modified_text = st.session_state[scenario_mod_key]
                data[current_index]['scenario_reality_modified'] = modified_text
                self.save_annotations(data, st.session_state.annotation_filepath)
            st.text_area(
                "Modify the scenario:",
                value=st.session_state[scenario_mod_key],
                key=scenario_mod_key,
                on_change=update_scenario_mod
            )


        st.markdown("---")

        # Question 1
        st.markdown(f"### {q1_cfg.get('label', 'Question 1')}")
        q1_options = q1_cfg.get('options', [])
        q1_edit_option = q1_cfg.get('editable_option', None)

        lab_issues = item.get('LabSafetyRelatedIssues', {})
        aspects_keys = [
            "MostCommonHazards",
            "ImproperOperationIssues",
            "NegativeLabEnvironmentImpacts",
            "MostLikelySafetyIncidents"
        ]
        aspects_shown = [
            "Most Common Hazards",
            "Improper Operation Issues",
            "Negative Lab Environment Impacts",
            "Most Likely Safety Incidents"
        ]

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
                        "modified_text": ""
                    })
                data[current_index]['question1_aspects'].append(aspect_obj)
            self.save_annotations(data, st.session_state.annotation_filepath)

        point_choice_keys = []
        point_mod_keys = []
        missing_items_keys = []
        for a_idx, aspect_data in enumerate(data[current_index]['question1_aspects']):
            point_choice_keys.append([])
            point_mod_keys.append([])
            missing_items_keys.append([f"missing_items_text_{a_idx}_{current_index}"])
            for p_idx, point_info in enumerate(aspect_data.get('points', [])):
                point_choice_keys[a_idx].append(f"point_choice_{a_idx}_{p_idx}_{current_index}")
                point_mod_keys[a_idx].append(f"point_mod_{a_idx}_{p_idx}_{current_index}")
        # Display and edit aspects
        for a_idx, aspect_data in enumerate(data[current_index]['question1_aspects']):
            aspect_name = aspect_data.get('aspect_name', f"Aspect {a_idx+1}")
            st.subheader(aspects_shown[a_idx])
            points_data = aspect_data.get('points', [])

            # Display each point
            for p_idx, point_info in enumerate(points_data):
                point_text = point_info.get('original_text', '')

                if point_choice_keys[a_idx][p_idx] not in st.session_state:
                    st.session_state[point_choice_keys[a_idx][p_idx]] = point_info.get('choice', "")

                if point_mod_keys[a_idx][p_idx] not in st.session_state:
                    st.session_state[point_mod_keys[a_idx][p_idx]] = point_info.get('modified_text', "")

                st.write(point_text)

                # If the stored choice is not in the list of available options, reset it
                if st.session_state[point_choice_keys[a_idx][p_idx]] not in q1_options:
                    # Reset to the first available option or any default choice
                    st.session_state[point_choice_keys[a_idx][p_idx]] = q1_options[0]

                def make_update_point_choice(a_index, p_index):
                    def update_point_choice():
                        print(point_choice_keys[a_index][p_index], a_index, p_index)
                        chosen = st.session_state[point_choice_keys[a_index][p_index]]
                        print(st.session_state[point_choice_keys[a_index][p_index]])
                        data[current_index]['question1_aspects'][a_index]['points'][p_index]['choice'] = chosen
                        if chosen != q1_edit_option:
                            st.session_state[point_mod_keys[a_index][p_index]] = ""
                            data[current_index]['question1_aspects'][a_index]['points'][p_index]['modified_text'] = ""
                        self.save_annotations(data, st.session_state.annotation_filepath)

                    return update_point_choice

                # print(st.session_state[point_choice_key])
                st.radio(
                    f"Aspect {a_idx + 1}, Point {p_idx + 1}",
                    q1_options,
                    # index=q1_options.index(st.session_state[point_choice_keys[a_idx][p_idx]]) if st.session_state[
                    #                                                                   point_choice_keys[a_idx][p_idx]] in q1_options else 0,
                    key=point_choice_keys[a_idx][p_idx],
                    on_change=make_update_point_choice(a_idx, p_idx),
                    label_visibility="collapsed"
                )

                # print(st.session_state[point_choice_key])
                if st.session_state[point_choice_keys[a_idx][p_idx]] == q1_edit_option:
                    def make_update_point_mod(a_index, p_index):
                        def update_point_mod():
                            modified_text = st.session_state[point_mod_keys[a_index][p_index]]
                            data[current_index]['question1_aspects'][a_index]['points'][p_index][
                                'modified_text'] = modified_text
                            self.save_annotations(data, st.session_state.annotation_filepath)

                        return update_point_mod

                    st.text_area(
                        f"Modify {aspect_name}, Point {p_idx+1}:",
                        value=st.session_state[point_mod_keys[a_idx][p_idx]],
                        key=point_mod_keys[a_idx][p_idx],
                        on_change=make_update_point_mod(a_idx, p_idx)
                    )

            # Add missing items section

            if missing_items_keys[a_idx] not in st.session_state:
                st.session_state[missing_items_keys[a_idx]] = ""

            st.markdown("**Missing Items (Add new points line by line):**")
            st.text_area(
                "Add Missing Points:",
                value=st.session_state[missing_items_keys[a_idx]],
                key=missing_items_keys[a_idx]
            )

            # def make_add_missing_points(a_index):
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
                    # st.session_state[missing_items_keys[a_index]] = ""
                    self.save_annotations(data, st.session_state.annotation_filepath)
                    st.rerun()

                # return add_missing_points

            add_button_key = f"add_missing_points_button_{a_idx}_{current_index}"
            if st.button("Add Missing Points", key=add_button_key):
                add_missing_points(a_index=a_idx)

        st.markdown("---")

        # Question 2
        st.markdown(f"### {q2_cfg.get('label', 'Question 2')}")
        q2_options = q2_cfg.get('options', [])
        q2_edit_option = q2_cfg.get('editable_option', None)

        option_consequences = item.get('OptionConsequences', {})
        if 'question2_situations' not in data[current_index]:
            data[current_index]['question2_situations'] = []
            for opt_key in ['A', 'B', 'C', 'D']:
                if opt_key in option_consequences:
                    desc = option_consequences[opt_key].get('Description', '')
                    cons = option_consequences[opt_key].get('Consequence', '')
                    full_text = f"Option {opt_key}: {desc}\n\nConsequence: {cons}"
                    data[current_index]['question2_situations'].append({
                        "option_key": opt_key,
                        "original_text": full_text,
                        "choice": "",
                        "modified_text": ""
                    })
            self.save_annotations(data, st.session_state.annotation_filepath)

        situation_choice_keys = []
        situation_mod_keys = []
        for s_idx, situation_info in enumerate(data[current_index]['question2_situations']):
            situation_choice_keys.append(f"q2_situation{s_idx}_radio_{current_index}")
            situation_mod_keys.append(f"q2_situation{s_idx}_mod_{current_index}")

        for s_idx, situation_info in enumerate(data[current_index]['question2_situations']):
            situation_text = situation_info.get('original_text', '')

            if situation_choice_keys[s_idx] not in st.session_state:
                st.session_state[situation_choice_keys[s_idx]] = situation_info.get('choice', "")

            if situation_mod_keys[s_idx] not in st.session_state:
                st.session_state[situation_mod_keys[s_idx]] = situation_info.get('modified_text', "")

            st.write(situation_text)

            # If the stored choice is not in the list of available options, reset it
            if st.session_state[situation_choice_keys[s_idx]] not in q2_options:
                # Reset to the first available option or any default choice
                st.session_state[situation_choice_keys[s_idx]] = q2_options[0]
            def make_update_situation_choice(s_index):
                def update_situation_choice():
                    chosen = st.session_state[situation_choice_keys[s_index]]
                    data[current_index]['question2_situations'][s_index]['choice'] = chosen
                    if chosen != q2_edit_option:
                        st.session_state[situation_mod_keys[s_index]] = ""
                        data[current_index]['question2_situations'][s_index]['modified_text'] = ""
                    self.save_annotations(data, st.session_state.annotation_filepath)

                return update_situation_choice

            st.radio(
                f"Situation {s_idx+1}",
                q2_options,
                index=q2_options.index(st.session_state[situation_choice_keys[s_idx]]) if st.session_state[situation_choice_keys[s_idx]] in q2_options else 0,
                key=situation_choice_keys[s_idx],
                on_change=make_update_situation_choice(s_idx),
                label_visibility="collapsed"
            )
            options = ['A', 'B', 'C', 'D']
            if st.session_state[situation_choice_keys[s_idx]] == q2_edit_option:
                def make_update_situation_mod(si_index):
                    def update_situation_mod():
                        modified_text = st.session_state[situation_mod_keys[si_index]]
                        data[current_index]['question2_situations'][si_index]['modified_text'] = modified_text
                        self.save_annotations(data, st.session_state.annotation_filepath)

                    return update_situation_mod
                st.text_area(
                    f"Modify Concequence of Option {options[s_idx]}:",
                    value=st.session_state[situation_mod_keys[s_idx]],
                    key=situation_mod_keys[s_idx],
                    on_change=make_update_situation_mod(s_idx)
                )

        st.markdown("---")

        # Feedback
        feedback_col, status_col = st.columns(2)
        with feedback_col:
            def update_feedback():
                st.session_state[f"feedback_{current_index}"] = st.session_state[f"feedback_textarea_{current_index}"]
                data[current_index]['feedback'] = st.session_state[f"feedback_{current_index}"]
                self.save_annotations(data, st.session_state.annotation_filepath)

            if f"feedback_textarea_{current_index}" not in st.session_state:
                st.session_state[f"feedback_textarea_{current_index}"] = item.get('feedback', "")

            st.subheader("Feedback:")
            st.text_area(
                "feedback",
                value=st.session_state[f"feedback_textarea_{current_index}"],
                key=f"feedback_textarea_{current_index}",
                on_change=update_feedback,
                label_visibility="collapsed",
            )

        with status_col:
            st.subheader("Status")
            st.write("Annotation status is being updated with your selections.")

        prev_col, next_col = st.columns([1, 1])
        with prev_col:
            st.button("Previous", on_click=self.go_previous)
        with next_col:
            st.button("Next", on_click=self.go_next)

    def display_overall_status(self, data):
        st.sidebar.subheader("Overall Status of Annotations:")
        st.sidebar.markdown("---")
        total = len(data)
        conform_count = sum(1 for d in data if d.get('scenario_reality') == 'Conform')
        st.sidebar.write(f"Scenario Conform Count: {conform_count}/{total}")

    def run(self):
        self.load_css()
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox("Go to", ["Configuration", "Text Annotation Platform"], label_visibility="collapsed")

        if page == "Configuration":
            st.title("Configuration Page")
            uploaded_file = st.file_uploader("Upload a JSON data file", type="json")
            if uploaded_file is not None:
                data, annotation_filepath, dataset_name = self.load_data_file(uploaded_file)
                st.session_state.annotation_filepath = annotation_filepath
                st.session_state.dataset_name = dataset_name
                st.write("JSON Data:", data)
                # Since we now take all keys, no selection step is needed.
                # All keys will be considered selected by default.
                st.session_state.data = data
                st.session_state.current_index = 0
                for i in range(len(data)):
                    self.initialize_annotation_state(i)
                st.success("All keys are considered selected. Proceed to the annotation platforms.")

        elif page == "Text Annotation Platform":
            st.title("Text Annotation Platform")
            # No longer checking for selected keys
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

        # elif page == "Image Annotation Platform":
        #     st.title("Image Annotation Platform")
        #     # No longer checking for selected keys
        #     if st.session_state.data:
        #         data = st.session_state.data
        #         st.sidebar.number_input(
        #             "Select Item Index",
        #             min_value=0,
        #             max_value=len(data) - 1,
        #             value=st.session_state.current_index,
        #             step=1,
        #             key="item_index",
        #             on_change=self.on_index_change
        #         )
        #         st.sidebar.markdown(f'Total items: {len(data)}')
        #         current_index = st.session_state.current_index
        #         self.display_annotation_interface(data, current_index, show_image=True)
        #
        #         if st.sidebar.button("Show Status"):
        #             self.display_overall_status(data)

if __name__ == "__main__":
    app = AnnotationApp()
    app.run()
