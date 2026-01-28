from rest_framework import viewsets, status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.decorators import action

from .serializers import TaskSerializer, CommentSerializer, TaskHistorySerailizer
from tasks.models import TaskModel, CommentModel, TaskHistoryModel
from core.services.roles import ROLE_PERMISSIONS
from core.services.permissions import TaskPermissions
from core.services.task_service import TaskService, CommentService

class CommentViewSet(viewsets.ModelViewSet):
   pass

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [TaskPermissions]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self): # type: ignore
        user = self.request.user

        return(
            TaskModel.objects.filter(
                Q(created_by = user) |
                Q(assigned_to = user)
            )
            .distinct()
            .prefetch_related('project')
            .select_related('created_by')
        )

    # def create(self, request, *args, **kwargs):
    #     """Create a new task using the task service"""
    #     serializer = self.get_serializer(data = request.data)
    #     serializer.is_valid(raise_exception=True)

    #     # Extract project id from the request data
    #     project_id = request.data.get('project')

    #     if not project_id:
    #         return Response(
    #             {"error": f"{project_id} field is required"},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # create task model using the service
    #     task = TaskService.create_task(
    #         user = request.user,
    #         project_id= project_id,
    #         data = serializer.validated_data
    #     )

    #     # Return serializer response
    #     output_serializer = self.get_serializer(task)
    #     return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    # TODO: Implement PUT /api/v1/project/{project_id}/tasks/{task_id} — update a task (e.g., change description, due date)
    # TODO: GET /api/v1/projects/{project_id}/tasks?status=OPEN&assigned_to=12 - filtering 
    #! TODO: Get rid of the patches
    

    @action(detail=True, methods=['patch'])
    def assign(self, request, pk=None):
        """Assign a task to a user"""
        task = self.get_object()
        assigned_to_id = request.data.get('assigned_to')

        update_task = TaskService.assign_task(
            task_id=task.id,
            altered_by = request.user,
            assigned_to_id=assigned_to_id,
        )

        serializer = self.get_serializer(update_task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        new_status = request.data.get('status')

        update_task = TaskService.update_task_status(
            task_id=task.id,
            user = request.user,
            status = new_status
        )

        serializer = self.get_serializer(update_task)
        return Response(serializer.data)    
    
    @action(detail=True, methods=['patch'], url_path='priority')
    def update_priority(self, request, pk=None):
        """Update task priority"""
        task = self.get_object()
        new_priority = request.data.get('priority')

        update_task = TaskService.update_task_priority(
            task_id=task.id,
            user = request.user,
            priority = new_priority
        )

        serializer = self.get_serializer(update_task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'get'], url_path='comments')
    def comments(self, request, pk=None):
        """Handle comments for a task"""

        # get task id from the url parameter
        task = self.get_object()

        if request.method == 'POST':
            # Create a new comment
            serializer = CommentSerializer(data = request.data)
            serializer.is_valid(raise_exception=True)

            comment = CommentService.create_comment(
                user = request.user,
                task= task,
                data = serializer.validated_data
            )

            # Return serializer response
            output_serializer = CommentSerializer(comment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        else: # GET request
            # List all comments for this task
            comments = CommentModel.objects.filter(
                        task=task
                    ).select_related('author')
            
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='logs') 
    def task_logs(self, request, pk=None):
        """Manage task logs"""
        task = self.get_object()

        task_history = TaskHistoryModel.objects.all()
        serializer = TaskHistorySerailizer(task_history, many=True)

        return Response(serializer.data)


        
    

