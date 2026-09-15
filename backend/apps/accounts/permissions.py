"""Permisos por rol.

Se declaran como clases con `message` propio para que un 403 diga por que
fue rechazado; un 403 vacio es de las cosas que mas tiempo hacen perder al
que consume la API.
"""

from rest_framework.permissions import BasePermission


class IsDispatcher(BasePermission):
    message = "Solo un despachador puede hacer esta operacion."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_dispatcher)


class IsDriver(BasePermission):
    message = "Solo un chofer puede hacer esta operacion."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_driver)
