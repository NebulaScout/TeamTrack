from rest_framework import serializers

from Calendar.models import CalendarEvent

class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'description', 'event_type', 'priority',
            'start_datetime', 'end_datetime', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        if attrs['start_datetime'] > attrs['end_datetime']:
            raise serializers.ValidationError("End time must be after start time")
        return attrs