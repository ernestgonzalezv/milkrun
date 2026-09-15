from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView as BaseTokenRefreshView,
)
from rest_framework_simplejwt.views import (
    TokenVerifyView as BaseTokenVerifyView,
)

from .serializers import UserSerializer


@extend_schema(tags=["Authentication"], summary="The signed-in user")
class MeView(RetrieveAPIView):
    """La app movil y el dashboard la llaman al arrancar para saber el rol."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


# Las vistas de simplejwt se envuelven solo para etiquetarlas. Sin esto caen en
# un grupo "api" generico al final del Swagger, que es justo donde nadie busca
# lo primero que necesita para probar la API.


@extend_schema(
    tags=["Authentication"],
    summary="Obtain the token pair",
    description="Returns `access` (8 h, one shift) and `refresh` (30 days).",
)
class TokenObtainPairView(BaseTokenObtainPairView):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Refresh the access token",
    description="The refresh token rotates on every use: the previous one stops working.",
)
class TokenRefreshView(BaseTokenRefreshView):
    pass


@extend_schema(tags=["Authentication"], summary="Check whether a token is still valid")
class TokenVerifyView(BaseTokenVerifyView):
    pass
