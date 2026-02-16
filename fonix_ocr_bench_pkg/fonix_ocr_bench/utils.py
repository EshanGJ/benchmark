from difflib import SequenceMatcher

def word_diff(gt, pred):
    gt_words = gt.split()
    pred_words = pred.split()
    
    gt_words_lower = [w.lower() for w in gt_words]
    pred_words_lower = [w.lower() for w in pred_words]
    
    matcher = SequenceMatcher(None, gt_words_lower, pred_words_lower)
    diffs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        # tag can be: 'replace', 'delete', 'insert', 'equal'
        if tag != 'equal':
            diffs.append((tag, gt_words[i1:i2], pred_words[j1:j2]))
    return diffs
