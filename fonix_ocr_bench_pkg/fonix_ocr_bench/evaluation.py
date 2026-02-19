from .utils import word_diff

class Evaluator:
    QUESTION_TYPE_LABELS = {
        "QA": "Question Answering",
        "FITB": "Fill In The Blanks",
        "W": "Writing/Essay",
        "U": "Underline",
        "C": "Circling",
        "M": "Matching"
    }

    def __init__(self):
        pass

    def iterate_answers(self, gt_ans, pred_ans, path=""): 
        """Recursively iterate through nested answer structures with path tracking"""
        if isinstance(gt_ans, dict) and "answer" in gt_ans: 
            yield gt_ans, pred_ans, path
        elif isinstance(gt_ans, dict): 
            for k in gt_ans: 
                # Ensure key exists in prediction
                if isinstance(pred_ans, dict) and k in pred_ans:
                    new_path = f"{path}.{k}" if path else k
                    yield from self.iterate_answers(gt_ans[k], pred_ans[k], new_path)

    def calculate_hallucinations(self, gt, pred):
        """
        Calculate various types of hallucinations.
        Adapted from dev.ipynb
        """
        
        # Counters
        fabricated_hallucinations = 0
        crossed_out_hallucinations = 0
        illegibility_hallucinations = 0
        
        total_gt_words = 0
        total_hallucinated_words = 0
        
        replaced_word_pairs = []
        inserted_words = []

        # Question type metrics
        question_type_metrics = {} # qtype -> {fabricated, crossed, illegible, gt_words, hallu_words}
        
        def update_qtype_metric(qtype, field, count=1):
            if qtype not in question_type_metrics:
                question_type_metrics[qtype] = {
                    "fabricated": 0,
                    "crossed": 0,
                    "illegible": 0,
                    "gt_words": 0,
                    "hallu_words": 0
                }
            question_type_metrics[qtype][field] += count
        
        # Create lookup dictionaries
        gt_questions = {q["test_number"]: q for q in gt.get("questions", [])}
        pred_questions = {q["test_number"]: q for q in pred.get("questions", [])}
        
        for tnum, gtq in gt_questions.items():
            if tnum not in pred_questions:
                continue
            
            predq = pred_questions[tnum]
            qtype = gtq.get("question_type", "Unknown")
            
            gt_ans = gtq.get("student_answers", "")
            pred_ans = predq.get("student_answers", "")
            
            # -------- Essay level hallucination --------
            if isinstance(gt_ans, str):
                # Fabricated hallucination: AI reads text where there is none
                if gt_ans == "" and pred_ans != "":
                    fabricated_hallucinations += 1
                    update_qtype_metric(qtype, "fabricated")
                
                # Word-level hallucination for essays
                if isinstance(pred_ans, str) and gt_ans.strip() != "":
                    diff = word_diff(gt_ans, pred_ans)
                    
                    for tag, gtw, prw in diff:
                        if tag == "replace" and gtw != prw:
                            replaced_word_pairs.append({
                                "question": tnum,
                                "gt_words": gtw,
                                "pred_words": prw
                            })
                            total_hallucinated_words += len(prw)
                            update_qtype_metric(qtype, "hallu_words", len(prw))
                        
                        elif tag == "insert" and prw:
                            inserted_words.append({
                                "question": tnum,
                                "words": prw
                            })
                            total_hallucinated_words += len(prw)
                            update_qtype_metric(qtype, "hallu_words", len(prw))
                    
                    word_count = len(gt_ans.split())
                    total_gt_words += word_count
                    update_qtype_metric(qtype, "gt_words", word_count)
                
                continue
            
            # -------- Structured QA hallucination --------
            for gtqa, predqa, sub_path in self.iterate_answers(gt_ans, pred_ans):
                
                # 1. Fabricated hallucination
                if gtqa["answer"] == "" and predqa.get("answer", "") != "":
                    fabricated_hallucinations += 1
                    update_qtype_metric(qtype, "fabricated")
                
                # 2. Crossed-out text hallucination
                # If GT has crossed_out_text, and prediction includes those words
                if gtqa.get("crossedout_text") and predqa.get("answer", ""):
                    pred_answer_lower = predqa["answer"].lower()
                    for crossed_word in gtqa["crossedout_text"]:
                        if crossed_word.lower() in pred_answer_lower:
                            crossed_out_hallucinations += 1
                            update_qtype_metric(qtype, "crossed")
                
                # 3. Illegibility hallucination
                gt_legible = str(gtqa.get("is_legible", "")).lower()
                pred_legible = str(predqa.get("is_legible", "")).lower()
                
                if gt_legible not in ["true"]:
                    # GT answer is blank/illegible; if AI claims it's legible or provides text, it hallucinated
                    if pred_legible == "true" or predqa.get("answer", "") != "":
                        illegibility_hallucinations += 1
                        update_qtype_metric(qtype, "illegible")
                
                # 4. Word-level hallucination (for readable text)
                if gtqa["answer"] != "" and predqa.get("answer", "") != "":
                    diff = word_diff(gtqa["answer"], predqa["answer"])
                    
                    for tag, gtw, prw in diff:
                        if tag == "replace" and gtw != prw:
                            replaced_word_pairs.append({
                                "question": tnum,
                                "sub_question": sub_path,
                                "gt_words": gtw,
                                "pred_words": prw
                            })
                            total_hallucinated_words += len(prw)
                            update_qtype_metric(qtype, "hallu_words", len(prw))
                        
                        elif tag == "insert" and prw:
                            inserted_words.append({
                                "question": tnum,
                                "sub_question": sub_path,
                                "words": prw
                            })
                            total_hallucinated_words += len(prw)
                            update_qtype_metric(qtype, "hallu_words", len(prw))
                    
                    word_count = len(gtqa["answer"].split())
                    total_gt_words += word_count
                    update_qtype_metric(qtype, "gt_words", word_count)
        
        # -------- Calculate rates --------
        hallucination_rate = (
            total_hallucinated_words / total_gt_words
            if total_gt_words > 0 else 0
        )
        
        fabricated_hallucination_rate = (
            fabricated_hallucinations / total_gt_words
            if total_gt_words > 0 else 0
        )
        
        crossed_out_hallucination_rate = (
            crossed_out_hallucinations / total_gt_words
            if total_gt_words > 0 else 0
        )
        
        illegibility_hallucination_rate = (
            illegibility_hallucinations / total_gt_words
            if total_gt_words > 0 else 0
        )

        return {
            "fabricated_hallucinations": fabricated_hallucinations,
            "fabricated_hallucination_rate": fabricated_hallucination_rate,
            "crossed_out_hallucinations": crossed_out_hallucinations,
            "crossed_out_hallucination_rate": crossed_out_hallucination_rate,
            "illegibility_hallucinations": illegibility_hallucinations,
            "illegibility_hallucination_rate": illegibility_hallucination_rate,
            "word_level_hallucination_rate": hallucination_rate,
            "total_hallucinated_words": total_hallucinated_words,
            "total_gt_words": total_gt_words,
            "replaced_word_pairs": replaced_word_pairs,
            "inserted_words": inserted_words,
            "question_type_metrics": question_type_metrics
        }

