from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from processing.serializers import LaunchProcessingSerializer, ProcessingResultSerializer


class LaunchProcessingApi(generics.CreateAPIView):
    permission_classes = [AllowAny, ]

    request_serializer_class = LaunchProcessingSerializer
    response_serializer_class = ProcessingResultSerializer

    def get_serializer_class(self, for_request=True):
        assert self.response_serializer_class is not None, (
                "'%s' should either include a `serializer_class` attribute, "
                "or override the `get_serializer_class()` method."
                % self.__class__.__name__
        )

        if for_request:
            return self.request_serializer_class
        else:
            return self.response_serializer_class

    def post(self, request, *args, **kwargs):

        print(request.data['user_id'], request.data['processing_time'])
        user_id = request.data.get('user_id')
        processing_time = request.data.get('processing_time')

        # TODO start processing for 'processing_time' seconds (time.sleep(processing_time))

        # TODO store result to the DB

        # TODO send notifications via websockets

        serializer = self.get_serializer_class(for_request=False)({'user_id': user_id,
                         'result': 'GOOD',
                         'processing_time': processing_time
                         })

        return Response(serializer.data, status=status.HTTP_201_CREATED)
