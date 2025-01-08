scenario_instruction = '''**Task for Experts**

Your task is to review and evaluate each **scenario** generated using the provided prompt. For each scenario, you need to:

1. **Evaluate the Scenario’s Realism**:
   - Assess whether the scenario is realistic and plausible in an actual laboratory setting.
   - Ensure the scenario provides sufficient detail about the laboratory environment, equipment, substances, their storage conditions, and placement to align with the question.

2. **Ensure Accurate and Informed Judgments**:
   - Verify all details for accuracy and relevance.
   - For any uncertainties, consult reliable resources to provide a confident and well-informed judgment.

---

**For Each Scenario, Choose One of the Following Options**:

1. **Conform**:
   - Select this option if the scenario is realistic, meaningful, and aligns appropriately with the laboratory setting described in the question.

2. **Delete**:
   - Choose this option if the scenario:
     - Is illogical or nonsensical.
     - Is overly similar to a previously presented scenario.
     - Lacks essential details or context to make it plausible.
     - Contains inherent contradictions or inconsistencies.

3. **Modify**:
   - Select this option if the scenario requires refinement.
     - Provide the revised **Scenario** in the input box.
     - Ensure your language is formal and professional, as your changes will directly reflect in the revised question.
     - To refine your input further, you can use the GPT-4o API integrated into the system. Enter your draft or instructions for refinement, and you’ll receive a polished result within seconds. However, do not entirely rely on GPT for complex or specialized knowledge—ensure professional accuracy in your edits.

4. **Comment**:
   - If you remain uncertain after consulting relevant resources, select this option.
   - Provide detailed concerns or questions regarding the scenario to guide further review or discussion.'''

issues_instruction = '''**Task for Experts**

Your task is to review and evaluate the **lab-safety-related issues** identified for each scenario. For every issue, you need to:

1. **Assess Quality and Alignment**:
   - Determine if each issue is accurate and appropriately aligned with the described scenario.
   - Ensure issues are categorized correctly and belong only to the specified category.

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
   - Choose this option if the issue:
     - Is a duplicate or overly similar to another issue within the same category.
     - Does not belong to the specified category.
     - Is unrelated to the scenario.
     - Is vague or non-specific.

3. **Modify**:
   - Select this option if the issue requires refinement.
     - Provide the revised **Issue** in the input box.
     - Ensure your language is formal and professional, as your changes will directly reflect in the revised content.
     - To refine your input further, you can use the GPT-4o API integrated into the system. Enter your draft or instructions for refinement, and you’ll receive a polished result within seconds. However, do not entirely rely on GPT for complex or specialized knowledge—ensure professional accuracy in your edits.

4. **Comment**:
   - If you remain uncertain after consulting relevant resources, select this option.
   - Provide detailed concerns or questions regarding the issue to guide further review or discussion.

---

**Additional Task: Add Missing Points**  
- For each category, assess if there are any significant lab-safety issues missing.  
- Add these missing points in the **Add Missing Points** section. Use clear, concise, and professional language. Refine your inputs using the GPT-4o API if needed.'''

decision_instruction = '''**Task for Experts**

Your task is to review and evaluate each **decision** and its corresponding **consequence** generated using the provided prompt. For each decision, you need to:

1. **Evaluate the Decision's Validity**:
   - Assess whether the decision is meaningful and relevant within the context of laboratory safety.
   - Determine if the decision logically leads to the stated consequence.

2. **Ensure Accurate and Informed Judgments**:
   - Consult relevant resources for any uncertainties to ensure your assessments are accurate and thorough.
   - Provide clear and confident conclusions.

---

**For Each Decision, Choose One of the Following Options**:

1. **Correct**:
   - Select this option if the decision is meaningful, relevant, and directly leads to the stated consequence as described.

2. **Delete**:
   - Choose this if the decision is illogical, nonsensical, irrelevant to the scenario, or if it is similar to or duplicates another decision.

3. **Modify**:
   - Use this option if you believe the decision or consequence requires refinement.
     - Provide the revised **Decision** in the first input box.
     - Provide the revised **Consequence** in the second input box.
     - If only one of the two (Decision or Consequence) requires modification, leave the other box empty.
     - Ensure your language is formal and professional, as your changes will directly reflect in the revised question.
     - To refine your input further, you can use the GPT-4o API integrated into the system. Enter your draft or instructions for refinement, and you’ll receive a polished result within seconds. However, do not entirely rely on GPT for complex or specialized knowledge—ensure professional accuracy in your edits.

4. **Comment**:
   - If you remain uncertain after consulting relevant resources, select this option.
   - Provide detailed concerns or questions regarding the decision or consequence to guide further review or discussion.'''

