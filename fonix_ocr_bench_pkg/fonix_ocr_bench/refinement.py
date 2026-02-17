import json
import re
from .model_interface import ModelInterface, PredictionResult

class Refiner:
    def __init__(self, model: ModelInterface):
        self.model = model
        self.system_instruction = "You are very good at detecting hallucinations in student's answers."

    def refine(self, evaluation_results: dict) -> dict:
        """
        Refines the evaluation results using the model.
        """
        prompt = f"""
Here there is the hallucination report but the word level error is progamatically calculated. So, the some of the predictions which are not semms to be  a hallucination is categorized as word level error, then the word level hallucination rate is got increased. So, I need you to correct the Word-level hallucination rate, DETAILED WORD-LEVEL ERRORS, and the question_type_metrics.

REPORT:
```
{json.dumps(evaluation_results, indent=4)}
```

Output should be same as given REPORT but with corrected word level hallucination rates (both global and in question_type_metrics) and DETAILED WORD-LEVEL ERRORS.
Only output the corrected report in json format nothing else.
"""
        
        result: PredictionResult = self.model.call(prompt, self.system_instruction)
        
        try:
            match = re.search(r'```json\s*(.*?)\s*```', result.text, re.DOTALL)
            if match:
                json_text = match.group(1)
                return json.loads(json_text)
            else:
                # Try simple json load if no code blocks
                return json.loads(result.text)
        except Exception as e:
            print(f"Error parsing refinement result: {e}")
            return evaluation_results # Return original if failure
