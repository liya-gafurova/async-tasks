from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny


from notifications.sync.sync_api.processing.serializers import LaunchProcessingSerializer


class LaunchProcessingApi(generics.CreateAPIView):
    serializer_class = LaunchProcessingSerializer
    permission_classes = [AllowAny,]

    def post(self, request, *args, **kwargs):

        print(request.data['user_id'], request.data['processing_time'])

        # TODO start processing for 'processing_time' seconds (time.sleep(processing_time))

        # TODO store result to the DB

        # TODO send notifications via websockets



        return HttpResponse({'result': "good"})