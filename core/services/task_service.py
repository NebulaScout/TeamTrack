from tasks.models import TaskModel
from projects.models import ProjectsModel
from django.contrib.auth.models import User

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
    def update_task(*, task_id, data):
        """Update an existing task"""
        task = TaskModel.objects.get(id = task_id)

        for key, value in data.items():
            setattr(task, key, value)

            task.save()
            return task
    
    @staticmethod
    def assign_task(*, task_id, assigned_to_id):
        """Assign a task to a user"""
        task = TaskModel.objects.get(id = task_id)
        user = User.objects.get(id = assigned_to_id) # get the user
        task.assigned_to = user
        task.save()

        return task
    
    @staticmethod
    def update_task_status(*, task_id, status):
        """Update the status of a task"""
        task = TaskModel.objects.get(id = task_id)
        task.status = status
        task.save()

        return task
    
    @staticmethod
    def update_task_priority(*, task_id, priority):
        """Update the priority of a task"""
        task = TaskModel.objects.get(id = task_id)
        task.priority = priority
        task.save()

        return task