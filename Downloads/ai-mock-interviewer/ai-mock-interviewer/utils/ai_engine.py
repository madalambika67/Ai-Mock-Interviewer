"""
AI Engine for the Mock Interviewer.

Two modes:
  1. Offline heuristic engine (default, zero-setup, zero-cost)
  2. Pluggable real LLM scoring (OpenAI or Anthropic)

Both paths return the same score schema.
"""

import json
import os
import random
import re


# --------------------------------------------------------------------------
# Load question bank
# --------------------------------------------------------------------------

# ai_engine.py and questions.json are in the same project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    QUESTION_BANK = json.load(f)


FILLER_WORDS = [
    "um",
    "uh",
    "like",
    "you know",
    "basically",
    "actually",
    "sort of",
    "kind of",
    "i guess",
    "maybe",
]

HEDGING_WORDS = [
    "i think maybe",
    "not sure but",
    "i guess",
    "possibly",
    "i don't know if",
]

STAR_KEYWORDS = {
    "situation": [
        "situation",
        "context",
        "when i",
        "at my previous",
        "while working",
        "there was a time",
    ],
    "task": [
        "task",
        "responsible for",
        "my role",
        "needed to",
        "goal was",
        "objective",
    ],
    "action": [
        "i did",
        "i implemented",
        "i decided",
        "i built",
        "i created",
        "i led",
        "i designed",
        "i took the initiative",
        "so i",
    ],
    "result": [
        "result",
        "outcome",
        "as a result",
        "eventually",
        "in the end",
        "this led to",
        "improved",
        "increased",
        "reduced",
        "achieved",
    ],
}


# --------------------------------------------------------------------------
# Question generation
# --------------------------------------------------------------------------

def get_role_data(role):
    return QUESTION_BANK["roles"].get(
        role,
        QUESTION_BANK["roles"]["General / Other"]
    )


def build_interview_questions(
    role,
    interview_type,
    difficulty,
    num_questions=8,
    resume_skills=None
):
    """
    Builds an ordered list of question dicts:
    {text, category, difficulty}
    """

    role_data = get_role_data(role)
    resume_skills = resume_skills or []
    pool = []

    def add(bank, category, diffs):
        for d in diffs:
            for q in bank.get(d, []):
                pool.append({
                    "text": q,
                    "category": category,
                    "difficulty": d
                })

    diff_order = {
        "easy": ["easy", "medium"],
        "medium": ["easy", "medium", "hard"],
        "hard": ["medium", "hard"],
    }

    diffs = diff_order.get(
        difficulty,
        ["easy", "medium", "hard"]
    )

    if interview_type in ("technical", "mixed"):
        add(
            role_data["technical"],
            "technical",
            diffs
        )

    if interview_type in ("role-specific", "mixed"):
        add(
            role_data["role_specific"],
            "role-specific",
            diffs
        )

    if interview_type in ("hr", "mixed"):
        add(
            QUESTION_BANK["hr"],
            "hr",
            diffs
        )

    if interview_type in ("behavioral", "mixed"):
        add(
            QUESTION_BANK["behavioral"],
            "behavioral",
            diffs
        )

    # Personalize questions based on resume skills
    def relevance(q):
        return -sum(
            1
            for s in resume_skills
            if s.lower() in q["text"].lower()
        )

    random.shuffle(pool)
    pool.sort(key=relevance)

    selected = (
        pool[:num_questions]
        if len(pool) >= num_questions
        else pool
    )

    for i, q in enumerate(selected):
        q["order_index"] = i

    return selected


def generate_follow_up(question_text, answer_text):
    """Return a follow-up question when the answer is too short."""

    word_count = len(answer_text.split())

    if word_count < 25:
        return random.choice(
            QUESTION_BANK["follow_up_templates"]
        )

    return None


# --------------------------------------------------------------------------
# Offline heuristic scoring engine
# --------------------------------------------------------------------------

def _keyword_overlap_score(
    question_text,
    answer_text,
    role_skills
):
    q_words = set(
        re.findall(
            r"[a-zA-Z+#.]+",
            question_text.lower()
        )
    )

    a_words = set(
        re.findall(
            r"[a-zA-Z+#.]+",
            answer_text.lower()
        )
    )

    skill_words = set(
        s.lower()
        for s in role_skills
    )

    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "you",
        "your",
        "to",
        "of",
        "and",
        "in",
        "for",
        "how",
        "what",
        "why",
        "do",
        "does",
        "with",
        "on",
        "would",
        "tell",
        "me",
        "about",
    }

    q_words -= stopwords

    overlap = len(q_words & a_words) / max(
        len(q_words),
        1
    )

    skill_hits = len(skill_words & a_words)

    skill_bonus = min(
        skill_hits * 8,
        30
    )

    score = min(
        100,
        overlap * 70 + skill_bonus + 20
    )

    return round(score, 1)


def _communication_score(answer_text):
    words = answer_text.split()
    word_count = len(words)
    lowered = answer_text.lower()

    filler_count = sum(
        lowered.count(f)
        for f in FILLER_WORDS
    )

    filler_ratio = filler_count / max(
        word_count,
        1
    )

    sentences = max(
        len(re.findall(r"[.!?]+", answer_text)),
        1
    )

    avg_sentence_len = (
        word_count / sentences
    )

    length_score = (
        100
        if 40 <= word_count <= 180
        else max(
            30,
            100 - abs(word_count - 100) * 0.6
        )
    )

    filler_penalty = min(
        filler_ratio * 400,
        40
    )

    structure_bonus = (
        10
        if 8 <= avg_sentence_len <= 25
        else 0
    )

    score = max(
        0,
        min(
            100,
            length_score
            - filler_penalty
            + structure_bonus
        )
    )

    return round(score, 1)


def _confidence_score(answer_text):
    lowered = answer_text.lower()

    hedges = sum(
        lowered.count(h)
        for h in HEDGING_WORDS
    )

    word_count = len(
        answer_text.split()
    )

    hedge_ratio = hedges / max(
        word_count,
        1
    )

    assertive_markers = [
        "i led",
        "i decided",
        "i implemented",
        "i achieved",
        "i am confident",
        "definitely",
        "certainly",
        "i ensured",
        "i successfully",
    ]

    assertive_hits = sum(
        lowered.count(m)
        for m in assertive_markers
    )

    score = (
        70
        - hedge_ratio * 500
        + min(assertive_hits * 8, 30)
    )

    return round(
        max(0, min(100, score)),
        1
    )


def _clarity_score(answer_text):
    words = answer_text.split()
    word_count = len(words)

    if word_count == 0:
        return 0.0

    long_words = sum(
        1
        for w in words
        if len(w) > 12
    )

    long_word_ratio = (
        long_words / word_count
    )

    sentences = max(
        len(re.findall(r"[.!?]+", answer_text)),
        1
    )

    avg_sentence_len = (
        word_count / sentences
    )

    penalty = 0

    if avg_sentence_len > 35:
        penalty += 20

    penalty += min(
        long_word_ratio * 100,
        15
    )

    score = 95 - penalty

    return round(
        max(0, min(100, score)),
        1
    )


def _completeness_score(
    answer_text,
    category
):
    word_count = len(
        answer_text.split()
    )

    target = (
        120
        if category in ("technical", "behavioral")
        else 80
    )

    ratio = min(
        word_count / target,
        1.2
    )

    score = ratio * 90

    if category == "behavioral":
        star = _detect_star(answer_text)
        star_hits = sum(
            star.values()
        )
        score += star_hits * 2.5

    return round(
        max(0, min(100, score)),
        1
    )


def _detect_star(answer_text):
    lowered = answer_text.lower()
    result = {}

    for part, keywords in STAR_KEYWORDS.items():
        result[part] = any(
            k in lowered
            for k in keywords
        )

    return result


def analyze_answer_heuristic(
    question_text,
    answer_text,
    category,
    role_skills,
    time_taken=None,
    seconds_allotted=None
):
    answer_text = (
        answer_text or ""
    ).strip()

    if not answer_text:
        zero = 0.0

        return {
            "technical_accuracy": zero,
            "relevance": zero,
            "communication": zero,
            "clarity": zero,
            "confidence": zero,
            "completeness": zero,
            "question_score": zero,
            "star_feedback": None,
            "feedback": (
                "No answer was provided for this question. "
                "Try to answer every question, even briefly - "
                "an incomplete or vague answer scores far better "
                "than a blank one."
            ),
        }

    relevance = _keyword_overlap_score(
        question_text,
        answer_text,
        role_skills
    )

    communication = _communication_score(
        answer_text
    )

    confidence = _confidence_score(
        answer_text
    )

    clarity = _clarity_score(
        answer_text
    )

    completeness = _completeness_score(
        answer_text,
        category
    )

    if category in (
        "technical",
        "role-specific"
    ):
        technical_accuracy = round(
            relevance * 0.7
            + completeness * 0.3,
            1
        )
    else:
        technical_accuracy = round(
            relevance * 0.4
            + completeness * 0.6,
            1
        )

    if time_taken and seconds_allotted:
        time_ratio = (
            time_taken /
            seconds_allotted
        )

        if time_ratio > 1.15:
            communication = round(
                communication * 0.92,
                1
            )

    scores = {
        "technical_accuracy": technical_accuracy,
        "relevance": relevance,
        "communication": communication,
        "clarity": clarity,
        "confidence": confidence,
        "completeness": completeness,
    }

    weights = {
        "technical_accuracy": 0.30,
        "relevance": 0.20,
        "communication": 0.15,
        "clarity": 0.15,
        "confidence": 0.10,
        "completeness": 0.10,
    }

    question_score = round(
        sum(
            scores[k] * w
            for k, w in weights.items()
        ),
        1
    )

    star_feedback = None

    if category == "behavioral":
        star_feedback = _detect_star(
            answer_text
        )

    feedback = _build_feedback_sentence(
        category,
        technical_accuracy,
        communication,
        confidence,
        clarity,
        completeness,
        star_feedback
    )

    return {
        "technical_accuracy": technical_accuracy,
        "relevance": relevance,
        "communication": communication,
        "clarity": clarity,
        "confidence": confidence,
        "completeness": completeness,
        "question_score": question_score,
        "star_feedback": star_feedback,
        "feedback": feedback,
    }


def _build_feedback_sentence(
    category,
    technical,
    communication,
    confidence,
    clarity,
    completeness,
    star_feedback
):
    notes = []

    if technical >= 80:
        notes.append(
            "Strong, relevant content"
        )
    elif technical < 50:
        notes.append(
            "Try to include more specific, relevant details"
        )

    if communication < 55:
        notes.append(
            "watch filler words and aim for a well-structured 60-120 word answer"
        )

    if confidence < 55:
        notes.append(
            "use more assertive language instead of hedging"
        )

    if clarity < 60:
        notes.append(
            "simplify long sentences for clarity"
        )

    if completeness < 55:
        notes.append(
            "expand your answer with more depth"
        )

    if category == "behavioral" and star_feedback:
        missing = [
            k.title()
            for k, present in star_feedback.items()
            if not present
        ]

        if missing:
            notes.append(
                "use the STAR method more fully - "
                f"your answer was missing: {', '.join(missing)}"
            )
        else:
            notes.append(
                "great STAR structure (Situation, Task, Action, Result)"
            )

    if not notes:
        notes.append(
            "Solid, well-rounded answer"
        )

    return ". ".join(
        notes
    ).capitalize() + "."


# --------------------------------------------------------------------------
# Optional real-LLM scoring path
# --------------------------------------------------------------------------

def analyze_answer_llm(
    question_text,
    answer_text,
    category,
    role_skills,
    provider,
    api_key,
    time_taken=None,
    seconds_allotted=None
):
    prompt = f"""You are an expert interview coach. Evaluate this interview answer.

Question ({category}): {question_text}
Candidate's answer: {answer_text}
Relevant skills for this role: {', '.join(role_skills)}

Score the answer from 0-100 on each of:
technical_accuracy, relevance, communication,
clarity, confidence, completeness.

Also give one concise (<=2 sentence)
piece of feedback.

{"If this is a behavioral question, also assess whether Situation, Task, Action, and Result were each present (true/false) in a star_feedback object." if category == "behavioral" else ""}

Respond ONLY with valid JSON in this exact shape, nothing else:
{{"technical_accuracy": 0, "relevance": 0, "communication": 0, "clarity": 0, "confidence": 0, "completeness": 0, "feedback": "...", "star_feedback": null}}
"""

    try:
        if provider == "openai":
            import requests

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
            )

            resp.raise_for_status()

            content = resp.json()[
                "choices"
            ][0]["message"]["content"]

        elif provider == "anthropic":
            import requests

            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                },
                timeout=30,
            )

            resp.raise_for_status()

            content = resp.json()[
                "content"
            ][0]["text"]

        else:
            raise ValueError(
                "Unknown provider"
            )

        content = content.strip().strip("`")

        if content.startswith("json"):
            content = content[4:]

        data = json.loads(content)

        weights = {
            "technical_accuracy": 0.30,
            "relevance": 0.20,
            "communication": 0.15,
            "clarity": 0.15,
            "confidence": 0.10,
            "completeness": 0.10,
        }

        data["question_score"] = round(
            sum(
                data.get(k, 0) * w
                for k, w in weights.items()
            ),
            1
        )

        return data

    except Exception:
        return analyze_answer_heuristic(
            question_text,
            answer_text,
            category,
            role_skills,
            time_taken,
            seconds_allotted
        )


def analyze_answer(
    question_text,
    answer_text,
    category,
    role_skills,
    ai_provider=None,
    api_key=None,
    time_taken=None,
    seconds_allotted=None
):
    if (
        ai_provider in ("openai", "anthropic")
        and api_key
    ):
        return analyze_answer_llm(
            question_text,
            answer_text,
            category,
            role_skills,
            ai_provider,
            api_key,
            time_taken,
            seconds_allotted
        )

    return analyze_answer_heuristic(
        question_text,
        answer_text,
        category,
        role_skills,
        time_taken,
        seconds_allotted
    )


# --------------------------------------------------------------------------
# Final interview report generation
# --------------------------------------------------------------------------

def generate_final_report(
    role,
    questions_data,
    resume_skills=None
):
    """
    Generate the final interview report.
    """

    resume_skills = resume_skills or []
    role_data = get_role_data(role)

    answered = [
        q
        for q in questions_data
        if q.get("question_score") is not None
    ]

    if not answered:
        return _empty_report(role)

    def avg(key):
        vals = [
            q[key]
            for q in answered
            if q.get(key) is not None
        ]

        return (
            round(
                sum(vals) / len(vals),
                1
            )
            if vals
            else 0.0
        )

    overall = avg("question_score")
    technical = avg("technical_accuracy")
    communication = avg("communication")
    confidence = avg("confidence")
    clarity = avg("clarity")
    completeness = avg("completeness")
    relevance = avg("relevance")

    dims = {
        "Technical Accuracy": technical,
        "Relevance": relevance,
        "Communication": communication,
        "Clarity": clarity,
        "Confidence": confidence,
        "Completeness": completeness,
    }

    sorted_dims = sorted(
        dims.items(),
        key=lambda x: x[1],
        reverse=True
    )

    strengths = [
        f"{name} ({score}/100)"
        for name, score in sorted_dims
        if score >= 70
    ][:4]

    weaknesses = [
        f"{name} ({score}/100)"
        for name, score in sorted_dims
        if score < 60
    ][:4]

    if not strengths:
        strengths = [
            f"{sorted_dims[0][0]} was your best-performing area "
            f"({sorted_dims[0][1]}/100)"
        ]

    if not weaknesses:
        weaknesses = [
            "No major weak areas detected - keep practicing to maintain consistency"
        ]

    role_skills = set(
        s.lower()
        for s in role_data.get("skills", [])
    )

    demonstrated = set()

    for q in answered:
        text = (
            q.get("answer_text") or ""
        ).lower()

        for s in role_skills:
            if s in text:
                demonstrated.add(s)

    resume_skill_set = set(
        s.lower()
        for s in resume_skills
    )

    missing_skills = sorted(
        role_skills
        - demonstrated
        - resume_skill_set
    )[:6]

    if not missing_skills:
        missing_skills = sorted(
            role_skills - demonstrated
        )[:6]

    improvement_plan = _build_improvement_plan(
        dims,
        missing_skills
    )

    recommended_topics = _recommend_topics(
        role,
        missing_skills
    )

    practice_questions = _pick_practice_questions(
        role,
        weaknesses
    )

    return {
        "overall_score": overall,
        "technical_score": technical,
        "communication_score": communication,
        "confidence_score": confidence,
        "clarity_score": clarity,
        "completeness_score": completeness,
        "relevance_score": relevance,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_skills": missing_skills,
        "improvement_plan": improvement_plan,
        "recommended_topics": recommended_topics,
        "practice_questions": practice_questions,
    }


def _empty_report(role):
    return {
        "overall_score": 0,
        "technical_score": 0,
        "communication_score": 0,
        "confidence_score": 0,
        "clarity_score": 0,
        "completeness_score": 0,
        "relevance_score": 0,
        "strengths": [],
        "weaknesses": [
            "No answers were recorded for this interview."
        ],
        "missing_skills": [],
        "improvement_plan": [
            "Complete a full interview session to get personalized feedback."
        ],
        "recommended_topics": [],
        "practice_questions": [],
    }


def _build_improvement_plan(
    dims,
    missing_skills
):
    plan = []

    for name, score in dims.items():
        if score < 60:

            tips = {
                "Technical Accuracy":
                    "Revise core concepts for this role and practice explaining them out loud, with concrete examples.",

                "Relevance":
                    "Re-read each question carefully and directly address what's being asked before adding extra context.",

                "Communication":
                    "Practice the STAR framework and aim for concise 60-120 word answers with fewer filler words.",

                "Clarity":
                    "Break long sentences into shorter ones and structure answers as: point -> example -> outcome.",

                "Confidence":
                    "Practice answers out loud beforehand and use assertive phrasing ('I led', 'I decided') instead of hedging.",

                "Completeness":
                    "Add more depth: context, your specific action, and the measurable result.",
            }

            plan.append(
                tips.get(
                    name,
                    f"Work on improving {name.lower()}."
                )
            )

    if missing_skills:
        plan.append(
            "Study and prepare examples demonstrating: "
            f"{', '.join(missing_skills[:4])}."
        )

    if not plan:
        plan.append(
            "Great performance overall - keep practicing timed mock interviews to build consistency under pressure."
        )

    return plan


def _recommend_topics(
    role,
    missing_skills
):
    topics = list(
        missing_skills[:5]
    )

    role_data = get_role_data(role)

    for s in role_data.get("skills", []):
        if (
            s not in topics
            and len(topics) < 6
        ):
            topics.append(s)

    return topics


def _pick_practice_questions(
    role,
    weaknesses
):
    role_data = get_role_data(role)
    pool = []

    for diff in ("medium", "hard"):
        pool += role_data[
            "technical"
        ].get(diff, [])

        pool += role_data[
            "role_specific"
        ].get(diff, [])

    pool += QUESTION_BANK[
        "behavioral"
    ].get("medium", [])

    random.shuffle(pool)

    return pool[:5]