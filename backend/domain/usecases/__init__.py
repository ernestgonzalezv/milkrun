"""Casos de uso: un archivo por operacion del negocio.

Cada uno recibe sus puertos en el constructor y expone un unico `__call__`.
Ninguno llama a otro: si dos comparten logica, esa logica baja al repositorio
o a `policies.py`.
"""
