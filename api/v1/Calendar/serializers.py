from rest_framework import serializers

from Calendar.models import CalendarEvent

class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'description', 'event_type', 'priority',
            'event_date', 'start_time', 'end_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        if attrs['end_time'] < attrs['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        return attrs