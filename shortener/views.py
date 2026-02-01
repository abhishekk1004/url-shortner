from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.utils.timezone import now

from .models import ShortURL
from .serializers import RegisterSerializer, ShortURLSerializer
from .utils import generate_short_key

#class for api
class RegisterAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered successfully"})



#short url
class CreateShortURLAPI(APIView):
    def post(self, request):
        original_url = request.data.get("original_url")
        custom_key = request.data.get("custom_key")

        short_key = custom_key or generate_short_key()

        if ShortURL.objects.filter(short_key=short_key).exists():
            return Response({"error": "Short key already exists"}, status=400)

        url = ShortURL.objects.create(
            user=request.user,
            original_url=original_url,
            short_key=short_key
        )

        return Response(ShortURLSerializer(url).data)

#user lists
class ListURLsAPI(APIView):
    def get(self, request):
        urls = ShortURL.objects.filter(user=request.user)
        return Response(ShortURLSerializer(urls, many=True).data)


#redirectt
class RedirectAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, key):
        url = get_object_or_404(ShortURL, short_key=key)

        if url.expires_at and url.expires_at < now():
            return Response({"error": "Link expired"}, status=410)

        url.clicks += 1
        url.save()

        return HttpResponseRedirect(url.original_url)



#deletion
class DeleteURLAPI(APIView):
    def delete(self, request, key):
        ShortURL.objects.filter(user=request.user, short_key=key).delete()
        return Response({"message": "Deleted"})

