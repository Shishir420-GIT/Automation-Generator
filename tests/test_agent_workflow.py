import sys
import types
import unittest


def install_streamlit_stub():
    streamlit = types.ModuleType("streamlit")
    streamlit.error = lambda *args, **kwargs: None
    streamlit.info = lambda *args, **kwargs: None
    streamlit.warning = lambda *args, **kwargs: None
    streamlit.success = lambda *args, **kwargs: None

    components = types.ModuleType("streamlit.components")
    components_v1 = types.ModuleType("streamlit.components.v1")
    components_v1.html = lambda *args, **kwargs: None
    components.v1 = components_v1

    sys.modules.setdefault("streamlit", streamlit)
    sys.modules.setdefault("streamlit.components", components)
    sys.modules.setdefault("streamlit.components.v1", components_v1)


install_streamlit_stub()

from utils.agent_service import AutomationAgentService, AutomationRequest, AutomationResult


class FakeGemini:
    def gemini_summarize(self, pdf_text, domain, extra_info=""):
        return "A detailed summary for an invoice approval workflow with validation and routing."

    def gemini_generate_mermaid_diagram(self, summary, domain, extra_info="", complexity="moderate"):
        return "not a flowchart"

    def gemini_generate_script(self, summary, domain, extra_info=""):
        return "eval('bad')"

    def gemini_generate_unit_tests(self, summary, script, domain, extra_info=""):
        return """```python
import unittest

class TestAutomation(unittest.TestCase):
    def test_example(self):
        self.assertTrue(True)
```"""

    def gemini_generate_prerequisites(self, summary, domain, extra_info=""):
        return "Python 3.11 or newer and access to the source system."

    def gemini_generate_content(self, prompt, model_name="gemini-1.5-flash", operation="content generation"):
        if operation == "Mermaid correction":
            return """flowchart TD
    A["Start"] --> B{"Validate invoice?"}
    B -->|"Yes"| C["Route approval"]
    B -->|"No"| D["Reject invoice"]
"""
        if operation == "script correction":
            return """import logging

def main():
    logging.info("Run automation")

if __name__ == "__main__":
    main()
"""
        return ""


class AgentWorkflowTest(unittest.TestCase):
    def test_stream_generates_result_and_validation_events(self):
        service = AutomationAgentService(FakeGemini(), max_retries=1)
        request = AutomationRequest(
            pdf_text="This SOP describes invoice approval and exception handling.",
            domain="Finance",
        )

        items = list(service.stream(request))
        result = next(item for item in items if isinstance(item, AutomationResult))
        events = [item for item in items if not isinstance(item, AutomationResult)]

        self.assertIn("A detailed summary", result.summary)
        self.assertTrue(result.mermaid_diagram.startswith("flowchart TD"))
        self.assertIn("def main", result.script)
        self.assertIn("unittest", result.unit_tests)
        self.assertTrue(any(event.type == "retry" for event in events))
        self.assertTrue(any(event.type == "validation" for event in events))
        self.assertTrue(any(issue.component == "script" for issue in result.validation_report))


if __name__ == "__main__":
    unittest.main()
