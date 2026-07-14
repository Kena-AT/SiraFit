from app.services.batch_operations import (
    batch_score_item, batch_tag_item, batch_archive_item
)
from app.models.job import Job
from app.models.profile import Profile
from app.models.profile import Skill

def test_batch_score_item(test_user, db):
    job = Job(external_id="score-job", title="Engineer", company="Co", tags=["python", "react"])
    db.add(job)
    db.commit()
    profile = Profile(user_id=test_user.id, skills=[Skill(name="python")], experiences=[], educations=[])
    db.add(profile)
    db.commit()
    result = batch_score_item(job.id, test_user.id, {}, db)
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert "breakdown" in result

def test_batch_tag_item_add(test_user, db):
    job = Job(external_id="tag-job", title="Engineer", company="Co", tags=["python"])
    db.add(job)
    db.commit()
    result = batch_tag_item(job.id, test_user.id, {"tags": ["remote", "senior"], "action": "add"}, db)
    assert "remote" in result["tags"]
    assert "senior" in result["tags"]
    assert "python" in result["tags"]

def test_batch_tag_item_remove(test_user, db):
    job = Job(external_id="tag-job2", title="Engineer", company="Co", tags=["python", "remote", "senior"])
    db.add(job)
    db.commit()
    result = batch_tag_item(job.id, test_user.id, {"tags": ["remote"], "action": "remove"}, db)
    assert "remote" not in result["tags"]
    assert "senior" in result["tags"]
    assert "python" in result["tags"]

def test_batch_archive_job(test_user, db):
    job = Job(external_id="arch-job", title="Engineer", company="Co")
    db.add(job)
    db.commit()
    result = batch_archive_item(job.id, test_user.id, {"target": "jobs"}, db)
    assert result["archived"] is True
    db.refresh(job)
    assert job.source == "archived"

def test_batch_archive_application(test_user, db):
    job = Job(external_id="arch-app-job", title="Engineer", company="Co")
    db.add(job)
    db.commit()
    from app.models.job import JobApplication
    app = JobApplication(user_id=test_user.id, job_id=job.id, status="applied")
    db.add(app)
    db.commit()
    db.refresh(app)
    result = batch_archive_item(app.id, test_user.id, {"target": "applications"}, db)
    assert result["archived"] is True
    assert result["target"] == "applications"
    db.refresh(app)
    assert app.status == "archived"