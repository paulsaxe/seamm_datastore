"""
Automatic import of projects and jobs from directories.
"""

import json
import os
from pathlib import Path

from seamm_datastore import api

from seamm_datastore.util import parse_job_data


def _build_initial(session, default_project):
    """Build the initial database"""

    from seamm_datastore.database.models import Role, Group, User, Project

    # Create roles
    role_names = ["user", "group manager", "admin"]
    for role_name in role_names:
        role = Role(name=role_name)
        session.add(role)
        session.commit()

    # Create default admin group
    admin_group = Group(name="admin")
    session.add(admin_group)
    session.commit()

    # Create default admin user.s
    admin_role = session.query(Role).filter_by(name="admin").one()
    admin_user = User(username="admin", password="admin", roles=[admin_role])
    admin_user.groups.append(admin_group)

    # Create a user and group with the same information as user running
    try:
        item = Path.home()
        username = item.owner()
        group_name = item.group()
    except NotImplementedError:
        # This will occur on Windows
        import os

        username = os.environ["USERNAME"]
        # Just a default group name.
        group_name = "staff"

    group = Group(name=group_name)

    password = "default"
    user = User(username=username, password=password, roles=[admin_role])
    user.groups.append(group)

    # Admin user needs to be part of all groups.
    admin_user.groups.append(group)

    session.add(admin_user)
    session.add(admin_role)
    session.add(admin_group)

    session.add(user)

    # Create a default project
    project = Project(name=default_project, owner=user, group=group)
    session.add(project)
    session.commit()


def import_datastore(session, location, as_json=True):
    """Import all the projects and jobs at <location>.

    Parameters
    ----------
    session : SQLAlchemy or flask session
    location : str or path
        The location to check for jobs or projects. Usually the projects directory in a datastore.

    Returns
    -------
    (n_projects, n_jobs) : int, integer
        The number of projects and jobs added to the database.
    """

    from seamm_datastore.database.models import Project

    jobs = []
    project_names = []

    # Get directory contents of file path
    for folder in os.listdir(location):
        potential_project = os.path.join(location, folder)

        # If item is a directory, it may contain jobs.
        # We are going to be taking the project names
        # from the job_data.json
        if os.path.isdir(potential_project):
            project_name = os.path.basename(potential_project)
            item = Path(potential_project)
            group = item.group()
            username = item.owner()
            project_data = {
                "owner": username,
                "group": group,
                "name": project_name,
                "path": potential_project,
            }

            try:
                api.add_project(session, project_data, as_json=as_json)
                project_names.append(project_data["name"])
            except ValueError:
                # Project exists, we don't need to add it.
                # Pass here because we should still try importing jobs.
                pass

            for potential_job in os.listdir(potential_project):
                potential_job = os.path.join(potential_project, potential_job)

                if os.path.isdir(potential_job):

                    # Check for job_data.json - has to have this to be job
                    check_path = os.path.join(potential_job, "job_data.json")

                    if os.path.exists(check_path):
                        with open(check_path, 'r') as fd:
                            lines = fd.read().splitlines()
                        # Old files may not have a header line
                        if lines[0][0] == "{":
                            text = "\n".join(lines)
                        else:
                            text = "\n".join(lines[1:])                            
                        job_data_json = json.loads(text)
                        job_data = parse_job_data(job_data_json)

                        try:
                            job = api.add_job(
                                session, job_data=job_data, as_json=as_json)
                            jobs.append(job)
                        except ValueError:
                            # Job has already been added.
                            pass

    # retrieve projects now that all the jobs have been added.
    projects = Project.query.filter(Project.name.in_(project_names)).all()

    return jobs, projects
