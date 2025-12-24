from django.contrib.auth.models import User

from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from projects.models import ProjectsModel
from .enums import TaskFieldEnum

class TaskService():
    # TODO: On task creation, set default status and priority
    @staticmethod
    def create_task(*, user, project_id, data):
        """Logic for task creation"""

        # Get project instance
        project = ProjectsModel.objects.get(id = project_id)

        return TaskModel.objects.create(
            project = project,
            created_by = user,
            **data,
        )
    
    @staticmethod
    def update_task(*, user, task_id, data):
        """Update an existing task"""
        task = TaskModel.objects.get(id = task_id)        

        for field, value in data.items():
            old_value = getattr(task, field)

            # Restrict the fields that contain unnecessary data
            if field in TaskFieldEnum: 
                TaskHistoryModel.objects.create(
                    task = task,
                    changed_by = user,
                    field = TaskFieldEnum.value,
                    old_value = old_value,
                    new_value = value
                )

            setattr(task, field, value)

        task.save()
        return task
    
    @staticmethod
    def assign_task(*, altered_by, task_id, assigned_to_id):
        """Assign a task to a user"""
        task = TaskModel.objects.get(id = task_id)
        user = User.objects.get(id = assigned_to_id) # get the user
        old_assignee = task.assigned_to

        if old_assignee != user:
            TaskHistoryModel.objects.create(
                task = task,
                changed_by = altered_by,
                field_changed = TaskFieldEnum.ASSIGNED_TO,
                old_value = old_assignee,
                new_value = user
            )

        task.assigned_to = user
        task.save()

        return task
    
    @staticmethod
    def update_task_status(*, user, task_id, status):
        """Update the status of a task"""
        task = TaskModel.objects.get(id = task_id)
        old_status = task.status

        if old_status != status:
            TaskHistoryModel.objects.create(
                task = task,
                changed_by = user,
                field_changed = TaskFieldEnum.STATUS,
                old_value = old_status,
                new_value = status
            )

        task.status = status
        task.save()

        return task
    
    @staticmethod
    def update_task_priority(*, user, task_id, priority):
        """Update the priority of a task"""
        task = TaskModel.objects.get(id = task_id)
        old_priority = task.priority

        if old_priority != priority:
            TaskHistoryModel.objects.create(
                task = task,
                changed_by = user,
                field_changed = TaskFieldEnum.PRIORITY,
                old_value = old_priority,
                new_value = priority
            )

        task.priority = priority
        task.save()

        return task
    
class CommentService:
    @staticmethod
    def create_comment(*, user, task, data):
        """Logic for comment creation"""

        # Get project instance
        task = TaskModel.objects.get(id = task.id)

        return CommentModel.objects.create(
            task = task,
            author = user,
            **data,
        )