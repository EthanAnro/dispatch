from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true


from .models import Project, ProjectCreate, ProjectRead, ProjectUpdate


def get(*, db_session: Session, project_id: int) -> Project | None:
    """Returns a project based on the given project id."""
    return db_session.query(Project).filter(Project.id == project_id).first()


def get_default(*, db_session: Session) -> Project | None:
    """Returns the default project."""
    return db_session.query(Project).filter(Project.default == true()).one_or_none()


def get_default_or_raise(*, db_session: Session) -> Project:
    """Returns the default project or raise a ValidationError if one doesn't exist."""
    project = get_default(db_session=db_session)

    if not project:
        raise ValidationError(
            [
                {
                    "loc": ("project",),
                    "msg": "No default project defined.",
                    "type": "value_error",
                }
            ]
        )
    return project


def get_by_name(*, db_session: Session, name: str) -> Project | None:
    """Returns a project based on the given project name."""
    return db_session.query(Project).filter(Project.name == name).one_or_none()


def get_by_name_or_raise(*, db_session: Session, project_in: ProjectRead) -> Project:
    """Returns the project specified or raises ValidationError."""
    project = get_by_name(db_session=db_session, name=project_in.name)

    if not project:
        raise ValidationError(
            [
                {
                    "msg": "Project not found.",
                    "name": project_in.name,
                    "loc": "name",
                }
            ]
        )

    return project


def get_by_name_or_default(*, db_session, project_in: ProjectRead) -> Project:
    """Returns a project based on a name or the default if not specified."""
    if project_in and project_in.name:
        project = get_by_name(db_session=db_session, name=project_in.name)
        if project:
            return project
    return get_default_or_raise(db_session=db_session)


def get_all(*, db_session) -> list[Project | None]:
    """Returns all projects."""
    return db_session.query(Project)


def create(*, db_session, project_in: ProjectCreate) -> Project:
    """Creates a project."""
    from dispatch.organization import service as organization_service

    organization = organization_service.get_by_slug(
        db_session=db_session, slug=project_in.organization.slug
    )
    project = Project(
        **project_in.dict(exclude={"organization"}),
        organization_id=organization.id,
    )

    db_session.add(project)
    db_session.commit()
    return project


def get_or_create(*, db_session, project_in: ProjectCreate) -> Project:
    if project_in.id:
        q = db_session.query(Project).filter(Project.id == project_in.id)
    else:
        q = db_session.query(Project).filter_by(**project_in.dict(exclude={"id", "organization"}))

    instance = q.first()
    if instance:
        return instance

    return create(db_session=db_session, project_in=project_in)


def update(*, db_session, project: Project, project_in: ProjectUpdate) -> Project:
    """Updates a project."""
    project_data = project.dict()

    update_data = project_in.dict(exclude_unset=True, exclude={})

    for field in project_data:
        if field in update_data:
            setattr(project, field, update_data[field])

    db_session.commit()
    return project


def delete(*, db_session, project_id: int):
    """Deletes a project."""
    project = db_session.query(Project).filter(Project.id == project_id).first()
    db_session.delete(project)
    db_session.commit()
