from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from models import Interview

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def home():
    interviews = Interview.query.filter_by(user_id=current_user.id, status="completed") \
        .order_by(Interview.completed_at.desc()).all()

    total = len(interviews)
    avg_score = round(sum(i.overall_score for i in interviews) / total, 1) if total else 0
    best_score = round(max((i.overall_score for i in interviews), default=0), 1)
    last_score = interviews[0].overall_score if interviews else 0

    in_progress = Interview.query.filter_by(user_id=current_user.id, status="in_progress").count()

    return render_template(
        "dashboard.html", interviews=interviews, total=total, avg_score=avg_score,
        best_score=best_score, last_score=last_score, in_progress=in_progress,
    )


@dashboard_bp.route("/api/analytics")
@login_required
def analytics_data():
    interviews = Interview.query.filter_by(user_id=current_user.id, status="completed") \
        .order_by(Interview.completed_at.asc()).all()

    trend = {
        "labels": [i.completed_at.strftime("%b %d") for i in interviews],
        "overall": [i.overall_score for i in interviews],
    }

    skill_totals = {"Technical": 0, "Communication": 0, "Confidence": 0, "Clarity": 0, "Completeness": 0, "Relevance": 0}
    if interviews:
        n = len(interviews)
        skill_totals["Technical"] = round(sum(i.technical_score for i in interviews) / n, 1)
        skill_totals["Communication"] = round(sum(i.communication_score for i in interviews) / n, 1)
        skill_totals["Confidence"] = round(sum(i.confidence_score for i in interviews) / n, 1)
        skill_totals["Clarity"] = round(sum(i.clarity_score for i in interviews) / n, 1)
        skill_totals["Completeness"] = round(sum(i.completeness_score for i in interviews) / n, 1)
        skill_totals["Relevance"] = round(sum(i.relevance_score for i in interviews) / n, 1)

    role_counts = {}
    for i in interviews:
        role_counts[i.job_role] = role_counts.get(i.job_role, 0) + 1

    type_counts = {}
    for i in interviews:
        type_counts[i.interview_type] = type_counts.get(i.interview_type, 0) + 1

    return jsonify({
        "trend": trend, "skill_radar": skill_totals,
        "role_distribution": role_counts, "type_distribution": type_counts,
    })
